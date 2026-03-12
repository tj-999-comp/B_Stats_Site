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
    tab: str | None,
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

    tab_label = tab if tab is not None else 'default'
    attempt = {
        'tab': tab_label,
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


def _extract_schedule_score_map_from_topics(topics: list[str]) -> dict[int, dict[str, Any]]:
    """schedule topics HTML から ScheduleKey ごとの最小スコア情報を抽出する。"""
    html = ''.join(topics)
    soup = BeautifulSoup(html, 'html.parser')

    score_map: dict[int, dict[str, Any]] = {}
    for item in soup.find_all('li', class_='list-item'):
        schedule_key: int | None = None

        raw_id = item.get('id')
        if raw_id is not None:
            try:
                schedule_key = int(raw_id)
            except Exception:
                schedule_key = None

        if schedule_key is None:
            anchor = item.find('a', href=True)
            if anchor is not None:
                match = SCHEDULE_KEY_PATTERN.search(anchor['href'])
                if match:
                    schedule_key = int(match.group(1))
        if schedule_key is None:
            continue

        home_score_node = item.select_one('.number.home-score span')
        away_score_node = item.select_one('.number.away-score span')
        home_name_node = item.select_one('.team.home .team-name')
        away_name_node = item.select_one('.team.away .team-name')

        def _to_int_or_none(text: str | None) -> int | None:
            if not text:
                return None
            cleaned = re.sub(r'[^0-9]', '', text)
            if not cleaned:
                return None
            try:
                return int(cleaned)
            except Exception:
                return None

        home_score = _to_int_or_none(home_score_node.get_text(strip=True) if home_score_node else None)
        away_score = _to_int_or_none(away_score_node.get_text(strip=True) if away_score_node else None)
        home_name = home_name_node.get_text(strip=True) if home_name_node else None
        away_name = away_name_node.get_text(strip=True) if away_name_node else None

        score_map[schedule_key] = {
            'HomeTeamScore': home_score,
            'AwayTeamScore': away_score,
            'HomeTeamNameJ': home_name,
            'AwayTeamNameJ': away_name,
        }

    return score_map


def _apply_schedule_score_fallback(
    games: list[dict[str, Any]],
    score_map: dict[int, dict[str, Any]],
) -> None:
    """html_fallback で取得したゲームに schedule topics 由来スコアを補完する。"""
    if not score_map:
        return

    for item in games:
        if not isinstance(item, dict):
            continue
        if item.get('source_tab') != 'fallback_html':
            continue

        schedule_key = _extract_item_schedule_key(item)
        if schedule_key is None:
            continue

        score_info = score_map.get(schedule_key)
        if not score_info:
            continue

        game = item.get('game')
        if not isinstance(game, dict):
            continue

        home_score = score_info.get('HomeTeamScore')
        away_score = score_info.get('AwayTeamScore')
        home_name = score_info.get('HomeTeamNameJ')
        away_name = score_info.get('AwayTeamNameJ')

        if game.get('HomeTeamScore') is None and home_score is not None:
            game['HomeTeamScore'] = home_score
        if game.get('AwayTeamScore') is None and away_score is not None:
            game['AwayTeamScore'] = away_score

        if not game.get('HomeTeamNameJ') and home_name:
            game['HomeTeamNameJ'] = home_name
        if not game.get('AwayTeamNameJ') and away_name:
            game['AwayTeamNameJ'] = away_name

        game['ScoreDataSource'] = 'schedule_topics_fallback'


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


def _extract_minimal_game_from_html(
    html: str,
    *,
    schedule_key: int,
    candidate_dates: list[str] | None = None,
) -> dict[str, Any] | None:
    """game_detail HTML から最小限の Game 情報を抽出するフォールバック。"""
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    if not title:
        return None

    # 例: "2017-18 B1リーグ 2018/01/01 A東京 VS 千葉 | B.LEAGUE（Bリーグ）公式サイト"
    match = re.search(
        r'^(?P<convention>.+?)\s+(?P<date>\d{4}/\d{2}/\d{2})\s+(?P<home>.+?)\s+VS\s+(?P<away>.+?)\s+\|',
        title,
    )

    convention = None
    game_date_iso: str | None = None
    home_name = None
    away_name = None
    if match:
        convention = match.group('convention').strip() or None
        home_name = match.group('home').strip() or None
        away_name = match.group('away').strip() or None
        game_date_iso = match.group('date').replace('/', '-')

    if game_date_iso is None and candidate_dates:
        game_date_iso = candidate_dates[0]

    game_datetime: str | None = None
    if game_date_iso is not None:
        try:
            jst = timezone(timedelta(hours=9))
            dt = datetime.fromisoformat(game_date_iso).replace(tzinfo=jst)
            game_datetime = str(int(dt.timestamp()))
        except Exception:
            game_datetime = None

    fallback_game: dict[str, Any] = {
        'ScheduleKey': schedule_key,
        'DataSource': 'html_fallback',
        'FallbackFieldsOnly': True,
    }
    if convention is not None:
        fallback_game['ConventionTitleJ'] = convention
    if game_datetime is not None:
        fallback_game['GameDateTime'] = game_datetime
    if home_name is not None:
        fallback_game['HomeTeamNameJ'] = home_name
        fallback_game['HomeTeamShortNameJ'] = home_name
    if away_name is not None:
        fallback_game['AwayTeamNameJ'] = away_name
        fallback_game['AwayTeamShortNameJ'] = away_name

    # ScheduleKey 以外が取れなければフォールバック失敗扱い
    if len(fallback_game) <= 3:
        return None

    return fallback_game


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
    request_headers = dict(HEADERS)
    request_headers['Accept-Encoding'] = 'gzip, deflate'

    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(2.0 ** attempt)  # 2秒 → 4秒
        last_exc = None
        try:
            response = requests.get(url, params=params, headers=request_headers, timeout=60)
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
    max_retries: int = 3,
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
    fallback_candidates: list[tuple[str | None, str, str]] = []
    jst = timezone(timedelta(hours=9))

    tab_candidates: list[str | None] = ['4', '2', None]
    for tab in tab_candidates:
        params = {'ScheduleKey': str(schedule_key)}
        if tab is not None:
            params['tab'] = tab
        request_url = requests.Request('GET', url, params=params).prepare().url or url

        response, retried, conn_exc = _fetch_game_detail_with_retry(
            url,
            params,
            max_retries=max_retries,
        )

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

        fallback_candidates.append((tab, response.url, response.text))

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
                tab_label = tab if tab is not None else 'default'
                path = log_dir / f'failed_context_{schedule_key}_tab{tab_label}.html'
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

        # context 抽出に成功しても、Game 本体が空のケースは取得失敗として扱う。
        # （このケースを成功扱いにすると、failed_schedule_keys に残らず再取得対象から漏れる）
        if not isinstance(game, dict) or not game:
            _record_game_detail_attempt(
                fetch_audit=fetch_audit,
                schedule_key=schedule_key,
                tab=tab,
                url=response.url,
                outcome='empty_game_payload',
                status_code=response.status_code,
                candidate_dates=candidate_dates,
                error='Game payload is empty',
            )
            continue

        result = {
            'schedule_key': schedule_key,
            'source_tab': tab if tab is not None else 'default',
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
                            selected_tab=tab if tab is not None else 'default',
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

    for tab, source_url, raw_html in fallback_candidates:
        fallback_game = _extract_minimal_game_from_html(
            raw_html,
            schedule_key=schedule_key,
            candidate_dates=candidate_dates,
        )
        if not fallback_game:
            continue

        _record_game_detail_attempt(
            fetch_audit=fetch_audit,
            schedule_key=schedule_key,
            tab=tab,
            url=source_url,
            outcome='minimal_html_fallback',
            status_code=200,
            candidate_dates=candidate_dates,
        )
        _mark_game_detail_result(
            fetch_audit,
            schedule_key,
            result='success',
            final_reason='minimal_html_fallback',
            selected_tab='fallback_html',
        )
        return {
            'schedule_key': schedule_key,
            'source_tab': 'fallback_html',
            'game': fallback_game,
            'summaries': [],
            'home_boxscores': [],
            'away_boxscores': [],
            'play_by_play_count': 0,
            'play_by_plays': [],
        }

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
        'error': 'Failed to fetch game_detail (HTTP 5xx or empty payload)',
    }


def scrape_date_range_games(
    start_date: date,
    end_date: date,
    season: str,
    include_play_by_play: bool = False,
    max_retries: int = 3,
) -> dict[str, Any]:
    """指定期間の試合データをスクレイピングして返す"""
    day_to_keys: dict[str, list[int]] = {}
    schedule_score_map: dict[int, dict[str, Any]] = {}
    all_keys: list[int] = []
    seen: set[int] = set()

    current = start_date
    schedule_api_year = _resolve_schedule_api_year(season, start_date)
    while current <= end_date:
        if current > start_date:
            time.sleep(1.0)  # スロットリング: schedule API リクエスト間の待機
        topics = _fetch_schedule_topics(current, schedule_api_year)
        keys = _extract_schedule_keys_from_topics(topics)
        schedule_score_map.update(_extract_schedule_score_map_from_topics(topics))
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
                max_retries=max_retries,
                candidate_dates=schedule_key_to_dates.get(schedule_key),
                fetch_audit=fetch_audit,
            )
        )

    _apply_mapped_date_to_game_datetimes(games, schedule_key_to_dates)
    _apply_schedule_score_fallback(games, schedule_score_map)

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
    max_retries: int = 3,
) -> Path:
    payload = scrape_date_range_games(
        start_date,
        end_date,
        season,
        include_play_by_play=include_play_by_play,
        max_retries=max_retries,
    )
    output_path = output_path_for_date_range(season, start_date, end_date)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return output_path


def load_latest_failed_schedule_keys(
    *,
    season: str,
    start_date: date,
    end_date: date,
) -> list[int]:
    """指定 run (season/start/end) の最新ログから failed_schedule_keys を返す。"""
    path = _game_detail_fetch_log_path()
    if not path.exists():
        return []

    try:
        loaded = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return []

    if not isinstance(loaded, list):
        return []

    start_iso = start_date.isoformat()
    end_iso = end_date.isoformat()

    for entry in reversed(loaded):
        if not isinstance(entry, dict):
            continue
        if entry.get('season') != season:
            continue
        if entry.get('start_date') != start_iso or entry.get('end_date') != end_iso:
            continue
        keys = entry.get('failed_schedule_keys', [])
        if not isinstance(keys, list):
            return []
        result: list[int] = []
        for key in keys:
            try:
                result.append(int(key))
            except Exception:
                continue
        return result

    return []


def _extract_item_schedule_key(item: dict[str, Any]) -> int | None:
    value = item.get('schedule_key')
    if value is None:
        game = item.get('game', {})
        if isinstance(game, dict):
            value = game.get('ScheduleKey')
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def retry_failed_games_into_json(
    *,
    target_json_path: Path,
    failed_schedule_keys: list[int],
    include_play_by_play: bool = False,
    max_retries: int = 3,
) -> dict[str, Any]:
    """失敗した schedule_key のみ再取得し、対象JSONへマージして保存する。"""
    payload = json.loads(target_json_path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise RuntimeError('target_json の形式が不正です: object ではありません')

    games = payload.get('games', [])
    if not isinstance(games, list):
        raise RuntimeError('target_json の形式が不正です: games が list ではありません')

    date_to_keys = payload.get('date_to_schedule_keys', {})
    if not isinstance(date_to_keys, dict):
        date_to_keys = {}
    schedule_key_to_dates = _build_schedule_key_to_mapped_date(date_to_keys)
    schedule_score_map: dict[int, dict[str, Any]] = {}

    fetch_audit: dict[int, dict[str, Any]] = {}
    merged: dict[int, dict[str, Any]] = {}
    order: list[int] = []

    for item in games:
        if not isinstance(item, dict):
            continue
        schedule_key = _extract_item_schedule_key(item)
        if schedule_key is None:
            continue
        if schedule_key not in merged:
            order.append(schedule_key)
        merged[schedule_key] = item

    normalized_keys: list[int] = []
    seen: set[int] = set()
    for key in failed_schedule_keys:
        try:
            sk = int(key)
        except Exception:
            continue
        if sk in seen:
            continue
        seen.add(sk)
        normalized_keys.append(sk)

    season = str(payload.get('season'))
    fetched_score_dates: set[str] = set()
    for schedule_key in normalized_keys:
        for iso in schedule_key_to_dates.get(schedule_key, []):
            if iso in fetched_score_dates:
                continue
            try:
                target = date.fromisoformat(iso)
            except Exception:
                continue
            api_year = _resolve_schedule_api_year(season, target)
            topics = _fetch_schedule_topics(target, api_year)
            schedule_score_map.update(_extract_schedule_score_map_from_topics(topics))
            fetched_score_dates.add(iso)

    for i, schedule_key in enumerate(normalized_keys):
        if i > 0:
            time.sleep(random.uniform(1.0, 3.0))
        fetched = fetch_game_context(
            schedule_key,
            include_play_by_play=include_play_by_play,
            max_retries=max_retries,
            candidate_dates=schedule_key_to_dates.get(schedule_key),
            fetch_audit=fetch_audit,
        )
        merged[schedule_key] = fetched
        if schedule_key not in order:
            order.append(schedule_key)

    merged_games = [merged[schedule_key] for schedule_key in order]
    _apply_mapped_date_to_game_datetimes(merged_games, schedule_key_to_dates)
    _apply_schedule_score_fallback(merged_games, schedule_score_map)

    failed_after = []
    for item in merged_games:
        if not isinstance(item, dict):
            continue
        if not item.get('error'):
            continue
        schedule_key = _extract_item_schedule_key(item)
        if schedule_key is not None:
            failed_after.append(schedule_key)

    start_date = date.fromisoformat(str(payload.get('start_date')))
    end_date = date.fromisoformat(str(payload.get('end_date')))
    _write_game_detail_fetch_run_log(
        season=season,
        start_date=start_date,
        end_date=end_date,
        game_count=len(normalized_keys),
        fetch_audit=fetch_audit,
    )

    payload['generated_at'] = datetime.now(timezone.utc).isoformat()
    payload['include_play_by_play'] = include_play_by_play
    payload['game_count'] = len(merged_games)
    payload['failed_schedule_keys'] = failed_after
    payload['games'] = merged_games

    target_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'season': season,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'target_json': str(target_json_path),
        'retried_count': len(normalized_keys),
        'failed_after_count': len(failed_after),
        'failed_after_schedule_keys': failed_after,
    }
