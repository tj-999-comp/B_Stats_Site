"""live snapshot、分類、補完監査からレビュー用players正本候補を生成する。"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIT_FIELDS = (
    "player_name_e",
    "birthplace",
    "league_registered_nationality",
    "player_slot_category",
    "last_seen_team_id",
    "last_seen_jersey_number",
)
PATCHABLE_FIELDS = {
    "league_registered_nationality",
    "birthplace",
    "player_slot_category",
}


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _player_id(row: dict[str, Any]) -> str:
    return str(row.get("player_id") or "").strip()


def _sort_player_id(player_id: str) -> tuple[int, int | str]:
    return (0, int(player_id)) if player_id.isdigit() else (1, player_id)


def _load_list(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise RuntimeError(f"Expected list[dict] JSON: path={path}")
    return payload


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected object JSON: path={path}")
    return payload


def _unique_by_id(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    by_id: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in rows:
        player_id = _player_id(row)
        if not player_id:
            continue
        counts[player_id] += 1
        by_id[player_id] = row
    duplicates = sorted(
        (player_id for player_id, count in counts.items() if count > 1),
        key=_sort_player_id,
    )
    return by_id, duplicates


def _missing_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(not _has_text(row.get(field)) for row in rows)
        for field in AUDIT_FIELDS
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="監査済み入力から、ファイルを上書きせずplayers正本候補を生成する"
    )
    parser.add_argument("--live-snapshot", type=Path, required=True)
    parser.add_argument("--classification-report", type=Path, required=True)
    parser.add_argument("--profile-audit", type=Path, required=True)
    parser.add_argument("--local-input", type=Path, default=Path("scraper/data/players.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    live_rows = _load_list(args.live_snapshot)
    local_rows = _load_list(args.local_input)
    classification = _load_object(args.classification_report)
    profile_audit = _load_object(args.profile_audit)

    excluded_values = classification.get("excluded_player_ids")
    audited_players = profile_audit.get("players")
    if not isinstance(excluded_values, list):
        raise RuntimeError("classification report must contain excluded_player_ids list")
    if not isinstance(audited_players, list):
        raise RuntimeError("profile audit must contain players list")

    excluded_ids = {str(value).strip() for value in excluded_values if str(value).strip()}
    live_by_id, live_duplicates = _unique_by_id(live_rows)
    if live_duplicates:
        raise RuntimeError(f"duplicate player IDs in live snapshot: {live_duplicates}")
    unknown_excluded_ids = excluded_ids - set(live_by_id)
    if unknown_excluded_ids:
        raise RuntimeError(
            f"excluded player ID is not in live snapshot: "
            f"{sorted(unknown_excluded_ids, key=_sort_player_id)}"
        )
    if profile_audit.get("mode") != "audit" or profile_audit.get("applied_rows") != 0:
        raise RuntimeError("profile audit must be an unapplied audit report")
    audit_excluded_ids = {
        str(value).strip()
        for value in profile_audit.get("excluded_player_ids", [])
        if str(value).strip()
    }
    if audit_excluded_ids != excluded_ids:
        raise RuntimeError("classification and profile audit excluded_player_ids differ")
    if profile_audit.get("players_total") != len(live_rows):
        raise RuntimeError("profile audit players_total does not match live snapshot")

    patches: dict[str, dict[str, Any]] = {}
    for result in audited_players:
        if not isinstance(result, dict):
            continue
        player_id = _player_id(result)
        proposed = result.get("proposed_patch")
        if player_id and isinstance(proposed, dict) and proposed:
            unsupported_fields = set(proposed) - PATCHABLE_FIELDS
            if unsupported_fields:
                raise RuntimeError(
                    f"unsupported proposed patch fields: player_id={player_id} "
                    f"fields={sorted(unsupported_fields)}"
                )
            patches[player_id] = proposed

    candidate_rows = []
    for row in live_rows:
        player_id = _player_id(row)
        if not player_id or player_id in excluded_ids:
            continue
        # nationality はliveスキーマで廃止済み。古い入力に残っていても候補へ戻さない。
        candidate = {key: value for key, value in row.items() if key != "nationality"}
        candidate.update(patches.get(player_id, {}))
        candidate_rows.append(candidate)
    candidate_rows.sort(key=lambda row: _sort_player_id(_player_id(row)))

    candidate_by_id, candidate_duplicates = _unique_by_id(candidate_rows)
    local_by_id, local_duplicates = _unique_by_id(local_rows)
    if candidate_duplicates:
        raise RuntimeError(f"duplicate player IDs in candidate: {candidate_duplicates}")
    invalid_patch_ids = set(patches) - set(candidate_by_id)
    if invalid_patch_ids:
        raise RuntimeError(
            f"patch target is not eligible: {sorted(invalid_patch_ids, key=_sort_player_id)}"
        )

    candidate_ids = set(candidate_by_id)
    local_ids = set(local_by_id)
    field_differences: Counter[str] = Counter()
    for player_id in candidate_ids & local_ids:
        candidate = candidate_by_id[player_id]
        local = local_by_id[player_id]
        for field in sorted(set(candidate) | set(local)):
            if field == "nationality":
                continue
            if candidate.get(field) != local.get(field):
                field_differences[field] += 1

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "live_snapshot": str(args.live_snapshot),
            "classification_report": str(args.classification_report),
            "profile_audit": str(args.profile_audit),
            "local_input": str(args.local_input),
        },
        "policy": {
            "base": "live snapshot",
            "excluded": "classification report staff_like and placeholder IDs",
            "profile_changes": "profile audit proposed_patch only",
            "nationality": "removed; live schema retired this column",
            "timestamps": "kept from live snapshot; no live write was performed",
        },
        "summary": {
            "live_rows": len(live_rows),
            "excluded_player_ids": len(excluded_ids),
            "profile_patches": len(patches),
            "candidate_rows": len(candidate_rows),
            "candidate_unique_ids": len(candidate_ids),
            "candidate_duplicate_ids": len(candidate_duplicates),
            "local_rows": len(local_rows),
            "local_unique_ids": len(local_ids),
            "local_duplicate_ids": len(local_duplicates),
            "candidate_only_ids": len(candidate_ids - local_ids),
            "local_only_ids": len(local_ids - candidate_ids),
            "common_ids": len(candidate_ids & local_ids),
            "missing_candidate": _missing_counts(candidate_rows),
            "common_id_field_difference_counts": dict(sorted(field_differences.items())),
        },
        "excluded_player_ids": sorted(excluded_ids, key=_sort_player_id),
        "candidate_only_ids": sorted(candidate_ids - local_ids, key=_sort_player_id),
        "local_only_ids": sorted(local_ids - candidate_ids, key=_sort_player_id),
        "local_duplicate_ids": local_duplicates,
        "profile_patch_player_ids": sorted(patches, key=_sort_player_id),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(candidate_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"output={args.output}")
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
