"""メインスクレイパー: Bリーグの統計データを取得してDBに保存する"""

import argparse
import logging
from datetime import date

from .config import SEASONS
from .game_scraper import save_date_range_games

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
    args = parser.parse_args()

    include_pbp: bool = args.include_play_by_play
    season = args.season or SEASONS[0]

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
