"""メインスクレイパー: Bリーグの統計データを取得してDBに保存する"""

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from scripts.db.config import SEASONS
from scripts.scraping.game_scraper import (
    load_latest_failed_schedule_keys,
    retry_failed_games_into_json,
    save_date_range_games,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def main() -> None:
    parser = argparse.ArgumentParser(
        description='BリーグスタッツデータをスクレイピングしてJSONに保存する'
    )
    parser.add_argument(
        '--date',
        type=str,
        metavar='YYYY-MM-DD',
        help='スクレイピングする日付（例: 2024-10-05）',
    )
    parser.add_argument(
        '--start-date',
        type=str,
        metavar='YYYY-MM-DD',
        help='スクレイピング開始日（例: 2024-10-05）。--end-date と併用',
    )
    parser.add_argument(
        '--end-date',
        type=str,
        metavar='YYYY-MM-DD',
        help='スクレイピング終了日（例: 2024-10-11）。--start-date と併用',
    )
    parser.add_argument(
        '--season',
        type=str,
        metavar='SEASON',
        help='シーズン識別子（例: 2024-25）。省略時は config.py の SEASONS[0] を使用',
    )
    parser.add_argument(
        '--include-play-by-play',
        action='store_true',
        help='play_by_play データも取得する（デフォルト: 無効）',
    )
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='失敗した schedule_key のみ再取得して既存JSONへマージする',
    )
    parser.add_argument(
        '--merge-into',
        type=str,
        metavar='PATH',
        help='再取得結果をねじ込む先のJSONファイルパス（--retry-failed で必須）',
    )
    parser.add_argument(
        '--failed-keys',
        type=str,
        metavar='K1,K2,...',
        help='再取得対象 schedule_key を手動指定（省略時はログから自動取得）',
    )
    args = parser.parse_args()

    include_pbp: bool = args.include_play_by_play
    season = args.season or SEASONS[0]

    if args.retry_failed:
        if not args.merge_into:
            parser.error('--retry-failed では --merge-into を指定してください')

        target = Path(args.merge_into)
        if not target.exists():
            parser.error(f'--merge-into のファイルが存在しません: {target}')

        payload = json.loads(target.read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            parser.error('--merge-into の JSON 形式が不正です')

        payload_season = str(payload.get('season') or season)
        payload_start = date.fromisoformat(str(payload.get('start_date')))
        payload_end = date.fromisoformat(str(payload.get('end_date')))

        if args.failed_keys:
            failed_keys: list[int] = []
            for token in args.failed_keys.split(','):
                token = token.strip()
                if not token:
                    continue
                failed_keys.append(int(token))
        else:
            failed_keys = load_latest_failed_schedule_keys(
                season=payload_season,
                start_date=payload_start,
                end_date=payload_end,
            )
            if not failed_keys:
                fallback = payload.get('failed_schedule_keys', [])
                if isinstance(fallback, list):
                    failed_keys = [int(k) for k in fallback]

        if not failed_keys:
            logger.info('再取得対象の failed_schedule_keys が見つからなかったため終了します')
            return

        logger.info(
            'Retry failed schedule_keys=%s into %s (%s ~ %s, season=%s)',
            len(failed_keys),
            target,
            payload_start,
            payload_end,
            payload_season,
        )
        result = retry_failed_games_into_json(
            target_json_path=target,
            failed_schedule_keys=failed_keys,
            include_play_by_play=include_pbp,
        )
        logger.info(
            'Merged retry result: retried=%s failed_after=%s target=%s',
            result['retried_count'],
            result['failed_after_count'],
            result['target_json'],
        )
        return

    if args.date:
        target = date.fromisoformat(args.date)
        logger.info(f'Scraping date={target} season={season}')
        output_path = save_date_range_games(target, target, season, include_play_by_play=include_pbp)
        logger.info(f'Saved: {output_path}')

    elif args.start_date and args.end_date:
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
        if start > end:
            parser.error('--start-date は --end-date 以前の日付を指定してください')
        logger.info(f'Scraping {start} ~ {end} season={season}')
        output_path = save_date_range_games(start, end, season, include_play_by_play=include_pbp)
        logger.info(f'Saved: {output_path}')

    elif args.start_date or args.end_date:
        parser.error('--start-date と --end-date は両方指定してください')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
