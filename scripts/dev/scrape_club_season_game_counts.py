"""公式クラブページからチーム・シーズン別の試合数を取得する。

公式クラブページの「クラブシーズン成績 > 合計」表を読み取り、
ローカルの試合JSONから集計した件数と並べてCSVへ出力する。
既定の対象はB1レギュラーシーズンとする。

Usage:
    python -m scripts.dev.scrape_club_season_game_counts
    python -m scripts.dev.scrape_club_season_game_counts --team-id 2486
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.bleague.jp/club_detail/"
DEFAULT_INPUT_GLOB = "scraper/data/season_*/games_*.json"
DEFAULT_OUTPUT = Path("scraper/data/club_season_game_counts.csv")
DEFAULT_CANDIDATE_INPUT = Path("scraper/data/game_supplement_candidates.csv")
SEASON_PATTERN = re.compile(r"^\d{4}-\d{2}$")

CSV_FIELDS = [
    "team_id",
    "team_name_j",
    "page_team_name_j",
    "season",
    "competition",
    "official_game_count",
    "official_win_count",
    "official_loss_count",
    "local_game_count",
    "local_season_game_count",
    "difference",
    "comparison_status",
    "supplement_candidate_game_count",
    "supplement_candidate_status",
    "remaining_team_game_count",
    "remaining_status",
    "source_url",
    "fetch_status",
    "error",
    "fetched_at",
]


def _text(node: Any) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _parse_int(value: str) -> int | None:
    normalized = value.replace(",", "").strip()
    if not normalized or normalized in {"-", "—"}:
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


def _normalize_competition(value: str) -> str:
    text = value.upper().replace(" ", "")
    if "CHAMPIONSHIP" in text or "チャンピオンシップ" in value or text in {"CS", "PO"}:
        return "POSTSEASON"
    if "ALL-STAR" in text or "ALLSTAR" in text or "オールスター" in value:
        return "ALLSTAR"
    if "U18" in text:
        return "U18"
    if "B3RS" in text:
        return "B3RS"
    for league in ("B1", "B2", "B3"):
        if league in text:
            return league
    if "昇格" in value:
        return "昇格"
    if "PO" == text:
        return "PO"
    return value.strip()


def _extract_local_reference(
    input_glob: str,
) -> tuple[dict[str, str], Counter[tuple[str, str, str]], Counter[tuple[str, str]]]:
    """ローカルJSONからチーム名と大会別・シーズン別件数を集計する。"""
    team_names: dict[str, str] = {}
    competition_counts: Counter[tuple[str, str, str]] = Counter()
    season_counts: Counter[tuple[str, str]] = Counter()

    paths = sorted(Path(".").glob(input_glob))
    if not paths:
        raise FileNotFoundError(f"入力JSONが見つかりません: {input_glob}")

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        season = str(payload.get("season") or "")
        for item in payload.get("games", []):
            if not isinstance(item, dict) or item.get("error"):
                continue
            game = item.get("game")
            if not isinstance(game, dict):
                continue

            competition = _normalize_competition(str(game.get("ConventionNameJ") or ""))
            for side in ("Home", "Away"):
                team_id = game.get(f"{side}TeamID")
                if team_id is None:
                    continue
                team_id_text = str(team_id)
                name = str(game.get(f"{side}TeamNameJ") or "").strip()
                if name:
                    team_names.setdefault(team_id_text, name)
                competition_counts[(team_id_text, season, competition)] += 1
                season_counts[(team_id_text, season)] += 1

    return team_names, competition_counts, season_counts


def _find_total_table(soup: BeautifulSoup) -> Any:
    for heading in soup.find_all(["h2", "h3", "h4"]):
        if _text(heading) != "クラブシーズン成績":
            continue
        container = heading.parent
        for table in container.find_all("table"):
            header_rows = table.select("thead tr")
            header_text = [_text(cell) for cell in header_rows[-1].find_all(["th", "td"])] if header_rows else []
            if len(header_text) >= 3 and header_text[0] == "SEASON" and header_text[1] == "TYPE" and header_text[2] == "G":
                return table
    return None


def _extract_candidate_counts(input_path: Path) -> Counter[tuple[str, str]]:
    """補完候補CSVからチーム・シーズン別の候補試合数を集計する。"""
    counts: Counter[tuple[str, str]] = Counter()
    if not input_path.exists():
        return counts
    with input_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("candidate_status") != "candidate":
                continue
            season = str(row.get("season") or "").strip()
            if not season:
                continue
            counted_team_ids = [
                team_id.strip()
                for team_id in str(row.get("counted_team_ids") or "").split("|")
                if team_id.strip()
            ]
            if not counted_team_ids:
                counted_team_ids = [
                    str(row.get(field) or "").strip()
                    for field in ("home_team_id", "away_team_id")
                    if str(row.get(field) or "").strip()
                ]
            for team_id in counted_team_ids:
                if team_id:
                    counts[(team_id, season)] += 1
    return counts


def _candidate_status(candidate_count: int, difference: int) -> str:
    if difference >= 0:
        return "not_needed"
    missing_count = abs(difference)
    if candidate_count == missing_count:
        return "candidate_complete"
    if candidate_count > 0:
        return "candidate_partial"
    return "no_candidate"


def _remaining_status(remaining_count: int, difference: int) -> str:
    if difference >= 0:
        return "not_needed"
    return "remaining" if remaining_count else "covered"


def _parse_page_rows(html: str) -> tuple[str, list[dict[str, Any]]]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one(".clubDetail-kv-name")
    page_team_name = _text(title)
    table = _find_total_table(soup)
    if table is None:
        return page_team_name, []

    rows: list[dict[str, Any]] = []
    for tr in table.select("tbody tr"):
        cells = [_text(cell) for cell in tr.find_all("td")]
        if len(cells) < 5 or not SEASON_PATTERN.fullmatch(cells[0]):
            continue
        game_count = _parse_int(cells[2])
        if game_count is None:
            continue
        rows.append(
            {
                "season": cells[0],
                "competition": cells[1],
                "competition_key": _normalize_competition(cells[1]),
                "official_game_count": game_count,
                "official_win_count": _parse_int(cells[3]),
                "official_loss_count": _parse_int(cells[4]),
            }
        )
    return page_team_name, rows


def _fetch_page(session: requests.Session, team_id: str, max_retries: int) -> tuple[str, list[dict[str, Any]], str, str]:
    url = f"{BASE_URL}?TeamID={team_id}"
    last_error = ""
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=(15, 45))
            response.raise_for_status()
            page_team_name, rows = _parse_page_rows(response.text)
            status = "ok" if rows else "ok_no_rows"
            return page_team_name, rows, status, ""
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc).replace("\n", " ")
            if attempt + 1 < max_retries:
                time.sleep(2**attempt)
    return "", [], "error", last_error


def scrape(
    *,
    team_ids: list[str],
    team_names: dict[str, str],
    competition_counts: Counter[tuple[str, str, str]],
    season_counts: Counter[tuple[str, str]],
    candidate_counts: Counter[tuple[str, str]],
    output_path: Path,
    min_sleep: float,
    max_sleep: float,
    max_retries: int,
    target_competition: str,
) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; BStatsSiteAudit/1.0)",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
    )

    for index, team_id in enumerate(team_ids):
        if index > 0:
            time.sleep(random.uniform(min_sleep, max_sleep))
        page_name, official_rows, fetch_status, error = _fetch_page(session, team_id, max_retries)
        source_url = f"{BASE_URL}?TeamID={team_id}"
        if not official_rows:
            rows.append(
                {
                    "team_id": team_id,
                    "team_name_j": team_names.get(team_id, ""),
                    "page_team_name_j": page_name,
                    "season": "",
                    "competition": "",
                    "official_game_count": "",
                    "official_win_count": "",
                    "official_loss_count": "",
                    "local_game_count": "",
                    "local_season_game_count": "",
                    "difference": "",
                    "comparison_status": "not_available",
                    "supplement_candidate_game_count": "",
                    "supplement_candidate_status": "not_available",
                    "remaining_team_game_count": "",
                    "remaining_status": "not_available",
                    "source_url": source_url,
                    "fetch_status": fetch_status,
                    "error": error,
                    "fetched_at": fetched_at,
                }
            )
            print(f"{team_id}: {fetch_status} ({page_name or team_names.get(team_id, '')})")
            continue

        target_rows = [
            official
            for official in official_rows
            if official["competition_key"] == target_competition
        ]
        for official in target_rows:
            key = (team_id, official["season"], official["competition_key"])
            local_count = competition_counts.get(key, 0)
            local_season_count = season_counts.get((team_id, official["season"]), 0)
            difference = local_count - official["official_game_count"]
            candidate_count = candidate_counts.get((team_id, official["season"]), 0)
            remaining_count = max(0, -difference - candidate_count)
            if local_count == official["official_game_count"]:
                comparison_status = "match"
            elif local_count == 0 and local_season_count > 0:
                comparison_status = "competition_not_matched"
            elif local_count == 0:
                comparison_status = "local_missing"
            else:
                comparison_status = "count_diff"
            rows.append(
                {
                    "team_id": team_id,
                    "team_name_j": team_names.get(team_id, ""),
                    "page_team_name_j": page_name,
                    **{key: official[key] for key in ("season", "competition", "official_game_count", "official_win_count", "official_loss_count")},
                    "local_game_count": local_count,
                    "local_season_game_count": local_season_count,
                    "difference": difference,
                    "comparison_status": comparison_status,
                    "supplement_candidate_game_count": candidate_count,
                    "supplement_candidate_status": _candidate_status(candidate_count, difference),
                    "remaining_team_game_count": remaining_count,
                    "remaining_status": _remaining_status(remaining_count, difference),
                    "source_url": source_url,
                    "fetch_status": fetch_status,
                    "error": "",
                    "fetched_at": fetched_at,
                }
            )
        print(f"{team_id}: {len(target_rows)} {target_competition} rows ({page_name or team_names.get(team_id, '')})")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV: {output_path} ({len(rows)} rows)")


def main() -> None:
    parser = argparse.ArgumentParser(description="公式クラブページのチーム・シーズン別試合数をCSV化")
    parser.add_argument("--team-id", action="append", default=[], help="対象TeamID。複数指定可。省略時はローカルJSONから全件抽出")
    parser.add_argument("--competition", default="B1", help="対象大会の正規化キー（既定: B1）")
    parser.add_argument("--input-glob", default=DEFAULT_INPUT_GLOB, help=f"ローカル試合JSONのglob（既定: {DEFAULT_INPUT_GLOB}）")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-sleep", type=float, default=1.0)
    parser.add_argument("--max-sleep", type=float, default=3.0)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()
    if args.min_sleep < 0 or args.max_sleep < args.min_sleep:
        parser.error("--min-sleep / --max-sleep の値が不正です")
    if args.max_retries < 1:
        parser.error("--max-retries は1以上を指定してください")

    team_names, competition_counts, season_counts = _extract_local_reference(args.input_glob)
    candidate_counts = _extract_candidate_counts(DEFAULT_CANDIDATE_INPUT)
    if args.team_id:
        team_ids = sorted(set(args.team_id))
    else:
        team_ids = sorted({
            team_id
            for (team_id, _, competition) in competition_counts
            if competition == args.competition
        })
    if not team_ids:
        parser.error("対象TeamIDが見つかりません")
    print(f"対象TeamID: {len(team_ids)}件")
    scrape(
        team_ids=team_ids,
        team_names=team_names,
        competition_counts=competition_counts,
        season_counts=season_counts,
        candidate_counts=candidate_counts,
        output_path=args.output,
        min_sleep=args.min_sleep,
        max_sleep=args.max_sleep,
        max_retries=args.max_retries,
        target_competition=args.competition,
    )


if __name__ == "__main__":
    main()
