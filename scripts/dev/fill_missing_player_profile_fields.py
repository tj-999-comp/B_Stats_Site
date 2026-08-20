"""players の欠損プロフィールを監査し、差分だけを補完する。"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.db.db import fetch_all_players, get_client
from scripts.dev.enrich_players_profile import infer_player_slot_category
from scripts.dev.fetch_profile_fields_parallel import fetch_profile


AUDIT_FIELDS = (
    "player_name_e",
    "birthplace",
    "league_registered_nationality",
    "player_slot_category",
    "last_seen_team_id",
    "last_seen_jersey_number",
)
PATCHABLE_FIELDS = (
    "league_registered_nationality",
    "birthplace",
    "player_slot_category",
)


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def count_missing(players: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(not _has_text(player.get(field)) for player in players)
        for field in AUDIT_FIELDS
    }


def load_excluded_player_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("excluded_player_ids") if isinstance(payload, dict) else None
    if not isinstance(values, list):
        raise RuntimeError(f"Expected excluded_player_ids list: path={path}")
    return {str(value).strip() for value in values if str(value).strip()}


def load_entity_types(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    entities = payload.get("entities") if isinstance(payload, dict) else None
    if not isinstance(entities, list):
        raise RuntimeError(f"Expected entities list in classification report: path={path}")

    result: dict[str, str] = {}
    allowed = {"player", "staff", "placeholder", "unresolved"}
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        player_id = str(entity.get("player_id") or "").strip()
        entity_type = str(entity.get("entity_type") or entity.get("classification") or "").strip()
        # 旧レポートも再利用できるよう、旧分類名を現行値へ読み替える。
        entity_type = {
            "staff_like": "staff",
            "unseen_in_tracked_games": "unresolved",
        }.get(entity_type, entity_type)
        if not player_id or entity_type not in allowed:
            raise RuntimeError(
                f"Invalid entity classification: player_id={player_id!r} entity_type={entity_type!r}"
            )
        result[player_id] = entity_type
    return result


def load_players_snapshot(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise RuntimeError(f"Expected list[dict] JSON: path={path}")
    return payload


def load_fetch_cache(path: Path | None) -> dict[str, tuple[str | None, str | None, str]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("players") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError(f"Expected players list in fetch cache: path={path}")

    cache: dict[str, tuple[str | None, str | None, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        player_id = str(row.get("player_id") or "").strip()
        fetch_status = row.get("fetch_status")
        fetched = row.get("fetched")
        if not player_id or not isinstance(fetch_status, str) or not isinstance(fetched, dict):
            continue
        cache[player_id] = (
            fetched.get("league_registered_nationality"),
            fetched.get("birthplace"),
            fetch_status,
        )
    return cache


def build_targets(players: list[dict[str, Any]], force: bool) -> list[dict[str, Any]]:
    """公式プロフィールの取得または既存値からの区分導出が必要な行を返す。"""
    if force:
        return [player for player in players if _has_text(player.get("player_id"))]
    return [
        player
        for player in players
        if _has_text(player.get("player_id"))
        and any(not _has_text(player.get(field)) for field in PATCHABLE_FIELDS)
    ]


def _profile_patch(
    player: dict[str, Any],
    *,
    fetched_league: str | None,
    fetched_birthplace: str | None,
) -> dict[str, Any]:
    """既存値を上書きせず、実値を得られた欠損列だけを返す。"""
    patch: dict[str, Any] = {}

    if not _has_text(player.get("league_registered_nationality")) and _has_text(fetched_league):
        patch["league_registered_nationality"] = str(fetched_league).strip()
    if not _has_text(player.get("birthplace")) and _has_text(fetched_birthplace):
        patch["birthplace"] = str(fetched_birthplace).strip()

    combined_league = patch.get(
        "league_registered_nationality",
        player.get("league_registered_nationality"),
    )
    combined_birthplace = patch.get("birthplace", player.get("birthplace"))
    slot = infer_player_slot_category(combined_league, combined_birthplace)
    if not _has_text(player.get("player_slot_category")) and _has_text(slot):
        patch["player_slot_category"] = slot

    return patch


def _result_status(
    fetch_status: str | None,
    fetched_values: dict[str, Any],
    patch: dict[str, Any],
    missing_before: list[str],
) -> str:
    if fetch_status is None:
        return "derived_from_existing_profile" if patch else "no_derivable_change"
    if fetch_status == "404":
        return "not_found"
    if fetch_status != "ok":
        return "fetch_error"
    official_blanks = [
        field
        for field in ("league_registered_nationality", "birthplace")
        if field in missing_before and not _has_text(fetched_values.get(field))
    ]
    if patch and official_blanks:
        return "ok_with_partial_patch"
    if patch:
        return "ok_with_patch"
    if official_blanks:
        return "official_fields_blank"
    return "ok_no_change"


def inspect_player(
    player: dict[str, Any],
    *,
    timeout: int,
    fetch_cache: dict[str, tuple[str | None, str | None, str]] | None = None,
) -> dict[str, Any]:
    player_id = str(player.get("player_id") or "").strip()
    needs_fetch = (
        not _has_text(player.get("league_registered_nationality"))
        or not _has_text(player.get("birthplace"))
    )

    fetch_status: str | None = None
    fetched_league: str | None = None
    fetched_birthplace: str | None = None
    fetch_source = "not_needed"
    if needs_fetch:
        cached = (fetch_cache or {}).get(player_id)
        if cached is not None:
            fetched_league, fetched_birthplace, fetch_status = cached
            fetch_source = "cache"
        else:
            _, fetched_league, fetched_birthplace, fetch_status = fetch_profile(player_id, timeout)
            fetch_source = "official"

    fetched_values = {
        "league_registered_nationality": fetched_league,
        "birthplace": fetched_birthplace,
    }
    patch = _profile_patch(
        player,
        fetched_league=fetched_league,
        fetched_birthplace=fetched_birthplace,
    )

    missing_before = [field for field in AUDIT_FIELDS if not _has_text(player.get(field))]
    unresolved_after = [
        field
        for field in PATCHABLE_FIELDS
        if not _has_text(patch.get(field, player.get(field)))
    ]
    return {
        "player_id": player_id,
        "player_name_j": player.get("player_name_j"),
        "expected_updated_at": player.get("updated_at"),
        "existing": {
            field: player.get(field)
            for field in PATCHABLE_FIELDS
        },
        "fetch_status": fetch_status,
        "fetch_source": fetch_source,
        "status": _result_status(fetch_status, fetched_values, patch, missing_before),
        "missing_before": missing_before,
        "unresolved_patchable_after_proposed": unresolved_after,
        "fetched": fetched_values,
        "proposed_patch": patch,
        "applied": False,
        "apply_error": None,
    }


def _apply_updates(results: list[dict[str, Any]]) -> int:
    client = get_client()
    applied = 0

    for result in results:
        proposed = result["proposed_patch"]
        if not proposed:
            continue
        if not _has_text(result.get("expected_updated_at")):
            result["apply_error"] = "missing expected_updated_at; update skipped"
            continue
        patch = {**proposed, "updated_at": _now_utc_iso()}
        try:
            query = (
                client.table("players")
                .update(patch)
                .eq("player_id", result["player_id"])
            )
            query = query.eq("updated_at", result["expected_updated_at"])
            response = query.execute()
            if response.data == []:
                raise RuntimeError("row changed after audit or no longer exists")
            result["applied"] = True
            applied += 1
        except Exception as exc:  # 部分反映時もレポートに完全な履歴を残す
            result["apply_error"] = f"{type(exc).__name__}: {exc}"

    return applied


def _project_missing_after(
    players: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, int]:
    patches = {
        str(result["player_id"]): result["proposed_patch"]
        for result in results
        if result["proposed_patch"]
    }
    projected = [
        {**player, **patches.get(str(player.get("player_id") or ""), {})}
        for player in players
    ]
    return count_missing(projected)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="players の欠損プロフィールを監査し、差分だけを補完する"
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="欠損有無に関係なく全選手を監査する")
    parser.add_argument(
        "--players-input",
        type=Path,
        default=None,
        help="監査済みliveスナップショット。省略時はlive DBから全件取得する",
    )
    parser.add_argument(
        "--classification-report",
        type=Path,
        default=None,
        help="classify_player_entities.pyのレポート。staff / placeholderを対象外にする",
    )
    parser.add_argument(
        "--fetch-cache",
        type=Path,
        default=None,
        help="過去のfill_missing_player_profile_fieldsレポートの取得結果を再利用する",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="提案差分をlive DBへ反映する（指定なしは監査のみ）",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="後方互換用。現在は指定なしでもDBを更新しない",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("/tmp/b_stats_fill_missing_player_profile_fields_report.json"),
        help="選手別監査レポート出力先",
    )
    args = parser.parse_args()

    if args.apply and args.classification_report is None:
        raise RuntimeError("--apply requires --classification-report")

    all_players = (
        load_players_snapshot(args.players_input)
        if args.players_input is not None
        else fetch_all_players()
    )
    excluded_player_ids = load_excluded_player_ids(args.classification_report)
    entity_types = load_entity_types(args.classification_report)
    all_player_ids = {
        str(player.get("player_id") or "").strip()
        for player in all_players
        if str(player.get("player_id") or "").strip()
    }
    unknown_excluded_ids = excluded_player_ids - all_player_ids
    if unknown_excluded_ids:
        raise RuntimeError(
            f"classification report contains IDs not present in players source: "
            f"{sorted(unknown_excluded_ids)}"
        )
    unknown_entity_ids = set(entity_types) - all_player_ids
    if unknown_entity_ids:
        raise RuntimeError(
            f"classification report contains entity IDs not present in players source: "
            f"{sorted(unknown_entity_ids)}"
        )
    if entity_types:
        excluded_player_ids = {
            player_id
            for player_id, entity_type in entity_types.items()
            if entity_type in {"staff", "placeholder"}
        }
    fetch_cache = load_fetch_cache(args.fetch_cache)
    eligible_players = [
        player
        for player in all_players
        if str(player.get("player_id") or "").strip() not in excluded_player_ids
    ]
    targets = build_targets(eligible_players, args.force)
    if args.limit is not None:
        targets = targets[: args.limit]

    print(f"players_total={len(all_players)}")
    print(f"eligible_players={len(eligible_players)} excluded_players={len(excluded_player_ids)}")
    print(f"targets={len(targets)}")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                inspect_player,
                player,
                timeout=args.timeout,
                fetch_cache=fetch_cache,
            ): player
            for player in targets
        }
        for index, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if index % 100 == 0:
                print(f"progress={index}/{len(futures)}")

    results.sort(key=lambda item: str(item["player_id"]))
    applied_rows = _apply_updates(results) if args.apply else 0
    status_counts = Counter(result["status"] for result in results)
    proposed_rows = sum(bool(result["proposed_patch"]) for result in results)
    apply_errors = sum(bool(result["apply_error"]) for result in results)

    report = {
        "generated_at": _now_utc_iso(),
        "mode": "apply" if args.apply else "audit",
        "players_source": str(args.players_input) if args.players_input else "live_db",
        "fetch_cache": str(args.fetch_cache) if args.fetch_cache else None,
        "players_total": len(all_players),
        "eligible_players": len(eligible_players),
        "excluded_player_ids": sorted(excluded_player_ids),
        "excluded_entity_types": ["staff", "placeholder"],
        "entity_type_counts": dict(
            sorted(Counter(entity_types.values()).items())
        ) if entity_types else None,
        "targets": len(targets),
        "status_counts": dict(sorted(status_counts.items())),
        "proposed_rows": proposed_rows,
        "applied_rows": applied_rows,
        "apply_errors": apply_errors,
        "missing_before_all": count_missing(all_players),
        "missing_before_eligible": count_missing(eligible_players),
        "missing_after_proposed_eligible": _project_missing_after(eligible_players, results),
        "players": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("done")
    print(json.dumps({key: value for key, value in report.items() if key != "players"}, ensure_ascii=False))
    print(f"report={args.report}")

    if apply_errors:
        raise RuntimeError(f"DB update failed for {apply_errors} rows; inspect report={args.report}")


if __name__ == "__main__":
    main()
