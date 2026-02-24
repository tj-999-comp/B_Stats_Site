"""HTMLパーサー: スクレイピングしたHTMLからデータを抽出する"""

import re
from typing import Any

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from .config import BASE_URL, HEADERS


def _fetch_html(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def _to_text(value: str) -> str:
    return ' '.join(value.replace('\u3000', ' ').split())


def _to_int(value: str) -> int:
    cleaned = value.replace(',', '').strip()
    if not cleaned:
        return 0
    return int(float(cleaned))


def _to_float(value: str) -> float:
    cleaned = value.replace('%', '').replace(',', '').strip()
    if not cleaned:
        return 0.0
    return float(cleaned)


def _split_team_name(cell: str) -> str:
    text = _to_text(cell)
    parts = text.split(maxsplit=1)
    if len(parts) == 2:
        return parts[1]
    return text


def _extract_table_rows(table: Tag) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in table.find_all('tr'):
        cells = tr.find_all('td')
        if not cells:
            continue
        row = [_to_text(td.get_text(' ', strip=True)) for td in cells]
        rows.append(row)
    return rows


def _find_player_table_rows(soup: BeautifulSoup) -> list[list[str]]:
    candidates: list[list[list[str]]] = []
    for table in soup.find_all('table'):
        rows = _extract_table_rows(table)
        if not rows:
            continue
        if any(len(row) >= 24 and row[0].isdigit() for row in rows):
            candidates.append(rows)

    if not candidates:
        return []

    return max(candidates, key=len)


def _season_to_year(season: str) -> str:
    if '-' in season:
        right = season.split('-')[-1]
        if len(right) == 2:
            return f'20{right}'
    return season[:4]


def _fetch_player_rows_from_json_api(season: str) -> list[list[str]]:
    year = _season_to_year(season)
    url = f'{BASE_URL}/stats/player'

    headers = {
        **HEADERS,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE_URL}/stats/player?season={season}',
    }

    rows: list[list[str]] = []
    index = '0'

    while True:
        params = {
            'data_format': 'json',
            'year': year,
            'tab': '1',
            'target': 'player-b1',
            'value': 'AveragePoints',
            'o': 'desc',
            'e': '2',
            'index': index,
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code >= 500:
            break
        response.raise_for_status()
        payload = response.json()

        topics = payload.get('topics', [])
        if not topics:
            break

        for row_html in topics:
            row_soup = BeautifulSoup(row_html, 'html.parser')
            tr = row_soup.find('tr')
            if not tr:
                continue
            cells = [_to_text(td.get_text(' ', strip=True)) for td in tr.find_all('td')]
            if cells:
                rows.append(cells)

        next_index = payload.get('index')
        if not next_index:
            break
        index = str(next_index)

    return rows


def _extract_standings_sections(soup: BeautifulSoup) -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    for heading in soup.find_all(re.compile('^h[1-6]$')):
        title = _to_text(heading.get_text(' ', strip=True))
        if title not in {'東地区', '西地区', 'ワイルドカード'}:
            continue

        table = heading.find_next('table')
        if not table:
            continue
        rows = _extract_table_rows(table)
        if rows:
            sections[title] = rows
    return sections


def extract_player_raw_rows(season: str) -> list[list[str]]:
    rows = _fetch_player_rows_from_json_api(season)
    if rows:
        return rows

    url = f"{BASE_URL}/stats/player?season={season}"
    soup = _fetch_html(url)
    return _find_player_table_rows(soup)


def extract_standings_raw_rows() -> dict[str, list[list[str]]]:
    url = f"{BASE_URL}/standings/"
    soup = _fetch_html(url)
    return _extract_standings_sections(soup)


def parse_player_stats(season: str) -> list[dict[str, Any]]:
    """選手スタッツページを解析してリストで返す"""
    rows = extract_player_raw_rows(season)
    parsed: list[dict[str, Any]] = []

    for row in rows:
        if len(row) < 24 or not row[0].isdigit():
            continue

        player_name = re.sub(r'\s*#\d+.*$', '', row[1]).strip()
        parsed.append(
            {
                'season': season,
                'player_name': player_name,
                'team_name': row[2],
                'games_played': _to_int(row[3]),
                'points': _to_float(row[7]),
                'rebounds': _to_float(row[19]),
                'assists': _to_float(row[20]),
                'steals': _to_float(row[22]),
                'blocks': _to_float(row[23]),
            }
        )

    return parsed


def parse_team_stats(season: str) -> list[dict[str, Any]]:
    """チームスタッツページを解析してリストで返す"""
    sections = extract_standings_raw_rows()
    parsed: list[dict[str, Any]] = []

    for conference in ('東地区', '西地区'):
        for row in sections.get(conference, []):
            if len(row) < 5 or not row[0].isdigit():
                continue

            parsed.append(
                {
                    'season': season,
                    'team_name': _split_team_name(row[1]),
                    'wins': _to_int(row[2]),
                    'losses': _to_int(row[3]),
                    'win_rate': _to_float(row[4]),
                }
            )

    return parsed


def parse_rankings(season: str) -> list[dict[str, Any]]:
    """順位表ページを解析してリストで返す"""
    sections = extract_standings_raw_rows()
    parsed: list[dict[str, Any]] = []

    for conference, rows in sections.items():
        for row in rows:
            if len(row) < 2 or not row[0].isdigit():
                continue

            parsed.append(
                {
                    'season': season,
                    'rank': _to_int(row[0]),
                    'team_name': _split_team_name(row[1]),
                    'conference': conference,
                }
            )

    return parsed
