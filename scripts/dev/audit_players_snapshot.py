"""live players を別ファイルへ保存し、ローカル正本との差分を監査する。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.db.db import fetch_all_players


AUDIT_FIELDS = (
    "player_name_e",
    "birthplace",
    "league_registered_nationality",
    "player_slot_category",
    "last_seen_team_id",
    "last_seen_jersey_number",
)
COMPARISON_FIELDS = (
    "player_name_j",
    *AUDIT_FIELDS,
)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _normalized(value: Any) -> str | None:
    if not _has_text(value):
        return None
    return str(value).strip()


def _player_id(row: dict[str, Any]) -> str:
    return str(row.get("player_id") or "").strip()


def _player_id_sort_key(value: str) -> tuple[int, int | str]:
    if value.isdigit():
        return 0, int(value)
    return 1, value


def load_players(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise RuntimeError(f"Expected list[dict] JSON: path={path}")
    return payload


def _group_by_player_id(players: list[dict[str, Any]]) -> dict[str, list[tuple[int, dict[str, Any]]]]:
    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, player in enumerate(players):
        player_id = _player_id(player)
        if player_id:
            grouped[player_id].append((index, player))
    return dict(grouped)


def _count_missing(players: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(not _has_text(player.get(field)) for player in players)
        for field in AUDIT_FIELDS
    }


def build_audit_report(
    live_players: list[dict[str, Any]],
    local_players: list[dict[str, Any]],
    *,
    local_input: Path,
    snapshot_output: Path,
) -> dict[str, Any]:
    live_by_id = {_player_id(player): player for player in live_players if _player_id(player)}
    local_groups = _group_by_player_id(local_players)
    # 現行 upsert_players_json.py と同じ「配列の後勝ち」を比較基準にする。
    local_by_id = {player_id: rows[-1][1] for player_id, rows in local_groups.items()}

    live_ids = set(live_by_id)
    local_ids = set(local_by_id)
    common_ids = live_ids & local_ids
    live_only_ids = live_ids - local_ids
    local_only_ids = local_ids - live_ids

    field_differences: dict[str, list[dict[str, Any]]] = {field: [] for field in COMPARISON_FIELDS}
    for player_id in sorted(common_ids, key=_player_id_sort_key):
        live = live_by_id[player_id]
        local = local_by_id[player_id]
        for field in COMPARISON_FIELDS:
            live_value = _normalized(live.get(field))
            local_value = _normalized(local.get(field))
            if live_value == local_value:
                continue
            field_differences[field].append(
                {
                    "player_id": player_id,
                    "player_name_j": live.get("player_name_j") or local.get("player_name_j"),
                    "live": live_value,
                    "local_last_by_order": local_value,
                }
            )

    duplicate_rows = []
    for player_id, rows in sorted(local_groups.items(), key=lambda item: _player_id_sort_key(item[0])):
        if len(rows) <= 1:
            continue
        duplicate_rows.append(
            {
                "player_id": player_id,
                "player_name_j": rows[-1][1].get("player_name_j"),
                "rows": [
                    {
                        "index": index,
                        "updated_at": row.get("updated_at"),
                        **{field: row.get(field) for field in AUDIT_FIELDS},
                    }
                    for index, row in rows
                ],
            }
        )

    live_missing_with_local_candidate: dict[str, list[dict[str, Any]]] = {}
    for field in AUDIT_FIELDS:
        candidates = []
        for player_id in sorted(common_ids, key=_player_id_sort_key):
            live = live_by_id[player_id]
            if _has_text(live.get(field)):
                continue
            values = sorted(
                {
                    str(row.get(field)).strip()
                    for _, row in local_groups[player_id]
                    if _has_text(row.get(field))
                }
            )
            if values:
                candidates.append(
                    {
                        "player_id": player_id,
                        "player_name_j": live.get("player_name_j"),
                        "local_candidates": values,
                    }
                )
        live_missing_with_local_candidate[field] = candidates

    live_only_rows = [live_by_id[player_id] for player_id in sorted(live_only_ids, key=_player_id_sort_key)]
    local_only_rows = [local_by_id[player_id] for player_id in sorted(local_only_ids, key=_player_id_sort_key)]
    likely_non_player_rows = [
        {
            "player_id": _player_id(player),
            "player_name_j": player.get("player_name_j"),
        }
        for player in live_players
        if not _has_text(player.get("player_name_e"))
        and not _has_text(player.get("last_seen_jersey_number"))
    ]

    return {
        "generated_at": _now_utc_iso(),
        "local_input": str(local_input),
        "snapshot_output": str(snapshot_output),
        "summary": {
            "live_rows": len(live_players),
            "live_unique_player_ids": len(live_ids),
            "local_rows": len(local_players),
            "local_unique_player_ids": len(local_ids),
            "common_player_ids": len(common_ids),
            "live_only_player_ids": len(live_only_ids),
            "local_only_player_ids": len(local_only_ids),
            "local_duplicate_player_ids": len(duplicate_rows),
            "local_extra_duplicate_rows": sum(len(item["rows"]) - 1 for item in duplicate_rows),
            "live_missing": _count_missing(live_players),
            "local_missing_raw_rows": _count_missing(local_players),
            "live_only_missing": _count_missing(live_only_rows),
            "field_difference_counts": {
                field: len(rows) for field, rows in field_differences.items()
            },
            "live_missing_with_local_candidate_counts": {
                field: len(rows)
                for field, rows in live_missing_with_local_candidate.items()
            },
            "likely_non_player_heuristic_count": len(likely_non_player_rows),
        },
        "review_notes": [
            "local comparison uses the final row by array order, matching upsert_players_json.py",
            "likely_non_player_heuristic means both player_name_e and last_seen_jersey_number are blank; it is not an automatic deletion rule",
        ],
        "live_only_rows": live_only_rows,
        "local_only_rows": local_only_rows,
        "local_duplicate_rows": duplicate_rows,
        "field_differences": field_differences,
        "live_missing_with_local_candidate": live_missing_with_local_candidate,
        "likely_non_player_heuristic_rows": likely_non_player_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="live players の別スナップショットとローカル正本の差分レポートを作る"
    )
    parser.add_argument(
        "--local-input",
        type=Path,
        default=Path("scraper/data/players.json"),
    )
    parser.add_argument(
        "--snapshot-output",
        type=Path,
        default=Path("/tmp/b_stats_players_live_snapshot.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("/tmp/b_stats_players_snapshot_audit.json"),
    )
    args = parser.parse_args()

    live_players = fetch_all_players()
    live_players.sort(key=lambda player: _player_id_sort_key(_player_id(player)))
    local_players = load_players(args.local_input)

    args.snapshot_output.parent.mkdir(parents=True, exist_ok=True)
    args.snapshot_output.write_text(
        json.dumps(live_players, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = build_audit_report(
        live_players,
        local_players,
        local_input=args.local_input,
        snapshot_output=args.snapshot_output,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"snapshot={args.snapshot_output}")
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
