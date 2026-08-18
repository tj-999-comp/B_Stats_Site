#!/usr/bin/env python3
"""Synchronize a work record's GitHub Issue status section.

The Markdown work record remains the source of truth for the rendered HTML, but
the current Issue section is generated from GitHub's open issues API. Pull
Requests are excluded because GitHub exposes them through the issues endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_DIR = ROOT / "work-records" / "md"
ISSUE_HEADING_RE = re.compile(
    r"^## GitHub Issue状況（\d{4}-\d{2}-\d{2}時点の現在値）\s*$",
    re.MULTILINE,
)
ISSUE_TABLE_HEADER = "| GitHub Issue | 状態 | 最終更新 | コメント | 関係・残件 |"
ISSUE_ROW_RE = re.compile(r"^\|\s*\[#(\d+)\]\([^)]*\)")
JST = ZoneInfo("Asia/Tokyo")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GitHubの全オープンIssueを作業記録へ同期・検証する"
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", "tj-999-comp/B_Stats_Site"),
        help="GitHubリポジトリ（owner/name）",
    )
    parser.add_argument(
        "--record",
        type=Path,
        help="対象Markdown。省略時はwork_record_###の最大番号を使う",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="Issue状況を更新する")
    action.add_argument("--check", action="store_true", help="Issue状況を照合する")
    parser.add_argument(
        "--skip-html",
        action="store_true",
        help="--write時にMarkdownからHTMLを再生成しない",
    )
    return parser.parse_args()


def _record_path(argument: Path | None) -> Path:
    if argument is not None:
        path = argument if argument.is_absolute() else ROOT / argument
        if not path.is_file():
            raise ValueError(f"対象Markdownが見つかりません: {path}")
        return path

    candidates = []
    for path in MARKDOWN_DIR.glob("work_record_*.md"):
        match = re.fullmatch(r"work_record_(\d{3})\.md", path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    if not candidates:
        raise ValueError("work-records/md/work_record_###.md が見つかりません")
    return max(candidates, key=lambda item: item[0])[1]


def _fetch_with_token(repo: str, token: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repo}/issues"
            f"?state=open&per_page=100&page={page}"
        )
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "B-Stats-Site-work-record-sync",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                page_items = json.load(response)
        except (HTTPError, URLError) as error:
            raise RuntimeError(f"GitHub API取得に失敗しました: {error}") from error
        if not isinstance(page_items, list):
            raise RuntimeError("GitHub APIのレスポンス形式が不正です")
        issues.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
    return issues


def _fetch_with_gh(repo: str) -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            [
                "gh",
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repo}/issues?state=open&per_page=100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("GitHub tokenまたはghコマンドが必要です") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise RuntimeError(f"ghでGitHub API取得に失敗しました: {detail}") from error

    try:
        pages = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("ghのレスポンスをJSONとして解釈できません") from error
    if not isinstance(pages, list):
        raise RuntimeError("ghのレスポンス形式が不正です")
    if pages and isinstance(pages[0], list):
        return [item for page in pages for item in page]
    return pages


def fetch_open_issues(repo: str) -> list[dict[str, Any]]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    raw_issues = _fetch_with_token(repo, token) if token else _fetch_with_gh(repo)
    issues = [item for item in raw_issues if "pull_request" not in item]
    return sorted(issues, key=lambda item: int(item["number"]))


def _jst_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S JST")


def _markdown_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value).replace("|", "\\|").strip()


def build_issue_section(repo: str, issues: list[dict[str, Any]]) -> str:
    checked_at = datetime.now(JST)
    checked_date = checked_at.strftime("%Y-%m-%d")
    lines = [
        f"## GitHub Issue状況（{checked_date}時点の現在値）",
        "",
        f"確認日: {checked_date}（JST）",
        "",
        (
            f"GitHub APIで `{repo}` のオープンIssueを確認した。"
            f"Pull Requestは除外した。オープンIssueは{len(issues)}件だった。"
        ),
        "",
        ISSUE_TABLE_HEADER,
        "|---|---|---|---:|---|",
    ]
    for issue in issues:
        number = int(issue["number"])
        title = _markdown_cell(str(issue.get("title", "（タイトルなし）")))
        url = issue.get("html_url", f"https://github.com/{repo}/issues/{number}")
        labels = [
            _markdown_cell(str(label.get("name", "")))
            for label in issue.get("labels", [])
            if label.get("name")
        ]
        relation = f"ラベル: {', '.join(labels)}" if labels else "API取得時点でオープン"
        lines.append(
            f"| [#{number}]({url}) {title} | 未完了 | "
            f"{_jst_timestamp(str(issue['updated_at']))} | "
            f"{int(issue.get('comments', 0))}件 | {relation} |"
        )
    return "\n".join(lines)


def _replace_issue_section(markdown: str, section: str) -> str:
    match = ISSUE_HEADING_RE.search(markdown)
    if match:
        if re.search(r"^##\s+", markdown[match.end() :], re.MULTILINE):
            raise ValueError("GitHub Issue状況セクションは作業記録の末尾に置いてください")
        prefix = markdown[: match.start()].rstrip()
        return f"{prefix}\n\n{section}\n"
    return f"{markdown.rstrip()}\n\n{section}\n"


def _extract_issue_numbers(markdown: str) -> tuple[set[int], list[str]]:
    matches = list(ISSUE_HEADING_RE.finditer(markdown))
    if len(matches) != 1:
        return set(), ["現在値のIssue状況セクションが1つ必要です"]
    section = markdown[matches[0].start() :]
    lines = section.splitlines()
    errors: list[str] = []
    if ISSUE_TABLE_HEADER not in lines:
        errors.append(f"必須のIssue表ヘッダーがありません: {ISSUE_TABLE_HEADER}")
    if "GitHub APIで" not in section:
        errors.append("GitHub API取得説明がありません")
    if not re.search(r"^確認日: \d{4}-\d{2}-\d{2}（JST）$", section, re.MULTILINE):
        errors.append("確認日（JST）がありません")
    numbers: list[int] = []
    for line in lines:
        row_match = ISSUE_ROW_RE.match(line)
        if row_match:
            numbers.append(int(row_match.group(1)))
    if len(numbers) != len(set(numbers)):
        errors.append("Issue番号が重複しています")
    return set(numbers), errors


def check_record(path: Path, issues: list[dict[str, Any]]) -> int:
    markdown = path.read_text(encoding="utf-8")
    actual, errors = _extract_issue_numbers(markdown)
    expected = {int(issue["number"]) for issue in issues}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"未記載のオープンIssue: {missing}")
    if extra:
        errors.append(f"API上で確認できないIssueの記載: {extra}")
    if errors:
        print(f"GitHub Issue状況の検証に失敗しました: {path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"GitHub Issue状況の検証に成功しました: {path}（{len(expected)}件）")
    return 0


def main() -> int:
    args = _parse_args()
    try:
        path = _record_path(args.record)
        issues = fetch_open_issues(args.repo)
        if args.check:
            return check_record(path, issues)
        section = build_issue_section(args.repo, issues)
        path.write_text(
            _replace_issue_section(path.read_text(encoding="utf-8"), section),
            encoding="utf-8",
        )
        if not args.skip_html:
            subprocess.run(
                [sys.executable, "-m", "scripts.dev.convert_work_records_to_html"],
                cwd=ROOT,
                check=True,
            )
        print(f"GitHub Issue状況を更新しました: {path}（{len(issues)}件）")
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
