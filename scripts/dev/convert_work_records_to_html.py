#!/usr/bin/env python3
"""Render the current work-record Markdown files as local, static HTML pages."""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_DIR = ROOT / "work-records" / "md"
OUTPUT_DIR = ROOT / "work-records"
DATE_RE = re.compile(r"^作成日:\s*(\S+)\s*$")
HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|(\d+)\.)\s+(.+?)\s*$")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$"
)
OMITTED_H2_PREFIXES = ("GitHub Issue", "GitHub側の整理")
CURRENT_GITHUB_H2_PREFIX = "GitHub Issue状況（"
SECTION_LABELS = {
    "概要": "概要",
    "背景": "背景",
    "対象": "対象",
    "目的": "目的",
    "親タスク": "タスク",
    "実行内容": "実行",
    "初回結果": "初回",
    "件数増分確認": "件数",
    "次アクション案": "次の作業",
    "再チャレンジ結果": "再実行",
    "Planning 統合メモ（2026-05-26）": "計画",
    "ここまでの完了事項（サマリー）": "完了",
    "全シーズン投入後の確認結果（2026-05-26）": "確認",
    "実施事項": "実施",
    "対応内容": "対応",
    "決定事項": "決定",
    "目視確認での補足事項": "補足",
    "作成物": "成果物",
    "現時点のCSV欠損": "欠損",
    "関連ファイル": "ファイル",
    "補足": "補足",
    "追記（2026-05-26: 再実行時エラー対応）": "追記",
    "完了報告（2026-05-26）": "完了",
    "原因": "原因",
    "原因と対応方針": "原因",
    "変換スクリプトの修正": "修正",
    "全月次JSONの検証": "検証",
    "live DBデータパッチ": "パッチ",
    "live DB適用後の確認結果": "確認",
    "live DB適用後の全件監査": "監査",
    "変更しない項目": "対象外",
    "取得結果（players.json）": "取得結果",
    "Upsert実行結果": "実行結果",
    "次アクション": "次の作業",
    "DB反映確認（players）": "確認",
    "このスレッドで確認したこと": "確認",
    "補足調査（欠損理由の切り分け）": "補足調査",
    "本スレッドの着地": "結論",
    "実装": "実装",
    "live差分監査結果": "監査",
    "IDと重複": "ID",
    "live欠損の内訳": "欠損",
    "共通693 IDの値差分": "差分",
    "3件プレビュー": "プレビュー",
    "未実施と次の判断": "次の判断",
    "選手・スタッフ分類": "分類",
    "全対象プロフィール監査": "監査",
    "正本候補とスキーマ整合": "整合",
    "残作業": "残作業",
    "反映SQL・ロールバックSQL": "SQL",
    "関連Issue": "関連",
    "検証": "検証",
    "適用状況": "結果",
    "完了判定": "判定",
    "GitHub Issue状況（2026-08-13時点の現在値）": "Issue状況",
}


def inline_markdown(value: str) -> str:
    """Render the inline Markdown used by the work records."""

    placeholders: list[str] = []

    def hold(value_to_hold: str) -> str:
        placeholders.append(value_to_hold)
        return f"\x00{len(placeholders) - 1}\x00"

    value = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: hold(
            f'<a href="{html.escape(match.group(2), quote=True)}">'
            f"{inline_markdown(match.group(1))}</a>"
        ),
        value,
    )
    value = html.escape(value, quote=False)
    value = re.sub(r"`([^`]+)`", lambda match: hold(f"<code>{match.group(1)}</code>"), value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)

    for index, replacement in enumerate(placeholders):
        value = value.replace(f"\x00{index}\x00", replacement)
    return value


def strip_frontmatter(lines: list[str]) -> tuple[list[str], str | None]:
    if not lines or lines[0].strip() != "---":
        return lines, None

    end_index = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end_index is None:
        return lines, None

    frontmatter = lines[1:end_index]
    title = None
    for line in frontmatter:
        match = re.match(r"^title:\s*[\"']?(.*?)[\"']?\s*$", line)
        if match:
            title = match.group(1)
            break
    return lines[end_index + 1 :], title


def document_title(lines: list[str], frontmatter_title: str | None, filename: str) -> tuple[str, str | None]:
    title = frontmatter_title
    date = None
    for line in lines:
        date_match = DATE_RE.match(line.strip())
        if date_match:
            date = date_match.group(1)
    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match and len(heading_match.group(1)) == 1:
            heading = heading_match.group(2)
            if heading.startswith("作業記録 ") and ":" in heading:
                title = heading.split(":", 1)[1].strip()
            elif title is None:
                title = heading
            break
    return title or filename, date


def remove_title_and_date(lines: list[str]) -> list[str]:
    result = []
    removed_title = False
    for line in lines:
        if not removed_title and HEADING_RE.match(line) and len(HEADING_RE.match(line).group(1)) == 1:
            removed_title = True
            continue
        if removed_title and DATE_RE.match(line.strip()):
            continue
        result.append(line)
    return result


def omit_github_state(lines: list[str]) -> tuple[list[str], bool]:
    result: list[str] = []
    skipping = False
    omitted = False
    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            heading = heading_match.group(2)
            if skipping and level <= 2:
                skipping = False
            is_current_github_section = (
                level == 2
                and heading.startswith(CURRENT_GITHUB_H2_PREFIX)
                and "現在値" in heading
            )
            if (
                level == 2
                and any(heading.startswith(prefix) for prefix in OMITTED_H2_PREFIXES)
                and not is_current_github_section
            ):
                skipping = True
                omitted = True
                continue
        if not skipping:
            result.append(line)
    return result, omitted


def table_cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in value.split("|")]


def render_table(lines: list[str], index: int) -> tuple[str, int]:
    header = table_cells(lines[index])
    index += 2
    rows: list[list[str]] = []
    while index < len(lines) and "|" in lines[index] and lines[index].strip():
        rows.append(table_cells(lines[index]))
        index += 1
    output = ["<table>", "<thead><tr>"]
    output.extend(f"<th>{inline_markdown(cell)}</th>" for cell in header)
    output.append("</tr></thead><tbody>")
    for row in rows:
        output.append("<tr>")
        output.extend(f"<td>{inline_markdown(cell)}</td>" for cell in row)
        output.append("</tr>")
    output.append("</tbody></table>")
    return "".join(output), index


def render_list(lines: list[str], index: int) -> tuple[str, int]:
    first_match = LIST_RE.match(lines[index])
    assert first_match is not None
    base_indent = len(first_match.group(1).replace("\t", "    "))
    tag = "ol" if first_match.group(3) else "ul"
    output = [f"<{tag}>"]

    while index < len(lines):
        match = LIST_RE.match(lines[index])
        if match is None:
            break
        indent = len(match.group(1).replace("\t", "    "))
        if indent < base_indent:
            break
        if indent > base_indent:
            nested, index = render_list(lines, index)
            if output[-1].endswith("</li>"):
                output[-1] = output[-1][:-5] + nested + "</li>"
            else:
                output.append(nested)
            continue
        current_tag = "ol" if match.group(3) else "ul"
        if current_tag != tag:
            break
        content = match.group(4)
        if content.startswith("[x] ") or content.startswith("[X] "):
            content = f"完了：{content[4:]}"
        elif content.startswith("[ ] "):
            content = f"未完了：{content[4:]}"
        output.append(f"<li>{inline_markdown(content)}</li>")
        index += 1
    output.append(f"</{tag}>")
    return "".join(output), index


def render_ordered_list(lines: list[str], index: int) -> tuple[str, int]:
    """Keep top-level ordered items together when child headings interrupt them."""

    output = ["<ol>"]
    while index < len(lines):
        match = LIST_RE.match(lines[index])
        if match is None or match.group(3) is None or match.group(1).strip():
            break
        content = match.group(4)
        index += 1
        child_lines: list[str] = []
        while index < len(lines):
            next_list = LIST_RE.match(lines[index])
            next_heading = HEADING_RE.match(lines[index])
            if next_list and next_list.group(3) and not next_list.group(1).strip():
                break
            if next_heading and len(next_heading.group(1)) <= 3:
                break
            child_lines.append(lines[index])
            index += 1
        child_content = render_content(child_lines) if any(line.strip() for line in child_lines) else ""
        output.append(f"<li>{inline_markdown(content)}{child_content}</li>")
    output.append("</ol>")
    return "".join(output), index


def render_content(lines: list[str]) -> str:
    output: list[str] = []
    index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            output.append(f"<p>{inline_markdown(text)}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            language_class = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            output.append(f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>")
            continue
        heading_match = HEADING_RE.match(line)
        if heading_match and len(heading_match.group(1)) >= 3:
            flush_paragraph()
            level = min(len(heading_match.group(1)), 4)
            output.append(f"<h{level}>{inline_markdown(heading_match.group(2))}</h{level}>")
            index += 1
            continue
        if "|" in stripped and index + 1 < len(lines) and TABLE_SEPARATOR_RE.match(lines[index + 1]):
            flush_paragraph()
            table, index = render_table(lines, index)
            output.append(table)
            continue
        if LIST_RE.match(line):
            flush_paragraph()
            if LIST_RE.match(line).group(3) and not LIST_RE.match(line).group(1).strip():
                rendered_list, index = render_ordered_list(lines, index)
            else:
                rendered_list, index = render_list(lines, index)
            output.append(rendered_list)
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            output.append(f"<blockquote>{inline_markdown(' '.join(quote_lines))}</blockquote>")
            continue
        if stripped == "---":
            flush_paragraph()
            index += 1
            continue
        paragraph.append(line)
        index += 1
    flush_paragraph()
    return "\n".join(output)


def render_sections(lines: list[str]) -> str:
    output: list[str] = []
    preamble: list[str] = []
    index = 0
    while index < len(lines):
        heading_match = HEADING_RE.match(lines[index])
        if not heading_match or len(heading_match.group(1)) != 2:
            preamble.append(lines[index])
            index += 1
            continue
        break
    if any(line.strip() for line in preamble):
        output.append(
            '<section class="record-section"><div class="section-intro">'
            '<p class="section-label">記録</p><h2>補足</h2></div>'
            f'<div class="section-content">{render_content(preamble)}</div></section>'
        )

    index = len(preamble)
    section_number = 0
    while index < len(lines):
        heading_match = HEADING_RE.match(lines[index])
        if not heading_match or len(heading_match.group(1)) != 2:
            index += 1
            continue
        heading = heading_match.group(2)
        section_number += 1
        index += 1
        section_lines: list[str] = []
        while index < len(lines):
            next_heading = HEADING_RE.match(lines[index])
            if next_heading and len(next_heading.group(1)) <= 2:
                break
            section_lines.append(lines[index])
            index += 1
        label = (
            "Issue状況"
            if heading.startswith(CURRENT_GITHUB_H2_PREFIX)
            else SECTION_LABELS.get(heading, "記録")
        )
        output.append(
            '<section class="record-section">'
            '<div class="section-intro">'
            f'<p class="section-label">{section_number:02d}　{html.escape(label)}</p>'
            f'<h2>{inline_markdown(heading)}</h2>'
            '</div>'
            f'<div class="section-content">{render_content(section_lines)}</div>'
            '</section>'
        )
    return "\n".join(output)


def render_document(path: Path) -> tuple[str, bool]:
    original_text = path.read_text(encoding="utf-8")
    original_lines = original_text.splitlines()
    lines, frontmatter_title = strip_frontmatter(original_lines)
    title, date = document_title(lines, frontmatter_title, path.stem)
    lines = remove_title_and_date(lines)
    has_current_github_section = any(
        (heading_match := HEADING_RE.match(line))
        and len(heading_match.group(1)) == 2
        and heading_match.group(2).startswith(CURRENT_GITHUB_H2_PREFIX)
        and "現在値" in heading_match.group(2)
        for line in lines
    )
    lines, omitted_github_section = omit_github_state(lines)
    has_issue_reference = bool(re.search(r"GitHub Issue|Issue #|親Issue|子Issue|関連Issue", original_text))

    record_number_match = re.fullmatch(r"work_record_(\d{3})", path.stem)
    record_label = f"作業記録 {record_number_match.group(1)}" if record_number_match else "補助文書"
    date_label = date or "作成日記載なし"
    note = ""
    if (
        not has_current_github_section
        and (omitted_github_section or has_issue_reference)
    ):
        note = (
            '<aside class="history-note">'
            '<h2>GitHub Issueの状態（省略）</h2>'
            '<p>当時のGitHub Issueの未完了・完了、親子関係、優先順位などは、現在の状態から正確に再現できないため、このHTMLでは省略しています。'
            '本文中のIssue番号・リンクは、作業記録上の参照情報として残しています。</p>'
            '</aside>'
        )

    sections = render_sections(lines)
    if not sections:
        sections = (
            '<section class="record-section"><div class="section-intro">'
            '<p class="section-label">記録</p><h2>本文なし</h2></div>'
            '<div class="section-content"><p>このMarkdownにはタイトル以外の本文がありません。</p></div>'
            '</section>'
        )

    document = f'''<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light">
    <title>{html.escape(title)} — 作業記録</title>
    <link rel="stylesheet" href="work_record.css">
  </head>
  <body>
    <div class="shell">
      <header class="topbar">
        <a class="wordmark" href="../README.md">B.LEAGUE STATS</a>
        <nav class="toplinks" aria-label="関連文書">
          <a href="README.md">運用ルール</a>
          <a href="design.md">デザイン原則</a>
          <a href="md/{html.escape(path.name, quote=True)}">Markdownを読む</a>
        </nav>
      </header>
      <main>
        <header class="record-header">
          <p class="kicker">{html.escape(record_label)} ・ {html.escape(date_label)}</p>
          <h1>{html.escape(title)}</h1>
          <dl class="record-meta">
            <div><dt>原本</dt><dd><code>md/{html.escape(path.name)}</code></dd></div>
            <div><dt>状態</dt><dd>記録本文をHTML化</dd></div>
          </dl>
        </header>
        {sections}
        {note}
      </main>
      <footer>
        <span>B.LEAGUE Stats · {html.escape(record_label)}</span>
        <span><a href="md/{html.escape(path.name, quote=True)}">Markdown原本</a></span>
      </footer>
    </div>
  </body>
</html>
'''
    document = "\n".join(line.rstrip() for line in document.splitlines()) + "\n"
    return document, has_issue_reference or omitted_github_section


def main() -> int:
    markdown_paths = sorted(MARKDOWN_DIR.glob("*.md"))
    for markdown_path in markdown_paths:
        document, _ = render_document(markdown_path)
        output_name = f"{markdown_path.stem}.html"
        (OUTPUT_DIR / output_name).write_text(document, encoding="utf-8")
        print(f"generated {OUTPUT_DIR / output_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
