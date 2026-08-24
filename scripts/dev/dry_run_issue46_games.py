"""Issue #46 の対象ゲームをシーズン単位でまとめて dry-run する CLI。"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / (
    'supabase/patches/20260824_issue46_missing_b1_games_manifest.csv'
)
DEFAULT_OUTPUT_DIR = Path('/tmp/issue46_dry_run_inputs')
HEADER_TEAM_ALIASES = {
    'A東京': 'アルバルク東京',
    '千葉': '千葉ジェッツ',
}


def _schedule_key(item: dict[str, Any]) -> int | None:
    value = item.get('schedule_key')
    if value is None and isinstance(item.get('game'), dict):
        value = item['game'].get('ScheduleKey')
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else REPO_ROOT / path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError(f'JSONを読み込めません: {path}: {exc}') from exc
    if not isinstance(payload, dict):
        raise ValueError(f'JSONのトップレベルがobjectではありません: {path}')
    if not isinstance(payload.get('games'), list):
        raise ValueError(f'games配列がありません: {path}')
    return payload


def _load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8', newline='') as file:
        rows = list(csv.DictReader(file))

    required = {
        'schedule_key',
        'season',
        'source_file',
        'source_tab',
        'home_team_id',
        'away_team_id',
        'summary_rows',
        'boxscore_rows',
        'detail_level',
    }
    actual = set(rows[0]) if rows else set()
    missing = sorted(required - actual)
    if missing:
        raise ValueError(f'マニフェストに必須列がありません: {missing}')
    if not rows:
        raise ValueError(f'マニフェストが空です: {path}')
    return rows


def _team_ids(item: dict[str, Any]) -> set[str]:
    game = item.get('game')
    if not isinstance(game, dict):
        return set()
    return {
        str(game[field])
        for field in ('HomeTeamID', 'AwayTeamID')
        if game.get(field) is not None
    }


def _select_games(
    manifest_rows: list[dict[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    source_cache: dict[Path, dict[str, Any]] = {}
    selected_by_season: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_schedule_keys: set[int] = set()

    for row in manifest_rows:
        try:
            schedule_key = int(row['schedule_key'])
            expected_summary_rows = int(row['summary_rows'])
            expected_boxscore_rows = int(row['boxscore_rows'])
        except ValueError as exc:
            raise ValueError(f'マニフェストの数値が不正です: {row}') from exc

        if schedule_key in seen_schedule_keys:
            raise ValueError(f'schedule_keyが重複しています: {schedule_key}')
        seen_schedule_keys.add(schedule_key)

        source_path = _resolve_repo_path(row['source_file'])
        if source_path not in source_cache:
            if not source_path.exists():
                raise FileNotFoundError(f'入力JSONがありません: {source_path}')
            source_cache[source_path] = _load_json(source_path)

        payload = source_cache[source_path]
        matches = [
            item
            for item in payload['games']
            if isinstance(item, dict) and _schedule_key(item) == schedule_key
        ]
        if len(matches) != 1:
            raise ValueError(
                f'schedule_key={schedule_key} のJSON内件数が想定外です: '
                f'{source_path} ({len(matches)}件)'
            )

        item = deepcopy(matches[0])
        if row['detail_level'] == 'header_only':
            game = item.setdefault('game', {})
            # ScheduleKey=1810の公式フォールバックヘッダにはTeamIDがない。
            # 候補CSVのホーム／アウェー順ではなく、ヘッダのチーム名順を正として
            # 確定済みのチームIDを変換時だけ補完する。
            candidate_by_name = {
                row['home_team_name_j']: row['home_team_id'],
                row['away_team_name_j']: row['away_team_id'],
            }
            home_name = HEADER_TEAM_ALIASES.get(
                str(game.get('HomeTeamNameJ')), str(game.get('HomeTeamNameJ'))
            )
            away_name = HEADER_TEAM_ALIASES.get(
                str(game.get('AwayTeamNameJ')), str(game.get('AwayTeamNameJ'))
            )
            if home_name not in candidate_by_name or away_name not in candidate_by_name:
                raise ValueError(
                    f'header_onlyのチーム名を候補IDへ解決できません: '
                    f'schedule_key={schedule_key}'
                )
            game['HomeTeamID'] = candidate_by_name[home_name]
            game['AwayTeamID'] = candidate_by_name[away_name]
            game['HomeTeamNameJ'] = home_name
            game['AwayTeamNameJ'] = away_name
        if len(item.get('summaries', [])) != expected_summary_rows:
            raise ValueError(
                f'schedule_key={schedule_key}: summaries件数が不一致です '
                f'({len(item.get("summaries", []))} != {expected_summary_rows})'
            )
        if len(item.get('boxscores', [])) != expected_boxscore_rows:
            raise ValueError(
                f'schedule_key={schedule_key}: boxscores件数が不一致です '
                f'({len(item.get("boxscores", []))} != {expected_boxscore_rows})'
            )

        if schedule_key != 1810:
            expected_team_ids = {row['home_team_id'], row['away_team_id']}
            if _team_ids(item) != expected_team_ids:
                raise ValueError(
                    f'schedule_key={schedule_key}: チームIDが不一致です '
                    f'({_team_ids(item)} != {expected_team_ids})'
                )

        selected_by_season[row['season']].append(item)

    return dict(selected_by_season)


def _season_sort_key(season: str) -> tuple[int, str]:
    try:
        return int(season.split('-', maxsplit=1)[0]), season
    except ValueError:
        return 9999, season


def _write_batch_inputs(
    selected_by_season: dict[str, list[dict[str, Any]]],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    for season in sorted(selected_by_season, key=_season_sort_key):
        items = selected_by_season[season]
        payload = {
            'season': season,
            'game_count': len(items),
            'games': items,
        }
        path = output_dir / f'issue46_games_{season}.json'
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        paths[season] = path

    return paths


def run(manifest_path: Path, output_dir: Path) -> None:
    manifest_rows = _load_manifest(manifest_path)
    selected_by_season = _select_games(manifest_rows)
    input_paths = _write_batch_inputs(selected_by_season, output_dir)

    total_games = sum(len(items) for items in selected_by_season.values())
    print(
        f'manifest={manifest_path} games={total_games} '
        f'season_batches={len(input_paths)} output_dir={output_dir}'
    )
    for season in sorted(input_paths, key=_season_sort_key):
        print(f'prepared season={season} input={input_paths[season]}')

    # run(dry_run=True) は player_id_map を取得せず、DBへ接続しない。
    from scripts.db.upsert_games import run as run_upsert_games

    for season in sorted(input_paths, key=_season_sort_key):
        print(f'=== dry-run season={season} ===')
        run_upsert_games(
            input_path=input_paths[season],
            dry_run=True,
            with_play_by_play=False,
        )

    print(
        f'ALL DRY-RUNS PASSED: games={total_games} '
        f'season_batches={len(input_paths)} play_by_play=0'
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Issue #46の対象ゲームをシーズン単位でまとめてdry-runする'
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f'対象マニフェスト（既定: {DEFAULT_MANIFEST})',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f'一括入力JSONの出力先（既定: {DEFAULT_OUTPUT_DIR})',
    )
    args = parser.parse_args()
    run(
        manifest_path=args.manifest,
        output_dir=args.output_dir,
    )


if __name__ == '__main__':
    main()
