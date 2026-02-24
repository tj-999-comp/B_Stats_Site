"""メインスクレイパー: Bリーグの統計データを取得してDBに保存する"""

import logging
from .config import SEASONS
from .game_scraper import save_opening_week_games

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_all(season: str) -> None:
    """指定シーズンの開幕1週間分の試合単位データをスクレイピングして保存する"""
    logger.info(f'Scraping opening week game data (without play_by_play): {season}')
    output_path = save_opening_week_games(season, include_play_by_play=False)
    logger.info(f'Saved opening week game data: {output_path}')
    logger.info(f'Finished scraping season: {season}')


if __name__ == '__main__':
    for season in SEASONS:
        scrape_all(season)
