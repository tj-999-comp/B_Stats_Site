#!/usr/bin/env python3
"""Validate work-record Markdown/HTML placement, filenames, and headings.

Rules:
- README.md and design.md are the only Markdown files directly under work-records/.
- Numbered records live under work-records/md/ as work_record_###.md.
- A numbered record starts with "# 作業記録 ###:" using the same number.
- Every Markdown file under work-records/md/ has a same-stem HTML file directly
  under work-records/.
"""

from __future__ import annotations

import re
from pathlib import Path

WORK_RECORDS_DIR = Path("work-records")
MARKDOWN_DIR = WORK_RECORDS_DIR / "md"
VALID_NAME_RE = re.compile(r"^work_record_(\d{3})\.md$")
VALID_HEADING_RE = re.compile(r"^# 作業記録 (\d{3}): .+$")
VALID_HTML_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*\.html$")
ALLOWED_ROOT_MARKDOWN = {"README.md", "design.md"}


def main() -> int:
    if not WORK_RECORDS_DIR.exists():
        print("work-records/ directory not found.")
        return 1

    violations: list[str] = []

    root_markdown = sorted(WORK_RECORDS_DIR.glob("*.md"))
    for path in root_markdown:
        if path.name not in ALLOWED_ROOT_MARKDOWN:
            violations.append(
                f"{path}: move Markdown files other than README.md and design.md "
                "to work-records/md/"
            )

    for required_name in sorted(ALLOWED_ROOT_MARKDOWN):
        if not (WORK_RECORDS_DIR / required_name).is_file():
            violations.append(f"work-records/{required_name}: required file not found")

    if not MARKDOWN_DIR.is_dir():
        violations.append("work-records/md/: directory not found")
    else:
        for path in sorted(MARKDOWN_DIR.glob("*.md")):
            name_match = VALID_NAME_RE.fullmatch(path.name)
            if name_match is not None:
                lines = path.read_text(encoding="utf-8").splitlines()
                if not lines:
                    violations.append(f"{path}: file is empty")
                    continue

                first_line = lines[0]
                heading_match = VALID_HEADING_RE.fullmatch(first_line)
                if heading_match is None:
                    violations.append(
                        f"{path}: expected first line '# 作業記録 ###: <内容>'"
                    )
                    continue

                if name_match.group(1) != heading_match.group(1):
                    violations.append(
                        f"{path}: filename number and heading number do not match"
                    )
            elif path.name.startswith("work_record"):
                violations.append(
                    f"{path}: expected filename pattern work_record_###.md"
                )

            expected_html = WORK_RECORDS_DIR / f"{path.stem}.html"
            if not expected_html.is_file():
                violations.append(f"{path}: corresponding HTML not found at {expected_html}")

    for path in sorted(WORK_RECORDS_DIR.rglob("*.html")):
        if path.parent != WORK_RECORDS_DIR:
            violations.append(
                f"{path}: move HTML files directly under work-records/"
            )
            continue

        html_name_match = VALID_HTML_NAME_RE.fullmatch(path.name)
        if html_name_match is None:
            violations.append(
                f"{path}: expected a same-stem HTML filename under work-records/"
            )
            continue

        markdown_path = MARKDOWN_DIR / f"{path.stem}.md"
        if not markdown_path.is_file():
            violations.append(
                f"{path}: corresponding Markdown record not found at {markdown_path}"
            )

    if violations:
        print("Work-record rule violations detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Work-record filename and placement validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
