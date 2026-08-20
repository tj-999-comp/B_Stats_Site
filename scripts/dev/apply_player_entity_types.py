"""分類レポートのentity_typeをplayersへ反映する。既定では監査のみ行う。"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.db.db import fetch_all_players, get_client


ENTITY_TYPES = {"player", "staff", "placeholder", "unresolved"}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_entity_types(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(
            f"Classification report does not exist: {path}. "
            "Run audit_players_snapshot.py and classify_player_entities.py first."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    entities = payload.get("entities") if isinstance(payload, dict) else None
    if not isinstance(entities, list):
        raise RuntimeError(f"Expected entities list in classification report: path={path}")

    result: dict[str, str] = {}
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        player_id = str(entity.get("player_id") or "").strip()
        entity_type = str(entity.get("entity_type") or "").strip()
        if not player_id or entity_type not in ENTITY_TYPES:
            raise RuntimeError(
                f"Invalid entity classification: player_id={player_id!r} "
                f"entity_type={entity_type!r}"
            )
        if player_id in result:
            raise RuntimeError(f"Duplicate player_id in classification report: {player_id}")
        result[player_id] = entity_type
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="分類レポートのentity_typeをplayersへ反映する（既定は監査のみ）"
    )
    parser.add_argument("--classification-report", type=Path, required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="差分をlive DBへ反映する。事前にバックアップと件数確認を行う",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("/tmp/b_stats_apply_player_entity_types_report.json"),
    )
    args = parser.parse_args()

    desired = load_entity_types(args.classification_report)
    client = get_client()
    try:
        client.table("players").select("player_id,entity_type").limit(1).execute()
    except Exception as exc:
        raise RuntimeError(
            "players.entity_type is not readable. Apply the rebuild SQL before this command."
        ) from exc

    current_rows = fetch_all_players()
    current = {
        str(row.get("player_id") or "").strip(): row.get("entity_type") or "player"
        for row in current_rows
        if str(row.get("player_id") or "").strip()
    }
    unknown_ids = set(desired) - set(current)
    if unknown_ids:
        raise RuntimeError(f"classification report contains unknown player IDs: {sorted(unknown_ids)}")

    changes = [
        {"player_id": player_id, "from": current[player_id], "to": entity_type}
        for player_id, entity_type in sorted(desired.items())
        if current[player_id] != entity_type
    ]
    applied = 0
    errors: list[dict[str, str]] = []
    if args.apply:
        for change in changes:
            try:
                response = (
                    client.table("players")
                    .update({"entity_type": change["to"], "updated_at": _now_utc_iso()})
                    .eq("player_id", change["player_id"])
                    .execute()
                )
                if response.data == []:
                    raise RuntimeError("row not found or update returned no row")
                applied += 1
            except Exception as exc:  # 部分反映時も対象とエラーをレポートに残す
                errors.append({"player_id": change["player_id"], "error": f"{type(exc).__name__}: {exc}"})

    report: dict[str, Any] = {
        "generated_at": _now_utc_iso(),
        "mode": "apply" if args.apply else "audit",
        "classification_report": str(args.classification_report),
        "players_total": len(current),
        "classification_counts": dict(sorted(Counter(desired.values()).items())),
        "changes": changes,
        "planned_rows": len(changes),
        "applied_rows": applied,
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "changes"}, ensure_ascii=False))
    print(f"report={args.report}")
    if errors:
        raise RuntimeError(f"DB update failed for {len(errors)} rows; inspect report={args.report}")


if __name__ == "__main__":
    main()
