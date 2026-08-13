"""players.json の league_registered_nationality / birthplace を並列取得する。"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scripts.dev.enrich_players_profile import (
    PROFILE_HEADERS,
    ROSTER_DETAIL_URL,
    _has_text,
    extract_profile_value,
    infer_player_slot_category,
)


def fetch_profile(
    player_id: str,
    timeout: int,
    *,
    max_retries: int = 3,
    backoff_seconds: float = 3.0,
) -> tuple[str, str | None, str | None, str]:
    """5xx・429・接続例外を待機付きで再試行し、取得結果を返す。"""
    if max_retries < 1:
        raise ValueError(f"max_retries must be at least 1: {max_retries}")

    last_status = "error:unknown"
    for attempt in range(max_retries):
        try:
            response = requests.get(
                ROSTER_DETAIL_URL,
                params={"PlayerID": player_id},
                headers=PROFILE_HEADERS,
                timeout=timeout,
            )
            if response.status_code == 404:
                return player_id, None, None, "404"
            if response.status_code == 429 or response.status_code >= 500:
                last_status = f"http_{response.status_code}"
            elif response.status_code >= 400:
                return player_id, None, None, f"http_{response.status_code}"
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                league_nationality = extract_profile_value(soup, "リーグ登録国籍")
                birthplace = extract_profile_value(soup, "出身地")
                return player_id, league_nationality, birthplace, "ok"
        except requests.RequestException as exc:
            last_status = f"error:{type(exc).__name__}"

        if attempt + 1 < max_retries:
            time.sleep(backoff_seconds * (2 ** attempt))

    return player_id, None, None, last_status


def main() -> None:
    parser = argparse.ArgumentParser(description="players.json のプロフィール項目を並列補完する")
    parser.add_argument("--input", type=Path, default=Path("scraper/data/players.json"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output_path = args.output or args.input
    players = json.loads(args.input.read_text(encoding="utf-8"))

    if args.force:
        target_indexes = [i for i, p in enumerate(players) if _has_text(p.get("player_id"))]
    else:
        target_indexes = [
            i for i, p in enumerate(players)
            if not _has_text(p.get("league_registered_nationality"))
            or not _has_text(p.get("birthplace"))
            or not _has_text(p.get("player_slot_category"))
        ]

    futures = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for i in target_indexes:
            player_id = str(players[i].get("player_id") or "").strip()
            if not player_id:
                continue
            futures[executor.submit(fetch_profile, player_id, args.timeout)] = i

        ok = 0
        not_found = 0
        errors = 0
        with_values = 0

        for n, future in enumerate(as_completed(futures), start=1):
            i = futures[future]
            player_id, league_nationality, birthplace, status = future.result()
            player = players[i]

            if not _has_text(player.get("league_registered_nationality")) and _has_text(league_nationality):
                player["league_registered_nationality"] = league_nationality
            if not _has_text(player.get("birthplace")) and _has_text(birthplace):
                player["birthplace"] = birthplace

            slot = infer_player_slot_category(
                player.get("league_registered_nationality"),
                player.get("birthplace"),
            )
            if not _has_text(player.get("player_slot_category")) and slot is not None:
                player["player_slot_category"] = slot

            if status == "ok":
                ok += 1
            elif status == "404":
                not_found += 1
            else:
                errors += 1

            if league_nationality or birthplace:
                with_values += 1

            if n % 100 == 0:
                print(f"progress: {n}/{len(futures)}")

    output_path.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding="utf-8")

    print("done")
    print(f"targets={len(target_indexes)}")
    print(f"ok={ok} not_found={not_found} errors={errors}")
    print(f"rows_with_values={with_values}")
    print(f"written={output_path}")


if __name__ == "__main__":
    main()
