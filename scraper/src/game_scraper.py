"""試合単位データのスクレイパー"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, HEADERS


SCHEDULE_KEY_PATTERN = re.compile(r'ScheduleKey=(\d+)')


@dataclass(frozen=True)
class OpeningWeekRange:
    opening_date: date
    end_date: date


def _season_start_year(season: str) -> int:
    head = season.split('-')[0]
    return int(head)


def _fetch_schedule_topics(target_date: date) -> list[str]:
    url = f'{BASE_URL}/schedule/'
    params = {
        'data_format': 'json',
        'year': str(target_date.year),
        'mon': f'{target_date.month:02d}',
        'day': f'{target_date.day:02d}',
        'tab': '1',
        'event': '',
        'club': '',
    }
    headers = {
        **HEADERS,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE_URL}/schedule/',
    }

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    payload = response.json()
    return payload.get('topics', [])


def _extract_schedule_keys_from_topics(topics: list[str]) -> list[int]:
    html = ''.join(topics)
    soup = BeautifulSoup(html, 'html.parser')
    keys: list[int] = []
    seen: set[int] = set()

    for anchor in soup.find_all('a', href=True):
        match = SCHEDULE_KEY_PATTERN.search(anchor['href'])
        if not match:
            continue
        schedule_key = int(match.group(1))
        if schedule_key in seen:
            continue
        seen.add(schedule_key)
        keys.append(schedule_key)

    return keys


def find_opening_week_range(season: str) -> OpeningWeekRange:
    start_year = _season_start_year(season)
    start_day = date(start_year, 9, 1)
    end_search_day = date(start_year, 12, 31)

    current = start_day
    while current <= end_search_day:
        topics = _fetch_schedule_topics(current)
        keys = _extract_schedule_keys_from_topics(topics)
        if keys:
            return OpeningWeekRange(
                opening_date=current,
                end_date=current + timedelta(days=6),
            )
        current += timedelta(days=1)

    raise RuntimeError(f'Opening date not found for season {season}')


def _extract_context_data(html: str) -> dict[str, Any]:
    needle = '_contexts_s3id.data = '
    start = html.find(needle)
    if start < 0:
        raise RuntimeError('Failed to find _contexts_s3id.data in game_detail HTML')

    index = start + len(needle)
    while index < len(html) and html[index] != '{':
        index += 1

    brace_depth = 0
    end = index
    for cursor in range(index, len(html)):
        char = html[cursor]
        if char == '{':
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
            if brace_depth == 0:
                end = cursor + 1
                break

    raw_json = html[index:end]
    return json.loads(raw_json)


def fetch_game_context(schedule_key: int, include_play_by_play: bool = False) -> dict[str, Any]:
    url = f'{BASE_URL}/game_detail/'
    for tab in ('4', '2'):
        params = {
            'ScheduleKey': str(schedule_key),
            'tab': tab,
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=60)
        if response.status_code >= 500:
            continue
        response.raise_for_status()

        context = _extract_context_data(response.text)
        game = context.get('Game', {})
        summaries = context.get('Summaries', [])
        home_boxscores = context.get('HomeBoxscores', [])
        away_boxscores = context.get('AwayBoxscores', [])
        play_by_plays = context.get('PlayByPlays', []) if include_play_by_play else []

        return {
            'schedule_key': schedule_key,
            'source_tab': tab,
            'game': game,
            'summaries': summaries,
            'home_boxscores': home_boxscores,
            'away_boxscores': away_boxscores,
            'play_by_play_count': len(context.get('PlayByPlays', [])),
            'play_by_plays': play_by_plays,
        }

    return {
        'schedule_key': schedule_key,
        'source_tab': None,
        'game': {},
        'summaries': [],
        'home_boxscores': [],
        'away_boxscores': [],
        'play_by_play_count': 0,
        'play_by_plays': [],
        'error': 'Failed to fetch game_detail (HTTP 5xx)',
    }


def scrape_opening_week_games(season: str, include_play_by_play: bool = False) -> dict[str, Any]:
    week_range = find_opening_week_range(season)

    day_to_keys: dict[str, list[int]] = {}
    all_keys: list[int] = []
    seen: set[int] = set()

    current = week_range.opening_date
    while current <= week_range.end_date:
        topics = _fetch_schedule_topics(current)
        keys = _extract_schedule_keys_from_topics(topics)
        day_to_keys[current.isoformat()] = keys

        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            all_keys.append(key)

        current += timedelta(days=1)

    games = [
        fetch_game_context(schedule_key, include_play_by_play=include_play_by_play)
        for schedule_key in all_keys
    ]
    failed_keys = [game['schedule_key'] for game in games if game.get('error')]

    return {
        'season': season,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'include_play_by_play': include_play_by_play,
        'opening_date': week_range.opening_date.isoformat(),
        'end_date': week_range.end_date.isoformat(),
        'date_to_schedule_keys': day_to_keys,
        'game_count': len(games),
        'failed_schedule_keys': failed_keys,
        'games': games,
    }


def output_path_for_opening_week(season: str) -> Path:
    root = Path(__file__).resolve().parent.parent
    output_dir = root / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f'games_{season}_opening_week.json'


def save_opening_week_games(season: str, include_play_by_play: bool = False) -> Path:
    payload = scrape_opening_week_games(season, include_play_by_play=include_play_by_play)
    output_path = output_path_for_opening_week(season)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_path
