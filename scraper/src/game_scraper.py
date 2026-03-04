"""試合単位データのスクレイパー"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, HEADERS


SCHEDULE_KEY_PATTERN = re.compile(r'ScheduleKey=(\d+)')


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


def _extract_context_data(html: str) -> dict[str, Any]:
    # Try several possible JavaScript patterns that hold the contexts JSON
    needles = [
        '_contexts_s3id.data = ',
        'window._contexts_s3id = ',
        '_contexts_s3id = ',
    ]
    start = -1
    index = -1
    for n in needles:
        start = html.find(n)
        if start >= 0:
            index = start + len(n)
            break
    if start < 0:
        # Include a short head snippet to aid debugging when this occurs
        snippet = html[:1000].replace('\n', ' ')
        raise RuntimeError(f"Failed to find contexts JSON in game_detail HTML. html_head={snippet!r}")

    # advance to the first '{'
    while index < len(html) and html[index] != '{':
        index += 1

    brace_depth = 0
    for cursor in range(index, len(html)):
        c = html[cursor]
        if c == '{':
            brace_depth += 1
        elif c == '}':
            brace_depth -= 1
            if brace_depth == 0:
                raw_json = html[index:cursor+1]
                return json.loads(raw_json)

    raise RuntimeError('Unterminated JSON object when extracting contexts')


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

        try:
            context = _extract_context_data(response.text)
        except Exception as e:
            # Save a short HTML snippet for debugging and try next tab
            try:
                log_dir = Path(__file__).resolve().parent.parent / 'logs'
                log_dir.mkdir(parents=True, exist_ok=True)
                snippet = response.text[:2000]
                path = log_dir / f'failed_context_{schedule_key}_tab{tab}.html'
                path.write_text(snippet, encoding='utf-8')
                print(f'Warning: failed to extract contexts for {schedule_key} tab={tab}, saved snippet to {path}')
            except Exception:
                pass
            continue

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


def scrape_date_range_games(
    start_date: date,
    end_date: date,
    season: str,
    include_play_by_play: bool = False,
) -> dict[str, Any]:
    """指定期間の試合データをスクレイピングして返す"""
    day_to_keys: dict[str, list[int]] = {}
    all_keys: list[int] = []
    seen: set[int] = set()

    current = start_date
    while current <= end_date:
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
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'date_to_schedule_keys': day_to_keys,
        'game_count': len(games),
        'failed_schedule_keys': failed_keys,
        'games': games,
    }


def output_path_for_date_range(season: str, start_date: date, end_date: date) -> Path:
    root = Path(__file__).resolve().parent.parent
    output_dir = root / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    if start_date == end_date:
        return output_dir / f'games_{season}_{start_date.isoformat()}.json'
    return output_dir / f'games_{season}_{start_date.isoformat()}_{end_date.isoformat()}.json'


def save_date_range_games(
    start_date: date,
    end_date: date,
    season: str,
    include_play_by_play: bool = False,
) -> Path:
    payload = scrape_date_range_games(start_date, end_date, season, include_play_by_play=include_play_by_play)
    output_path = output_path_for_date_range(season, start_date, end_date)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_path
