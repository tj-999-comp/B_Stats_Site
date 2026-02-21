"""HTMLパーサー: スクレイピングしたHTMLからデータを抽出する"""

import requests
from bs4 import BeautifulSoup
from typing import Any
from .config import BASE_URL, HEADERS


def _fetch_html(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def parse_player_stats(season: str) -> list[dict[str, Any]]:
    """選手スタッツページを解析してリストで返す"""
    url = f"{BASE_URL}/stats/player?season={season}"
    soup = _fetch_html(url)
    # TODO: 実際のBリーグサイトの構造に合わせて実装
    return []


def parse_team_stats(season: str) -> list[dict[str, Any]]:
    """チームスタッツページを解析してリストで返す"""
    url = f"{BASE_URL}/stats/team?season={season}"
    soup = _fetch_html(url)
    # TODO: 実際のBリーグサイトの構造に合わせて実装
    return []


def parse_rankings(season: str) -> list[dict[str, Any]]:
    """順位表ページを解析してリストで返す"""
    url = f"{BASE_URL}/standings?season={season}"
    soup = _fetch_html(url)
    # TODO: 実際のBリーグサイトの構造に合わせて実装
    return []
