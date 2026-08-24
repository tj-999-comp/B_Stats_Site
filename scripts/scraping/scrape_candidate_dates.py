"""候補CSVに含まれる複数日付の試合詳細を一括取得するCLI。"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scripts.scraping.game_scraper import scrape_date_range_games


DEFAULT_INPUT = Path('scraper/data/game_supplement_candidates.csv')
DEFAULT_OUTPUT_DIR = Path('scraper/data/issue45_candidate_scrapes')
REQUIRED_COLUMNS = {
    'season',
    'date',
    'home_team_id',
    'home_team_name_j',
    'away_team_id',
    'away_team_name_j',
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _season_sort_key(season: str) -> int:
    try:
        return int(season.split('-', maxsplit=1)[0])
    except (IndexError, ValueError) as exc:
        raise ValueError(f'シーズン形式が不正です: {season}') from exc


def load_candidate_dates(input_path: Path) -> list[dict[str, Any]]:
    """候補CSVを読み込み、同一シーズン・日付ごとにまとめる。"""
    grouped: dict[tuple[str, date], list[dict[str, str]]] = {}

    with input_path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            missing_text = ', '.join(sorted(missing))
            raise ValueError(f'候補CSVに必須列がありません: {missing_text}')

        for row_number, row in enumerate(reader, start=2):
            season = (row.get('season') or '').strip()
            date_text = (row.get('date') or '').strip()
            if not season or not date_text:
                raise ValueError(f'候補CSV {row_number}行目のseason/dateが空です')

            try:
                target_date = date.fromisoformat(date_text)
            except ValueError as exc:
                raise ValueError(
                    f'候補CSV {row_number}行目の日付が不正です: {date_text}'
                ) from exc

            normalized_row = {
                key: (value or '').strip() for key, value in row.items()
            }
            grouped.setdefault((season, target_date), []).append(normalized_row)

    groups = [
        {
            'season': season,
            'date': target_date.isoformat(),
            'candidates': candidates,
        }
        for (season, target_date), candidates in grouped.items()
    ]
    groups.sort(
        key=lambda item: (
            _season_sort_key(str(item['season'])),
            str(item['date']),
        )
    )
    return groups


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _build_manifest(
    *,
    input_path: Path,
    groups: list[dict[str, Any]],
    include_play_by_play: bool,
    max_retries: int,
) -> dict[str, Any]:
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'candidate_input': str(input_path),
        'candidate_count': sum(len(group['candidates']) for group in groups),
        'unique_date_count': len(groups),
        'include_play_by_play': include_play_by_play,
        'max_retries': max_retries,
        'runs': [],
    }


def scrape_candidate_dates(
    *,
    input_path: Path,
    output_dir: Path,
    include_play_by_play: bool = False,
    max_retries: int = 3,
    overwrite: bool = False,
) -> dict[str, Any]:
    """候補CSVの全日付を取得し、日付別JSONとmanifestを保存する。"""
    if max_retries < 1:
        raise ValueError('max_retriesは1以上を指定してください')

    groups = load_candidate_dates(input_path)
    if not groups:
        raise ValueError('候補CSVにデータ行がありません')

    manifest_path = output_dir / 'manifest.json'
    output_paths = [
        output_dir / f"games_{group['season']}_{group['date']}.json"
        for group in groups
    ]
    if not overwrite:
        conflicts = [
            path for path in [manifest_path, *output_paths] if path.exists()
        ]
        if conflicts:
            conflict_text = '\n'.join(str(path) for path in conflicts)
            raise FileExistsError(
                '既存出力があります。内容を保持するため処理を中止します。\n'
                f'{conflict_text}\n'
                '--overwrite を指定すると上書きできます。'
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = _build_manifest(
        input_path=input_path,
        groups=groups,
        include_play_by_play=include_play_by_play,
        max_retries=max_retries,
    )
    _write_json(manifest_path, manifest)

    for index, group in enumerate(groups, start=1):
        season = str(group['season'])
        target_date = date.fromisoformat(str(group['date']))
        output_path = output_dir / f'games_{season}_{target_date.isoformat()}.json'
        logger.info(
            '[%d/%d] date=%s season=%s candidates=%d',
            index,
            len(groups),
            target_date,
            season,
            len(group['candidates']),
        )

        try:
            payload = scrape_date_range_games(
                target_date,
                target_date,
                season,
                include_play_by_play=include_play_by_play,
                max_retries=max_retries,
            )
            _write_json(output_path, payload)
            failed_keys = [
                int(key) for key in payload.get('failed_schedule_keys', [])
            ]
            run = {
                'status': 'completed',
                'season': season,
                'date': target_date.isoformat(),
                'candidate_count': len(group['candidates']),
                'game_count': payload.get('game_count', 0),
                'failed_schedule_keys': failed_keys,
                'output': str(output_path),
            }
        except Exception as exc:  # noqa: BLE001 - 1日失敗で全体を止めない
            logger.exception(
                '[%d/%d] date=%s season=%s failed',
                index,
                len(groups),
                target_date,
                season,
            )
            run = {
                'status': 'error',
                'season': season,
                'date': target_date.isoformat(),
                'candidate_count': len(group['candidates']),
                'error': str(exc),
            }

        run['candidates'] = group['candidates']
        manifest['runs'].append(run)
        _write_json(manifest_path, manifest)

    failed_schedule_keys = sorted(
        {
            key
            for run in manifest['runs']
            for key in run.get('failed_schedule_keys', [])
        }
    )
    error_runs = [
        run for run in manifest['runs'] if run.get('status') == 'error'
    ]
    manifest['failed_schedule_keys'] = failed_schedule_keys
    manifest['error_run_count'] = len(error_runs)
    manifest['completed_game_count'] = sum(
        int(run.get('game_count', 0))
        for run in manifest['runs']
        if run.get('status') == 'completed'
    )
    _write_json(manifest_path, manifest)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='候補CSVの複数日付を一括スクレイピングする'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=DEFAULT_INPUT,
        help=f'候補CSV (default: {DEFAULT_INPUT})',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f'日付別JSONとmanifestの出力先 (default: {DEFAULT_OUTPUT_DIR})',
    )
    parser.add_argument(
        '--include-play-by-play',
        action='store_true',
        help='play_by_playデータも取得する（デフォルト: 無効）',
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='game_detail取得時の最大リトライ回数 (default: 3)',
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='既存のmanifestと日付別JSONを上書きする',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='取得せず、候補件数と日付一覧だけ確認する',
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    groups = load_candidate_dates(args.input)
    candidate_count = sum(len(group['candidates']) for group in groups)
    logger.info(
        '候補試合=%d、ユニーク日付=%d', candidate_count, len(groups)
    )

    if args.dry_run:
        for index, group in enumerate(groups, start=1):
            logger.info(
                '[%d/%d] %s %s (%d試合)',
                index,
                len(groups),
                group['season'],
                group['date'],
                len(group['candidates']),
            )
        return

    manifest = scrape_candidate_dates(
        input_path=args.input,
        output_dir=args.output_dir,
        include_play_by_play=args.include_play_by_play,
        max_retries=args.max_retries,
        overwrite=args.overwrite,
    )
    logger.info(
        '完了: completed_games=%d failed_schedule_keys=%d error_runs=%d manifest=%s',
        manifest['completed_game_count'],
        len(manifest['failed_schedule_keys']),
        manifest['error_run_count'],
        args.output_dir / 'manifest.json',
    )

    if manifest['failed_schedule_keys'] or manifest['error_run_count']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
