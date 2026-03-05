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


def _build_schedule_key_to_mapped_date(day_to_keys: dict[str, list[int]]) -> dict[int, list[str]]:
    """date_to_schedule_keys から schedule_key -> mapped_date のリストを構築する

    同じ schedule_key が複数日で出現するケースに備えて、
    値は候補日（文字列 YYYY-MM-DD）のリストを返します。
    実際にどの日付を採用するかは後段の補正処理で決定します。
    """
    schedule_key_to_dates: dict[int, list[str]] = {}

    for mapped_date, keys in day_to_keys.items():
        for key in keys:
            try:
                k = int(key)
            except Exception:
                continue
            schedule_key_to_dates.setdefault(k, []).append(mapped_date)

    return schedule_key_to_dates


def _apply_mapped_date_to_game_datetimes(
    games: list[dict[str, Any]],
    schedule_key_to_dates: dict[int, list[str]],
) -> None:
    """mapped_date 候補を用いて GameDateTime の日付を補正する（時刻は保持）。

    複数候補が存在する場合は、まず game に含まれる `GameDateTime` の
    JST 日付と一致する候補があればそれを優先します。無ければ候補リスト
    の先頭を採用します。整合しないケースは警告を出します。
    """
    jst = timezone(timedelta(hours=9))

    for item in games:
        game = item.get('game')
        if not isinstance(game, dict):
            continue

        schedule_key = item.get('schedule_key') or game.get('ScheduleKey')
        if schedule_key is None:
            continue

        try:
            schedule_key_int = int(schedule_key)
        except Exception:
            continue

        candidate_dates = schedule_key_to_dates.get(schedule_key_int)
        if not candidate_dates:
            continue

        raw_ts = game.get('GameDateTime')
        if raw_ts is None:
            continue

        try:
            ts = int(raw_ts)
            original_jst = datetime.fromtimestamp(ts, tz=jst)
        except Exception:
            continue

        # 優先ロジック: contexts による元の JST 日付と一致する候補を探す
        orig_date_iso = original_jst.date().isoformat()
        chosen_date = None
        if orig_date_iso in candidate_dates:
            chosen_date = orig_date_iso
        else:
            # 候補の中に一致がない場合は最初の出現を使う（安定的なフォールバック）
            chosen_date = candidate_dates[0]

        try:
            year, month, day = map(int, chosen_date.split('-'))
            normalized_jst = datetime(
                year,
                month,
                day,
                original_jst.hour,
                original_jst.minute,
                original_jst.second,
                tzinfo=jst,
            )
        except Exception:
            continue

        if chosen_date != orig_date_iso and len(candidate_dates) > 1:
            # 複数候補があるケースで最終採用日と contexts の元日付が不一致なら警告
            try:
                print(
                    f'Warning: schedule_key={schedule_key_int} had candidates={candidate_dates}; '
                    f'original contexts date={orig_date_iso}; chosen mapped_date={chosen_date}'
                )
            except Exception:
                pass

        game['GameDateTime'] = str(int(normalized_jst.timestamp()))


def _resolve_schedule_api_year(season: str, target_date: date) -> int:
    """schedule API に渡す year を決定する（原則: シーズン開始年）。"""
    match = re.match(r'^(\d{4})-\d{2}$', season)
    if match:
        return int(match.group(1))
    return target_date.year


def _fetch_schedule_topics(target_date: date, schedule_api_year: int) -> list[str]:
    url = f'{BASE_URL}/schedule/'
    params = {
        'data_format': 'json',
        'year': str(schedule_api_year),
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


def fetch_game_context(
    schedule_key: int,
    include_play_by_play: bool = False,
    candidate_dates: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch game_detail contexts for `schedule_key`.

    If `candidate_dates` is provided (list of YYYY-MM-DD strings), prefer
    the tab whose contexts `GameDateTime` (JST) date matches one of the
    candidates. If none match, return the first successful tab but print
    a warning to aid debugging.
    """
    url = f'{BASE_URL}/game_detail/'
    first_success: dict[str, Any] | None = None
    jst = timezone(timedelta(hours=9))

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
        except Exception:
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

        result = {
            'schedule_key': schedule_key,
            'source_tab': tab,
            'game': game,
            'summaries': summaries,
            'home_boxscores': home_boxscores,
            'away_boxscores': away_boxscores,
            'play_by_play_count': len(context.get('PlayByPlays', [])),
            'play_by_plays': play_by_plays,
        }

        # If there are candidate dates, prefer a tab whose GameDateTime (JST)
        # date matches one of them.
        if candidate_dates:
            raw_ts = game.get('GameDateTime')
            if raw_ts is not None:
                try:
                    ts = int(raw_ts)
                    g_jst = datetime.fromtimestamp(ts, tz=jst)
                    g_date_iso = g_jst.date().isoformat()
                    if g_date_iso in candidate_dates:
                        return result
                except Exception:
                    pass

        if first_success is None:
            first_success = result

    if first_success is not None:
        if candidate_dates:
            try:
                g = first_success.get('game', {})
                raw_ts = g.get('GameDateTime')
                g_date = None
                if raw_ts is not None:
                    try:
                        g_date = datetime.fromtimestamp(int(raw_ts), tz=jst).date().isoformat()
                    except Exception:
                        pass
                print(
                    f"Warning: schedule_key={schedule_key} candidates={candidate_dates} - no tab matched; returning tab={first_success.get('source_tab')} with contexts date={g_date}"
                )
            except Exception:
                pass
        return first_success

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
    schedule_api_year = _resolve_schedule_api_year(season, start_date)
    while current <= end_date:
        topics = _fetch_schedule_topics(current, schedule_api_year)
        keys = _extract_schedule_keys_from_topics(topics)
        day_to_keys[current.isoformat()] = keys

        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            all_keys.append(key)

        current += timedelta(days=1)

    # Build mapping schedule_key -> candidate mapped dates (list)
    schedule_key_to_dates = _build_schedule_key_to_mapped_date(day_to_keys)

    # Fetch contexts preferring tabs whose contexts date matches candidates
    games = [
        fetch_game_context(
            schedule_key,
            include_play_by_play=include_play_by_play,
            candidate_dates=schedule_key_to_dates.get(schedule_key),
        )
        for schedule_key in all_keys
    ]

    _apply_mapped_date_to_game_datetimes(games, schedule_key_to_dates)

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
