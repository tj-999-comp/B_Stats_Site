"""メインスクレイパー: Bリーグの統計データを取得してDBに保存する"""

import logging
from .parser import parse_player_stats, parse_team_stats, parse_rankings
from .db import upsert_player_stats, upsert_team_stats, upsert_rankings
from .config import SEASONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_all(season: str) -> None:
    """指定シーズンの全データをスクレイピングしてDBに保存する"""
    logger.info(f"Scraping season: {season}")

    player_stats = parse_player_stats(season)
    logger.info(f"Scraped {len(player_stats)} player stats")
    upsert_player_stats(player_stats)

    team_stats = parse_team_stats(season)
    logger.info(f"Scraped {len(team_stats)} team stats")
    upsert_team_stats(team_stats)

    rankings = parse_rankings(season)
    logger.info(f"Scraped {len(rankings)} rankings")
    upsert_rankings(rankings)

    logger.info(f"Finished scraping season: {season}")


if __name__ == '__main__':
    for season in SEASONS:
        scrape_all(season)
