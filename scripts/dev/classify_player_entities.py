"""tracked game JSONの根拠でlive playersを選手・スタッフ候補等に分類する。"""

from __future__ import annotations

import argparse
import glob
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.db.player_boxscore import (
    is_full_game_total_boxscore,
    is_player_total_boxscore,
)


AUDIT_FIELDS = (
    "player_name_e",
    "birthplace",
    "league_registered_nationality",
    "player_slot_category",
    "last_seen_team_id",
    "last_seen_jersey_number",
)
PLACEHOLDER_PLAYER_IDS = {"999999999"}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _player_id(row: dict[str, Any]) -> str:
    return str(row.get("player_id") or "").strip()


def _sort_player_id(value: str) -> tuple[int, int | str]:
    if value.isdigit():
        return 0, int(value)
    return 1, value


def load_players(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise RuntimeError(f"Expected list[dict] JSON: path={path}")
    return payload


def collect_game_observations(paths: list[Path]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    observations: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "accepted_rows": 0,
            "rejected_rows": 0,
            "names": Counter(),
            "team_ids": Counter(),
            "jersey_numbers": Counter(),
            "play_times": Counter(),
            "source_files": [],
        }
    )
    total_rows = 0
    accepted_rows = 0
    rejected_rows = 0

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        games = payload if isinstance(payload, list) else payload.get("games", [])
        for item in games:
            boxscores = item.get("home_boxscores", []) + item.get("away_boxscores", [])
            for boxscore in boxscores:
                if not is_full_game_total_boxscore(boxscore) or not _has_text(boxscore.get("PlayerID")):
                    continue
                player_id = str(boxscore.get("PlayerID")).strip()
                is_player = is_player_total_boxscore(boxscore)
                observation = observations[player_id]
                observation["accepted_rows" if is_player else "rejected_rows"] += 1
                observation["names"][str(boxscore.get("PlayerNameJ") or "").strip()] += 1
                observation["team_ids"][str(boxscore.get("TeamID") or "").strip()] += 1
                observation["jersey_numbers"][str(boxscore.get("PlayerNo") or "").strip()] += 1
                observation["play_times"][str(boxscore.get("PlayTime") or "").strip()] += 1
                if len(observation["source_files"]) < 3 and str(path) not in observation["source_files"]:
                    observation["source_files"].append(str(path))
                total_rows += 1
                accepted_rows += int(is_player)
                rejected_rows += int(not is_player)

    return dict(observations), {
        "game_files": len(paths),
        "full_game_total_rows": total_rows,
        "accepted_player_rows": accepted_rows,
        "rejected_staff_like_rows": rejected_rows,
        "observed_player_ids": len(observations),
    }


def _top_values(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def _classification(player_id: str, observation: dict[str, Any] | None) -> str:
    if player_id in PLACEHOLDER_PLAYER_IDS:
        return "placeholder"
    if observation is None:
        return "unseen_in_tracked_games"
    if observation["accepted_rows"] > 0:
        return "player"
    if observation["rejected_rows"] > 0:
        return "staff_like"
    return "unresolved"


def _entity_type(classification: str) -> str:
    """分類レポートとplayers.entity_typeで共有する正規化された分類値。"""
    return {
        "staff_like": "staff",
        "unseen_in_tracked_games": "unresolved",
    }.get(classification, classification)


def build_report(
    live_players: list[dict[str, Any]],
    local_players: list[dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    scan_summary: dict[str, int],
    *,
    games_glob: str,
    live_snapshot: Path,
    local_input: Path,
) -> dict[str, Any]:
    live_by_id = {_player_id(row): row for row in live_players if _player_id(row)}
    local_ids = {_player_id(row) for row in local_players if _player_id(row)}
    entities = []

    for player_id in sorted(live_by_id, key=_sort_player_id):
        player = live_by_id[player_id]
        observation = observations.get(player_id)
        classification = _classification(player_id, observation)
        evidence = None
        if observation is not None:
            evidence = {
                "accepted_rows": observation["accepted_rows"],
                "rejected_rows": observation["rejected_rows"],
                "names": _top_values(observation["names"]),
                "team_ids": _top_values(observation["team_ids"]),
                "jersey_numbers": _top_values(observation["jersey_numbers"]),
                "play_times": _top_values(observation["play_times"]),
                "source_files": observation["source_files"],
            }
        entities.append(
            {
                "player_id": player_id,
                "player_name_j": player.get("player_name_j"),
                "classification": classification,
                "entity_type": _entity_type(classification),
                "in_local_canonical": player_id in local_ids,
                "missing_fields": [field for field in AUDIT_FIELDS if not _has_text(player.get(field))],
                "evidence": evidence,
            }
        )

    classification_counts = Counter(entity["classification"] for entity in entities)
    excluded_ids = sorted(
        {
            entity["player_id"]
            for entity in entities
            if entity["classification"] in {"staff_like", "placeholder"}
        },
        key=_sort_player_id,
    )
    excluded_set = set(excluded_ids)
    eligible_players = [row for row in live_players if _player_id(row) not in excluded_set]
    excluded_players = [row for row in live_players if _player_id(row) in excluded_set]

    missing = lambda rows: {
        field: sum(not _has_text(row.get(field)) for row in rows)
        for field in AUDIT_FIELDS
    }
    mixed_observation_ids = sorted(
        [
            player_id
            for player_id, observation in observations.items()
            if observation["accepted_rows"] > 0 and observation["rejected_rows"] > 0
        ],
        key=_sort_player_id,
    )

    return {
        "generated_at": _now_utc_iso(),
        "games_glob": games_glob,
        "live_snapshot": str(live_snapshot),
        "local_input": str(local_input),
        "summary": {
            **scan_summary,
            "live_player_ids": len(live_by_id),
            "local_unique_player_ids": len(local_ids),
            "classification_counts": dict(sorted(classification_counts.items())),
            "excluded_player_ids": len(excluded_ids),
            "eligible_player_ids": len(eligible_players),
            "mixed_accepted_and_rejected_ids": len(mixed_observation_ids),
            "missing_before_exclusion": missing(live_players),
            "missing_after_exclusion": missing(eligible_players),
            "excluded_rows_missing": missing(excluded_players),
        },
        "classification_rules": {
            "player": "at least one PeriodCategory=18 row has jersey number, playing flag, starting flag, or positive play time",
            "staff_like": "all observed PeriodCategory=18 rows have blank jersey, false playing/starting flags, and no positive play time",
            "placeholder": f"player_id is one of {sorted(PLACEHOLDER_PLAYER_IDS)}",
            "unseen_in_tracked_games": "no PeriodCategory=18 row exists in the selected tracked game JSON files",
        },
        "entity_type_values": ["player", "staff", "placeholder", "unresolved"],
        "excluded_player_ids": excluded_ids,
        "mixed_observation_ids": mixed_observation_ids,
        "entities": entities,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="tracked game JSONの根拠でlive playersを選手・スタッフ候補等に分類する"
    )
    parser.add_argument("--games-glob", default="scraper/data/season_*/games_*.json")
    parser.add_argument("--live-snapshot", type=Path, required=True)
    parser.add_argument("--local-input", type=Path, default=Path("scraper/data/players.json"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("/tmp/b_stats_player_entity_classification.json"),
    )
    args = parser.parse_args()

    game_paths = [Path(value) for value in sorted(glob.glob(args.games_glob))]
    if not game_paths:
        raise RuntimeError(f"No game files matched: {args.games_glob}")

    observations, scan_summary = collect_game_observations(game_paths)
    live_players = load_players(args.live_snapshot)
    local_players = load_players(args.local_input)
    report = build_report(
        live_players,
        local_players,
        observations,
        scan_summary,
        games_glob=args.games_glob,
        live_snapshot=args.live_snapshot,
        local_input=args.local_input,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
