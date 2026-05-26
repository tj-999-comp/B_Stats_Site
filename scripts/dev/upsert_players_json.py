"""players.json を players テーブルへ upsert する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.db.db import upsert_players


ALLOWED_KEYS = {
    "player_id",
    "old_player_id",
    "player_name_j",
    "player_name_e",
    "nationality",
    "player_slot_category",
    "league_registered_nationality",
    "birthplace",
    "last_seen_team_id",
    "last_seen_jersey_number",
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

    rows: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        filtered = {k: row.get(k) for k in ALLOWED_KEYS if k in row}
        if filtered.get("player_id"):
            rows.append(filtered)

    upsert_players(rows)
    print(f"upserted {len(rows)} players from {args.input}")


if __name__ == "__main__":
    main()
