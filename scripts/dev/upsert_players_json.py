"""players.json を players テーブルへ upsert する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.db.db import get_client
from scripts.db.db import upsert_players


ALLOWED_KEYS = {
    "player_id",
    "old_player_id",
    "player_name_j",
    "player_name_e",
    "player_slot_category",
    "league_registered_nationality",
    "birthplace",
    "last_seen_team_id",
    "last_seen_jersey_number",
    "entity_type",
    "created_at",
    "updated_at",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="players.json を players テーブルへ upsert する")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("scraper/data/players.json"),
        help="Input players JSON path",
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected list JSON: path={args.input}")

    client = get_client()
    team_rows = client.table("teams").select("team_id").execute().data or []
    valid_team_ids = {str(r.get("team_id")) for r in team_rows if r.get("team_id") is not None}

    # ON CONFLICT エラー回避のため player_id で一意化する（後勝ち）
    deduped: dict[str, dict[str, Any]] = {}
    invalid_team_id_count = 0

    for row in payload:
        if not isinstance(row, dict):
            continue
        filtered = {k: row.get(k) for k in ALLOWED_KEYS if k in row}
        player_id = str(filtered.get("player_id") or "").strip()
        if not player_id:
            continue

        team_id = filtered.get("last_seen_team_id")
        if team_id is not None and str(team_id) not in valid_team_ids:
            filtered["last_seen_team_id"] = None
            invalid_team_id_count += 1

        deduped[player_id] = filtered

    rows = list(deduped.values())

    upsert_players(rows)
    print(f"upserted {len(rows)} players from {args.input}")
    if invalid_team_id_count:
        print(f"normalized invalid last_seen_team_id rows: {invalid_team_id_count}")


if __name__ == "__main__":
    main()
