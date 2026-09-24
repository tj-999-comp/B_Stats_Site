"""JST基準で1日分の試合データを取得する日次バッチ。"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scripts.db.config import SEASONS
from scripts.scraping.game_scraper import output_path_for_date_range, save_date_range_games


JST = timezone(timedelta(hours=9))
logger = logging.getLogger(__name__)


def resolve_target_date(date_text: str | None) -> date:
    """Resolve the batch date in JST, or return today's JST date."""
    if date_text is not None:
        return date.fromisoformat(date_text)
    return datetime.now(JST).date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='JSTの日付を基準にBリーグの1日分の試合データを取得する'
    )
    parser.add_argument(
        '--date',
        metavar='YYYY-MM-DD',
        help='取得対象日。省略時は実行時のJST日付',
    )
    parser.add_argument(
        '--season',
        default=SEASONS[0],
        help=f'シーズン識別子（既定: {SEASONS[0]}）',
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        metavar='N',
        help='game_detail取得時の最大リトライ回数（既定: 3）',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='取得せず、JST日付・シーズン・保存先だけ確認する',
    )
    return parser


def run_batch(
    *,
    target_date: date,
    season: str,
    max_retries: int,
    dry_run: bool,
) -> int:
    output_path = output_path_for_date_range(season, target_date, target_date)
    summary = {
        'season': season,
        'target_date_jst': target_date.isoformat(),
        'output_path': str(output_path),
        'dry_run': dry_run,
        'include_play_by_play': False,
    }

    if dry_run:
        print(json.dumps(summary, ensure_ascii=False))
        return 0

    logger.info(
        'Starting daily batch: season=%s target_date_jst=%s output=%s',
        season,
        target_date,
        output_path,
    )
    saved_path = save_date_range_games(
        target_date,
        target_date,
        season,
        include_play_by_play=False,
        max_retries=max_retries,
    )
    payload = json.loads(Path(saved_path).read_text(encoding='utf-8'))
    failed_keys = payload.get('failed_schedule_keys', [])
    game_count = payload.get('game_count', 0)
    logger.info(
        'Daily batch completed: season=%s target_date_jst=%s games=%s failed_schedule_keys=%s output=%s',
        season,
        target_date,
        game_count,
        len(failed_keys) if isinstance(failed_keys, list) else 'unknown',
        saved_path,
    )
    if isinstance(failed_keys, list) and failed_keys:
        logger.error('Daily batch has failed schedule keys: %s', failed_keys)
        return 1
    return 0


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = build_parser().parse_args()
    if args.max_retries < 1:
        raise SystemExit('--max-retries は 1 以上を指定してください')

    try:
        target_date = resolve_target_date(args.date)
    except ValueError as exc:
        raise SystemExit(f'--date の形式が不正です: {exc}') from exc

    try:
        exit_code = run_batch(
            target_date=target_date,
            season=args.season,
            max_retries=args.max_retries,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    raise SystemExit(exit_code)


if __name__ == '__main__':
    main()
