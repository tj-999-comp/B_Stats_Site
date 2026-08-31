#!/usr/bin/env python3
"""Synchronize a work record's GitHub Issue status section.

The Markdown work record remains the source of truth for the A-rendered HTML,
but the current Issue section is generated from GitHub's open issues API. Pull
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
POLICY_PATH = Path(__file__).with_name("github_issue_status_policy.json")
ISSUE_HEADING_RE = re.compile(
    r"^## GitHub Issue状況（\d{4}-\d{2}-\d{2}時点の現在値）\s*$",
    re.MULTILINE,
)
ISSUE_TABLE_HEADER = "| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |"
ISSUE_ROW_RE = re.compile(r"^\|\s*\d+\s*\|\s*P[0-3]\s*\|\s*\[#(\d+)\]\([^)]*\)")
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


def _fetch_with_token(repo: str, token: str, path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        url = f"https://api.github.com/repos/{repo}/{path}{separator}per_page=100&page={page}"
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
        items.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
    return items


def _fetch_with_gh(repo: str, path: str) -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            [
                "gh",
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repo}/{path}&per_page=100"
                if "?" in path
                else f"repos/{repo}/{path}?per_page=100",
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


def _fetch_endpoint(repo: str, path: str) -> list[dict[str, Any]]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    return _fetch_with_token(repo, token, path) if token else _fetch_with_gh(repo, path)


def fetch_issues(repo: str, state: str) -> list[dict[str, Any]]:
    raw_issues = _fetch_endpoint(repo, f"issues?state={state}")
    issues = [item for item in raw_issues if "pull_request" not in item]
    return sorted(issues, key=lambda item: int(item["number"]))


def fetch_subissues(repo: str, issue_numbers: list[int]) -> dict[int, list[int]]:
    children: dict[int, list[int]] = {}
    for number in issue_numbers:
        raw_children = _fetch_endpoint(repo, f"issues/{number}/sub_issues")
        child_numbers = sorted(
            int(item["number"])
            for item in raw_children
            if "pull_request" not in item and item.get("number") is not None
        )
        if child_numbers:
            children[number] = child_numbers
    return children


def _jst_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S JST")


def _markdown_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value).replace("|", "\\|").strip()


def _load_policy() -> dict[str, Any]:
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Issue状況ポリシーを読めません: {POLICY_PATH}") from error
    if not isinstance(policy, dict):
        raise RuntimeError(f"Issue状況ポリシーの形式が不正です: {POLICY_PATH}")
    return policy


def _state_label(issue: dict[str, Any]) -> str:
    return "未完了" if issue.get("state") == "open" else "完了"


def _render_parent_tree(
    parent_children: dict[int, list[int]], issues_by_number: dict[int, dict[str, Any]]
) -> list[str]:
    if not parent_children:
        return ["親子関係はGitHub上で登録されていない。"]

    child_numbers = {child for children in parent_children.values() for child in children}
    roots = sorted(parent for parent in parent_children if parent not in child_numbers)
    lines: list[str] = []

    def render_node(number: int, prefix: str, role: str) -> None:
        issue = issues_by_number.get(number, {"state": "closed"})
        lines.append(f"{prefix}#{number}（{_state_label(issue)}・{role}）")
        children = parent_children.get(number, [])
        for index, child in enumerate(children):
            connector = "└── " if index == len(children) - 1 else "├── "
            render_node(child, prefix + connector, "子Issue")

    for root in roots:
        render_node(root, "", "親Issue")
    return lines


def _relation_for_issue(
    number: int,
    policy: dict[str, Any],
    parent_by_child: dict[int, int],
    parent_children: dict[int, list[int]],
) -> str:
    configured = policy.get("relation", {}).get(str(number))
    if configured:
        return str(configured)
    if number in parent_by_child:
        parent = parent_by_child[number]
        return f"#{parent}の子Issue。#{parent}完了後"
    if number in parent_children:
        children = ", ".join(f"#{child}" for child in parent_children[number])
        return f"親Issue。子Issue: {children}"
    return "独立。優先度未設定"


def build_issue_section(
    repo: str,
    open_issues: list[dict[str, Any]],
    all_issues: list[dict[str, Any]],
    parent_children: dict[int, list[int]],
) -> str:
    policy = _load_policy()
    checked_at = datetime.now(JST)
    checked_date = checked_at.strftime("%Y-%m-%d")
    issues_by_number = {int(issue["number"]): issue for issue in all_issues}
    parent_by_child = {
        child: parent
        for parent, children in parent_children.items()
        for child in children
    }
    default_priority = str(policy.get("default_priority", "P3"))
    priorities = {
        str(number): str(priority)
        for number, priority in policy.get("priority", {}).items()
    }
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    sorted_issues = sorted(
        open_issues,
        key=lambda issue: (
            priority_order.get(priorities.get(str(issue["number"]), default_priority), 3),
            int(issue["number"]),
        ),
    )
    lines = [
        f"## GitHub Issue状況（{checked_date}時点の現在値）",
        "",
        f"確認日: {checked_date}（JST）",
        "",
        (
            f"GitHub APIで `{repo}` のIssueを確認した。Pull Requestは対象外とした。"
            f"未完了Issueは{len(open_issues)}件だった。"
        ),
        "",
        "### 親子関係",
        "",
        "```text",
        *_render_parent_tree(parent_children, issues_by_number),
        "```",
        "",
        "GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。",
        "",
        "### 優先順位順の未完了一覧",
        "",
        "優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。",
        "",
        ISSUE_TABLE_HEADER,
        "|---:|---|---|---|---|",
    ]
    for rank, issue in enumerate(sorted_issues, start=1):
        number = int(issue["number"])
        title = _markdown_cell(str(issue.get("title", "（タイトルなし）")))
        url = issue.get("html_url", f"https://github.com/{repo}/issues/{number}")
        priority = priorities.get(str(number), default_priority)
        relation = _markdown_cell(
            _relation_for_issue(number, policy, parent_by_child, parent_children)
        )
        lines.append(
            f"| {rank} | {priority} | [#{number}]({url}) {title} | "
            f"{_state_label(issue)} | {relation} |"
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
    if "### 親子関係" not in lines:
        errors.append("親子関係セクションがありません")
    if "### 優先順位順の未完了一覧" not in lines:
        errors.append("優先順位順の未完了一覧セクションがありません")
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


def _current_issue_section(markdown: str) -> str:
    matches = list(ISSUE_HEADING_RE.finditer(markdown))
    if len(matches) != 1:
        raise ValueError("現在値のIssue状況セクションが1つ必要です")
    return markdown[matches[0].start() :].strip()


def _normalize_dynamic_values(section: str) -> str:
    section = re.sub(
        r"^## GitHub Issue状況（\d{4}-\d{2}-\d{2}時点の現在値）$",
        "## GitHub Issue状況（確認時点の現在値）",
        section,
        flags=re.MULTILINE,
    )
    return re.sub(r"^確認日: \d{4}-\d{2}-\d{2}（JST）$", "確認日: （JST）", section, flags=re.MULTILINE)


def check_record(
    path: Path,
    repo: str,
    open_issues: list[dict[str, Any]],
    all_issues: list[dict[str, Any]],
    parent_children: dict[int, list[int]],
) -> int:
    markdown = path.read_text(encoding="utf-8")
    actual, errors = _extract_issue_numbers(markdown)
    expected = {int(issue["number"]) for issue in open_issues}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"未記載のオープンIssue: {missing}")
    if extra:
        errors.append(f"API上で確認できないIssueの記載: {extra}")
    if not errors:
        expected_section = build_issue_section(
            repo, open_issues, all_issues, parent_children
        )
        actual_section = _current_issue_section(markdown)
        if _normalize_dynamic_values(actual_section) != _normalize_dynamic_values(
            expected_section
        ):
            errors.append(
                "Issue状況の内容がAPI・親子関係・優先度ポリシーから生成した結果と一致しません。"
                " --writeで再生成してください"
            )
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
        open_issues = fetch_issues(args.repo, "open")
        all_issues = fetch_issues(args.repo, "all")
        parent_children = fetch_subissues(
            args.repo, [int(issue["number"]) for issue in all_issues]
        )
        if args.check:
            return check_record(
                path, args.repo, open_issues, all_issues, parent_children
            )
        section = build_issue_section(args.repo, open_issues, all_issues, parent_children)
        path.write_text(
            _replace_issue_section(path.read_text(encoding="utf-8"), section),
            encoding="utf-8",
        )
        print(f"GitHub Issue状況を更新しました: {path}（{len(open_issues)}件）")
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
