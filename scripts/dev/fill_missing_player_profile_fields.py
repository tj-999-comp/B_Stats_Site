"""players テーブルの league_registered_nationality / birthplace 欠損を差分補完する。"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.db.db import fetch_all_players, get_client
    from scripts.dev.fetch_profile_fields_parallel import fetch_profile
except ModuleNotFoundError:
    # python scripts/dev/... での直接実行時はプロジェクトルートを import path に追加する
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from scripts.db.db import fetch_all_players, get_client
    from scripts.dev.fetch_profile_fields_parallel import fetch_profile


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_targets(players: list[dict[str, Any]], force: bool) -> list[dict[str, Any]]:
    if force:
        return [p for p in players if _has_text(p.get("player_id"))]
    return [
        p
        for p in players
        if _has_text(p.get("player_id"))
        and (
            not _has_text(p.get("league_registered_nationality"))
            or not _has_text(p.get("birthplace"))
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="players テーブルの欠損プロフィール項目を差分補完")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="欠損有無に関係なく全選手を対象にする")
    parser.add_argument("--dry-run", action="store_true", help="DB更新せず件数のみ確認する")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("scraper/logs/fill_missing_player_profile_fields_report.json"),
        help="実行レポート出力先",
    )
    args = parser.parse_args()

    all_players = fetch_all_players()
    targets = build_targets(all_players, args.force)
    if args.limit is not None:
        targets = targets[: args.limit]

    print(f"players_total={len(all_players)}")
    print(f"targets={len(targets)}")

    if not targets:
        print("no targets")
        return

    futures = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for player in targets:
            player_id = str(player.get("player_id")).strip()
            futures[executor.submit(fetch_profile, player_id, args.timeout)] = player

        updates: list[dict[str, Any]] = []
        statuses: dict[str, int] = {"ok": 0, "404": 0, "error": 0}
        touched_rows = 0
        touched_league = 0
        touched_birthplace = 0

        for i, future in enumerate(as_completed(futures), start=1):
            original = futures[future]
            player_id, league_nationality, birthplace, status = future.result()

            if status == "ok":
                statuses["ok"] += 1
            elif status == "404":
                statuses["404"] += 1
            else:
                statuses["error"] += 1

            patch: dict[str, Any] = {"player_id": player_id}

            if not _has_text(original.get("league_registered_nationality")) and _has_text(league_nationality):
                patch["league_registered_nationality"] = league_nationality
                touched_league += 1

            if not _has_text(original.get("birthplace")) and _has_text(birthplace):
                patch["birthplace"] = birthplace
                touched_birthplace += 1

            if len(patch) > 1:
                patch["updated_at"] = _now_utc_iso()
                updates.append(patch)
                touched_rows += 1

            if i % 100 == 0:
                print(f"progress={i}/{len(futures)} updates={touched_rows}")

    report = {
        "players_total": len(all_players),
        "targets": len(targets),
        "status_ok": statuses["ok"],
        "status_404": statuses["404"],
        "status_error": statuses["error"],
        "updated_rows": touched_rows,
        "updated_league_registered_nationality": touched_league,
        "updated_birthplace": touched_birthplace,
        "dry_run": args.dry_run,
    }

    if not args.dry_run and updates:
        client = get_client()
        for patch in updates:
            player_id = patch.pop("player_id")
            client.table("players").update(patch).eq("player_id", player_id).execute()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("done")
    print(json.dumps(report, ensure_ascii=False))
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
