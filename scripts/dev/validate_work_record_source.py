#!/usr/bin/env python3
"""Validate the source_html contract for numbered work records.

This validator intentionally uses only the Python standard library so the same
checks can run locally and in GitHub Actions without installing extra packages.
"""

from __future__ import annotations

import argparse
import html.parser
import re
import tempfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK_RECORDS_DIR = ROOT / "work-records"
MARKDOWN_DIR = WORK_RECORDS_DIR / "md"
METADATA_DIR = WORK_RECORDS_DIR / "metadata"
NUMBERED_RE = re.compile(r"^work_record_([0-9]{3})$")
DATE_RE = re.compile(r"^作成日:\s*(\d{4}-\d{2}-\d{2})\s*$")
HEADING_RE = re.compile(r"^# 作業記録 ([0-9]{3}): (.+)$")
ALLOWED_FIELDS = {"schema_version", "title", "date", "project_id", "tags", "publish"}
PROJECT_ID = "B_Stats_Site"
FORBIDDEN_TAGS = {"script", "iframe", "object", "embed", "form", "base"}
ALLOWED_TAGS = {
    "html", "head", "meta", "title", "link", "body", "div", "header", "footer",
    "main", "aside", "span", "p", "h1", "h2", "h3", "h4", "dl", "dt", "dd", "code",
    "section", "ul", "ol", "li", "a", "strong", "em", "pre", "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRS = {
    "lang", "charset", "name", "content", "color-scheme", "rel", "href", "class",
}
URL_ATTRS = {"href", "src", "action", "poster", "cite", "formaction"}
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
CSS_IMPORT_RE = re.compile(r"@import", re.IGNORECASE)
CSS_URL_RE = re.compile(r"url\s*\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    return value


def parse_metadata(path: Path) -> dict[str, object]:
    """Parse the deliberately small metadata YAML subset used by the contract."""

    result: dict[str, object] = {}
    current_list: list[str] | None = None
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.rstrip()
        if line.lstrip().startswith("#"):
            continue
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise ValueError(f"{path}:{line_number}: list item without a field")
            current_list.append(str(_parse_scalar(line[4:])))
            continue
        if line.startswith(" "):
            raise ValueError(f"{path}:{line_number}: unsupported indentation")
        if ":" not in line:
            raise ValueError(f"{path}:{line_number}: expected key: value")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key in result:
            raise ValueError(f"{path}:{line_number}: duplicate or empty key")
        value = value.strip()
        if value:
            result[key] = _parse_scalar(value)
            current_list = None
        else:
            result[key] = []
            current_list = result[key]  # type: ignore[assignment]
    return result


class _HTMLInspector(html.parser.HTMLParser):
    def __init__(self, path: Path, violations: list[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.violations = violations
        self.local_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            self.violations.append(f"{self.path}: HTML element is not in the allowlist: <{tag}>")
        if tag in FORBIDDEN_TAGS:
            self.violations.append(f"{self.path}: forbidden HTML element <{tag}>")
        attrs_map = {name.lower(): value for name, value in attrs}
        unknown_attrs = sorted(set(attrs_map) - ALLOWED_ATTRS - URL_ATTRS)
        if unknown_attrs:
            self.violations.append(
                f"{self.path}: HTML attributes are not in the allowlist: {', '.join(unknown_attrs)}"
            )
        if any(name.startswith("on") for name in attrs_map):
            self.violations.append(f"{self.path}: inline event handler is not allowed")
        if tag == "meta" and attrs_map.get("http-equiv", "").lower() == "refresh":
            self.violations.append(f"{self.path}: meta refresh is not allowed")
        for name in URL_ATTRS:
            value = attrs_map.get(name)
            if value is not None:
                self._check_url(value)

    def _check_url(self, value: str) -> None:
        value = value.strip()
        if value.startswith("//"):
            self.violations.append(f"{self.path}: protocol-relative URL is not allowed: {value}")
            return
        if SCHEME_RE.match(value) and not value.lower().startswith(("http:", "https:")):
            self.violations.append(f"{self.path}: unsafe URL scheme: {value}")
            return
        if value.startswith("/") and not value.startswith("//"):
            self.violations.append(f"{self.path}: absolute path is not allowed: {value}")
            return
        if value.startswith("#") or SCHEME_RE.match(value):
            return
        self.local_urls.append(value)
        parts = value.split("#", 1)[0].split("?")[0].split("/")
        depth = 0
        for part in parts:
            if part in ("", "."):
                continue
            if part == "..":
                depth -= 1
            else:
                depth += 1
            if depth < 0:
                self.violations.append(f"{self.path}: path traversal URL: {value}")
                return


def validate_css(path: Path, violations: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    if CSS_IMPORT_RE.search(text):
        violations.append(f"{path}: CSS @import is not allowed")
    if re.search(r"expression\s*\(|(?<![-\w])behavior\s*:\s*|-moz-binding\s*:", text, re.IGNORECASE):
        violations.append(f"{path}: executable CSS syntax is not allowed")
    for match in CSS_URL_RE.finditer(text):
        value = match.group(2).strip()
        if value.startswith("//") or value.lower().startswith(("data:", "javascript:", "http:", "https:")):
            violations.append(f"{path}: external or unsafe CSS URL: {value}")
        elif value.startswith("/") or ".." in Path(value).parts:
            violations.append(f"{path}: CSS path outside project: {value}")


def _record_title_and_date(path: Path) -> tuple[str, str]:
    title: str | None = None
    record_date: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(2)
        date_match = DATE_RE.match(line.strip())
        if date_match:
            record_date = date_match.group(1)
    if title is None or record_date is None:
        raise ValueError(f"{path}: title or 作成日 is missing")
    return title, record_date


def validate_tree(root: Path) -> list[str]:
    records_dir = root / "work-records"
    markdown_dir = records_dir / "md"
    metadata_dir = records_dir / "metadata"
    violations: list[str] = []
    markdown_paths = sorted(
        path for path in markdown_dir.glob("work_record_*.md") if NUMBERED_RE.fullmatch(path.stem)
    )
    metadata_paths = sorted(metadata_dir.glob("work_record_*.yml")) if metadata_dir.exists() else []
    record_stems = {path.stem for path in markdown_paths}
    metadata_stems = {path.stem for path in metadata_paths}

    if not markdown_paths:
        violations.append(f"{markdown_dir}: no numbered Markdown records found")
    if record_stems != metadata_stems:
        missing = sorted(record_stems - metadata_stems)
        extra = sorted(metadata_stems - record_stems)
        if missing:
            violations.append(f"metadata missing for: {', '.join(missing)}")
        if extra:
            violations.append(f"metadata has no Markdown record: {', '.join(extra)}")

    for markdown_path in markdown_paths:
        stem = markdown_path.stem
        number = int(stem.rsplit("_", 1)[1])
        if not 1 <= number <= 999:
            violations.append(f"{markdown_path}: record number must be 001..999")
        html_path = records_dir / f"{stem}.html"
        metadata_path = metadata_dir / f"{stem}.yml"
        if not html_path.is_file():
            violations.append(f"{markdown_path}: corresponding HTML missing: {html_path}")
        if not metadata_path.is_file():
            continue
        try:
            metadata = parse_metadata(metadata_path)
        except ValueError as error:
            violations.append(str(error))
            continue
        unknown = sorted(set(metadata) - ALLOWED_FIELDS)
        missing_fields = sorted(ALLOWED_FIELDS - set(metadata))
        if unknown:
            violations.append(f"{metadata_path}: unknown fields: {', '.join(unknown)}")
        if missing_fields:
            violations.append(f"{metadata_path}: missing fields: {', '.join(missing_fields)}")
        if metadata.get("schema_version") != 1:
            violations.append(f"{metadata_path}: schema_version must be 1")
        if not isinstance(metadata.get("title"), str) or not metadata.get("title"):
            violations.append(f"{metadata_path}: title must be a non-empty string")
        if metadata.get("project_id") != PROJECT_ID:
            violations.append(f"{metadata_path}: project_id must be {PROJECT_ID}")
        if not isinstance(metadata.get("tags"), list) or not all(isinstance(tag, str) and tag for tag in metadata.get("tags", [])):
            violations.append(f"{metadata_path}: tags must be a list of non-empty strings")
        if not isinstance(metadata.get("publish"), bool):
            violations.append(f"{metadata_path}: publish must be boolean")
        metadata_date = metadata.get("date")
        try:
            parsed_date = date.fromisoformat(str(metadata_date))
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(metadata_date)):
                raise ValueError
            if parsed_date.isoformat() != metadata_date:
                raise ValueError
        except ValueError:
            violations.append(f"{metadata_path}: date must be a real YYYY-MM-DD")
        try:
            title, record_date = _record_title_and_date(markdown_path)
            if metadata.get("title") != title:
                violations.append(f"{metadata_path}: title does not match Markdown heading")
            if metadata.get("date") != record_date:
                violations.append(f"{metadata_path}: date does not match Markdown 作成日")
        except ValueError as error:
            violations.append(str(error))

        if html_path.is_file():
            inspector = _HTMLInspector(html_path, violations)
            try:
                inspector.feed(html_path.read_text(encoding="utf-8"))
            except ValueError as error:
                violations.append(f"{html_path}: invalid HTML: {error}")
            for value in inspector.local_urls:
                target = (html_path.parent / value.split("#", 1)[0].split("?", 1)[0]).resolve()
                try:
                    target.relative_to(records_dir.resolve())
                except ValueError:
                    continue
                if not target.is_file():
                    violations.append(f"{html_path}: referenced local file is missing: {value}")

    for support_name in ("README.md", "design.md", "work_record.css"):
        support_path = records_dir / support_name
        if not support_path.is_file():
            violations.append(f"{support_path}: required support file missing")
        elif support_path.suffix == ".css":
            validate_css(support_path, violations)

    # Legacy auxiliary HTML is deliberately outside the numbered metadata set.
    for auxiliary_name in ("phase_1_tasks.html", "scraping_db_automation.html"):
        auxiliary_path = records_dir / auxiliary_name
        if auxiliary_path.exists() and auxiliary_path.stem in metadata_stems:
            violations.append(f"{auxiliary_path}: auxiliary HTML must not be publish metadata")
    return violations


def run_fixtures() -> int:
    """Exercise the security checks and legacy auxiliary exclusion in a temp tree."""

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        records = root / "work-records"
        (records / "md").mkdir(parents=True)
        (records / "metadata").mkdir()
        (records / "md/work_record_001.md").write_text(
            "# 作業記録 001: Fixture\n作成日: 2026-08-20\n", encoding="utf-8"
        )
        (records / "metadata/work_record_001.yml").write_text(
            "schema_version: 1\ntitle: Fixture\ndate: \"2026-08-20\"\n"
            "project_id: B_Stats_Site\ntags:\n  - test\npublish: true\n",
            encoding="utf-8",
        )
        (records / "work_record.css").write_text("body { color: black; }\n", encoding="utf-8")
        (records / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (records / "design.md").write_text("# Fixture design\n", encoding="utf-8")
        (records / "work_record_001.html").write_text(
            '<!doctype html><html><body><a href="md/work_record_001.md">x</a></body></html>\n',
            encoding="utf-8",
        )
        (records / "phase_1_tasks.html").write_text("<p>legacy</p>\n", encoding="utf-8")
        (records / "scraping_db_automation.html").write_text("<p>legacy</p>\n", encoding="utf-8")
        if validate_tree(root):
            print("fixture baseline failed")
            return 1
        (records / "work_record_001.html").write_text("<script>alert(1)</script>\n", encoding="utf-8")
        violations = validate_tree(root)
        if not any("forbidden HTML element" in violation for violation in violations):
            print("fixture unsafe HTML was not rejected")
            return 1
        (records / "work_record_001.html").write_text('<a href="../README.md">x</a>\n', encoding="utf-8")
        violations = validate_tree(root)
        if not any("path traversal URL" in violation for violation in violations):
            print("fixture path traversal was not rejected")
            return 1
    print("source validator fixtures passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate work-record metadata and source HTML safety.")
    parser.add_argument("--check-fixtures", action="store_true", help="run negative and auxiliary-file fixtures")
    args = parser.parse_args()
    if args.check_fixtures:
        return run_fixtures()
    violations = validate_tree(ROOT)
    if violations:
        print("Work-record source contract violations detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print("Work-record source contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
