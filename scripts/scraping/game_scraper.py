"""試合単位データのスクレイパー"""

from __future__ import annotations

import json
import random
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from scripts.db.config import BASE_URL, HEADERS, SCRAPER_ROOT


SCHEDULE_KEY_PATTERN = re.compile(r'ScheduleKey=(\d+)')


def _game_detail_fetch_log_path() -> Path:
    log_dir = SCRAPER_ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / 'game_detail_fetch_log.json'


def _schedule_fetch_log_path() -> Path:
    log_dir = SCRAPER_ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / 'schedule_fetch_log.json'


def _append_schedule_fetch_log(entry: dict[str, Any]) -> None:
    path = _schedule_fetch_log_path()
    payload: list[dict[str, Any]] = []
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(loaded, list):
                payload = loaded
        except Exception:
            payload = []
    payload.append(entry)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def _summarize_error(error: str | None, max_length: int = 200) -> str | None:
    if not error:
        return None

    text = str(error).replace('\n', ' ').strip()
    if ' html_head=' in text:
        text = text.split(' html_head=', 1)[0]
    if len(text) > max_length:
        return f'{text[: max_length - 3]}...'
    return text


def _append_game_detail_fetch_log(entry: dict[str, Any]) -> None:
    path = _game_detail_fetch_log_path()
    payload: list[dict[str, Any]] = []

    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(loaded, list):
                if (
                    loaded
                    and isinstance(loaded[0], dict)
                    and 'failed_games' not in loaded[0]
                    and loaded[0].get('format') != 'legacy_attempt_log'
                ):
                    payload = [
                        {
                            'migrated_at': datetime.now(timezone.utc).isoformat(),
                            'format': 'legacy_attempt_log',
                            'entries': loaded,
                        }
                    ]
                else:
                    payload = loaded
        except Exception:
            payload = []

    payload.append(entry)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def _record_game_detail_attempt(
    *,
    fetch_audit: dict[int, dict[str, Any]] | None,
    schedule_key: int,
    tab: str,
    url: str,
    outcome: str,
    status_code: int | None = None,
    candidate_dates: list[str] | None = None,
    error: str | None = None,
    retried: int = 0,
) -> None:
    if fetch_audit is None:
        return

    game_log = fetch_audit.setdefault(
        schedule_key,
        {
            'schedule_key': schedule_key,
            'candidate_dates': candidate_dates or [],
            'attempts': [],
            'result': 'pending',
            'final_reason': None,
        },
    )
    if candidate_dates and not game_log.get('candidate_dates'):
        game_log['candidate_dates'] = candidate_dates

    attempt = {
        'tab': tab,
        'status_code': status_code,
        'outcome': outcome,
        'url': url,
    }
    summarized_error = _summarize_error(error)
    if summarized_error:
        attempt['error'] = summarized_error
    if retried > 0:
        attempt['retried'] = retried
    game_log['attempts'].append(attempt)


def _mark_game_detail_result(
    fetch_audit: dict[int, dict[str, Any]] | None,
    schedule_key: int,
    *,
    result: str,
    final_reason: str,
    selected_tab: str | None = None,
) -> None:
    if fetch_audit is None:
        return

    game_log = fetch_audit.setdefault(
        schedule_key,
        {
            'schedule_key': schedule_key,
            'candidate_dates': [],
            'attempts': [],
        },
    )
    game_log['result'] = result
    game_log['final_reason'] = final_reason
    if selected_tab is not None:
        game_log['selected_tab'] = selected_tab


def _write_game_detail_fetch_run_log(
    *,
    season: str,
    start_date: date,
    end_date: date,
    game_count: int,
    fetch_audit: dict[int, dict[str, Any]],
) -> None:
    failed_games = []
    for schedule_key in sorted(fetch_audit):
        game_log = fetch_audit[schedule_key]
        if game_log.get('result') != 'failed':
            continue
        failed_games.append(
            {
                'schedule_key': schedule_key,
                'candidate_dates': game_log.get('candidate_dates', []),
                'final_reason': game_log.get('final_reason'),
                'attempts': game_log.get('attempts', []),
            }
        )

    run_summary = {
        'run_at': datetime.now(timezone.utc).isoformat(),
        'season': season,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'game_count': game_count,
        'failed_count': len(failed_games),
        'failed_schedule_keys': [item['schedule_key'] for item in failed_games],
        'failed_games': failed_games,
    }
    _append_game_detail_fetch_log(run_summary)


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
    # NOTE:
    # schedule API はヘッダに敏感で 503 invalid headers を返すことがあるため、
    # game_detail よりも軽量なヘッダでリトライし、最終失敗時は [] を返して処理継続する。
    headers = {
        'User-Agent': HEADERS.get('User-Agent', 'Mozilla/5.0'),
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': HEADERS.get('Accept-Language', 'ja,en-US;q=0.9,en;q=0.8'),
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE_URL}/schedule/',
    }

    max_attempts = 4
    last_error: str | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            topics = payload.get('topics', [])
            if isinstance(topics, list):
                return topics
            last_error = 'topics is not a list'
        except Exception as exc:
            last_error = str(exc)

        if attempt < max_attempts:
            time.sleep(1.0 * attempt)

    _append_schedule_fetch_log(
        {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'date': target_date.isoformat(),
            'year': schedule_api_year,
            'url': requests.Request('GET', url, params=params).prepare().url,
            'attempts': max_attempts,
            'error': _summarize_error(last_error),
            'result': 'failed_return_empty_topics',
        }
    )
    return []


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


def _fetch_game_detail_with_retry(
    url: str,
    params: dict[str, str],
    max_retries: int = 3,
) -> tuple[requests.Response | None, int, Exception | None]:
    """5xx / 接続エラー時に Exponential Backoff でリトライする。

    Returns:
        (response_or_None, retry_count, last_conn_exception_or_None)
        - response が None かつ exception が None → 5xx で全失敗
    """
    last_exc: Exception | None = None
    last_response: requests.Response | None = None

    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(2.0 ** attempt)  # 2秒 → 4秒
        last_exc = None
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=60)
            last_response = response
        except requests.RequestException as exc:
            last_exc = exc
            continue
        if response.status_code < 500:
            return response, attempt, None
        # 5xx: 次のリトライへ

    return last_response, max_retries - 1, last_exc


def fetch_game_context(
    schedule_key: int,
    include_play_by_play: bool = False,
    candidate_dates: list[str] | None = None,
    fetch_audit: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Fetch game_detail contexts for `schedule_key`.

    If `candidate_dates` is provided (list of YYYY-MM-DD strings), prefer
    the tab whose contexts `GameDateTime` (JST) date matches one of the
    candidates. If none match, return the first successful tab.
    """
    url = f'{BASE_URL}/game_detail/'
    first_success: dict[str, Any] | None = None
    jst = timezone(timedelta(hours=9))

    for tab in ('4', '2'):
        params = {
            'ScheduleKey': str(schedule_key),
            'tab': tab,
        }
        request_url = requests.Request('GET', url, params=params).prepare().url or url

        response, retried, conn_exc = _fetch_game_detail_with_retry(url, params)

        if conn_exc is not None:
            _record_game_detail_attempt(
                fetch_audit=fetch_audit,
                schedule_key=schedule_key,
                tab=tab,
                url=request_url,
                outcome='request_exception',
                candidate_dates=candidate_dates,
                error=str(conn_exc),
                retried=retried,
            )
            continue

        if response is None or response.status_code >= 500:
            _record_game_detail_attempt(
                fetch_audit=fetch_audit,
                schedule_key=schedule_key,
                tab=tab,
                url=response.url if response else request_url,
                outcome='http_5xx',
                status_code=response.status_code if response else None,
                candidate_dates=candidate_dates,
                retried=retried,
            )
            continue

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            _record_game_detail_attempt(
                fetch_audit=fetch_audit,
                schedule_key=schedule_key,
                tab=tab,
                url=response.url,
                outcome='http_error',
                status_code=response.status_code,
                candidate_dates=candidate_dates,
                error=str(exc),
            )
            continue

        try:
            context = _extract_context_data(response.text)
        except Exception as exc:
            snippet_path: str | None = None
            _record_game_detail_attempt(
                fetch_audit=fetch_audit,
                schedule_key=schedule_key,
                tab=tab,
                url=response.url,
                outcome='extract_failed',
                status_code=response.status_code,
                candidate_dates=candidate_dates,
                error=str(exc),
            )
            # Save a short HTML snippet for debugging and try next tab
            try:
                log_dir = SCRAPER_ROOT / 'logs'
                log_dir.mkdir(parents=True, exist_ok=True)
                snippet = response.text[:2000]
                path = log_dir / f'failed_context_{schedule_key}_tab{tab}.html'
                path.write_text(snippet, encoding='utf-8')
                snippet_path = str(path.relative_to(SCRAPER_ROOT.parent))
            except Exception:
                pass
            if snippet_path and fetch_audit is not None:
                fetch_audit[schedule_key]['attempts'][-1]['snippet_path'] = snippet_path
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
                        _mark_game_detail_result(
                            fetch_audit,
                            schedule_key,
                            result='success',
                            final_reason='selected_candidate_match',
                            selected_tab=tab,
                        )
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
                _mark_game_detail_result(
                    fetch_audit,
                    schedule_key,
                    result='success',
                    final_reason=f'selected_fallback_tab contexts_date={g_date}',
                    selected_tab=str(first_success.get('source_tab')),
                )
            except Exception:
                pass
        else:
            _mark_game_detail_result(
                fetch_audit,
                schedule_key,
                result='success',
                final_reason='first_success',
                selected_tab=str(first_success.get('source_tab')),
            )
        return first_success

    _mark_game_detail_result(
        fetch_audit,
        schedule_key,
        result='failed',
        final_reason='no_successful_tab',
    )
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
        if current > start_date:
            time.sleep(1.0)  # スロットリング: schedule API リクエスト間の待機
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
    fetch_audit: dict[int, dict[str, Any]] = {}

    # Fetch contexts preferring tabs whose contexts date matches candidates
    # スロットリング: リクエスト間に 1〜3 秒のランダム待機を挿入してレートリミットを回避
    games = []
    for i, schedule_key in enumerate(all_keys):
        if i > 0:
            time.sleep(random.uniform(1.0, 3.0))
        games.append(
            fetch_game_context(
                schedule_key,
                include_play_by_play=include_play_by_play,
                candidate_dates=schedule_key_to_dates.get(schedule_key),
                fetch_audit=fetch_audit,
            )
        )

    _apply_mapped_date_to_game_datetimes(games, schedule_key_to_dates)

    failed_keys = [game['schedule_key'] for game in games if game.get('error')]
    _write_game_detail_fetch_run_log(
        season=season,
        start_date=start_date,
        end_date=end_date,
        game_count=len(games),
        fetch_audit=fetch_audit,
    )

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
    root = SCRAPER_ROOT
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
