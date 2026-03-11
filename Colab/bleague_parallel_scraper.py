from __future__ import annotations

import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bleague.jp"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.bleague.jp/",
}
SCHEDULE_KEY_PATTERN = re.compile(r"ScheduleKey=(\d+)")


@dataclass
class ScrapeOptions:
    include_play_by_play: bool = False
    max_workers: int = 8
    request_timeout_sec: int = 60
    min_delay_sec: float = 0.2
    max_delay_sec: float = 0.8
    max_retries: int = 3


def _resolve_schedule_api_year(season: str, target_date: date) -> int:
    match = re.match(r"^(\d{4})-\d{2}$", season)
    if match:
        return int(match.group(1))
    return target_date.year


def _extract_context_data(html: str) -> dict[str, Any]:
    needles = [
        "_contexts_s3id.data = ",
        "window._contexts_s3id = ",
        "_contexts_s3id = ",
    ]

    start = -1
    index = -1
    for needle in needles:
        start = html.find(needle)
        if start >= 0:
            index = start + len(needle)
            break

    if start < 0:
        snippet = html[:1000].replace("\n", " ")
        raise RuntimeError(f"Failed to find contexts JSON. html_head={snippet!r}")

    while index < len(html) and html[index] != "{":
        index += 1

    depth = 0
    for cursor in range(index, len(html)):
        ch = html[cursor]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[index : cursor + 1])

    raise RuntimeError("Unterminated JSON object while extracting contexts")


def _fetch_schedule_topics(target_date: date, schedule_api_year: int) -> list[str]:
    url = f"{BASE_URL}/schedule/"
    params = {
        "data_format": "json",
        "year": str(schedule_api_year),
        "mon": f"{target_date.month:02d}",
        "day": f"{target_date.day:02d}",
        "tab": "1",
        "event": "",
        "club": "",
    }
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": HEADERS["Accept-Language"],
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE_URL}/schedule/",
    }

    last_error = None
    for attempt in range(1, 5):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            topics = payload.get("topics", [])
            if isinstance(topics, list):
                return topics
            last_error = "topics is not a list"
        except Exception as exc:
            last_error = str(exc)

        if attempt < 4:
            time.sleep(float(attempt))

    print(f"[WARN] schedule fetch failed: date={target_date} error={last_error}")
    return []


def _extract_schedule_keys_from_topics(topics: list[str]) -> list[int]:
    soup = BeautifulSoup("".join(topics), "html.parser")
    keys: list[int] = []
    seen: set[int] = set()

    for anchor in soup.find_all("a", href=True):
        match = SCHEDULE_KEY_PATTERN.search(anchor["href"])
        if not match:
            continue
        schedule_key = int(match.group(1))
        if schedule_key in seen:
            continue
        seen.add(schedule_key)
        keys.append(schedule_key)

    return keys


def _fetch_game_detail_with_retry(
    schedule_key: int,
    tab: str,
    timeout_sec: int,
    max_retries: int,
) -> tuple[requests.Response | None, int, Exception | None]:
    url = f"{BASE_URL}/game_detail/"
    params = {"ScheduleKey": str(schedule_key), "tab": tab}

    last_exc: Exception | None = None
    last_response: requests.Response | None = None

    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(2.0 ** attempt)

        last_exc = None
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout_sec)
            last_response = response
        except requests.RequestException as exc:
            last_exc = exc
            continue

        if response.status_code < 500:
            return response, attempt, None

    return last_response, max_retries - 1, last_exc


def _fetch_single_game(
    schedule_key: int,
    candidate_dates: list[str] | None,
    options: ScrapeOptions,
) -> dict[str, Any]:
    if options.max_delay_sec > 0:
        time.sleep(random.uniform(options.min_delay_sec, options.max_delay_sec))

    jst = timezone(timedelta(hours=9))
    first_success: dict[str, Any] | None = None

    for tab in ("4", "2"):
        response, _retried, conn_exc = _fetch_game_detail_with_retry(
            schedule_key=schedule_key,
            tab=tab,
            timeout_sec=options.request_timeout_sec,
            max_retries=options.max_retries,
        )

        if conn_exc is not None:
            continue

        if response is None or response.status_code >= 500:
            continue

        try:
            response.raise_for_status()
            context = _extract_context_data(response.text)
        except Exception:
            continue

        game = context.get("Game", {})
        result = {
            "schedule_key": schedule_key,
            "source_tab": tab,
            "game": game,
            "summaries": context.get("Summaries", []),
            "home_boxscores": context.get("HomeBoxscores", []),
            "away_boxscores": context.get("AwayBoxscores", []),
            "play_by_play_count": len(context.get("PlayByPlays", [])),
            "play_by_plays": context.get("PlayByPlays", []) if options.include_play_by_play else [],
        }

        if candidate_dates:
            raw_ts = game.get("GameDateTime")
            if raw_ts is not None:
                try:
                    g_date = datetime.fromtimestamp(int(raw_ts), tz=jst).date().isoformat()
                    if g_date in candidate_dates:
                        return result
                except Exception:
                    pass

        if first_success is None:
            first_success = result

    if first_success is not None:
        return first_success

    return {
        "schedule_key": schedule_key,
        "source_tab": None,
        "game": {},
        "summaries": [],
        "home_boxscores": [],
        "away_boxscores": [],
        "play_by_play_count": 0,
        "play_by_plays": [],
        "error": "Failed to fetch game_detail",
    }


def _build_schedule_key_to_dates(day_to_keys: dict[str, list[int]]) -> dict[int, list[str]]:
    schedule_key_to_dates: dict[int, list[str]] = {}
    for mapped_date, keys in day_to_keys.items():
        for key in keys:
            schedule_key_to_dates.setdefault(int(key), []).append(mapped_date)
    return schedule_key_to_dates


def _apply_mapped_date_to_game_datetimes(
    games: list[dict[str, Any]],
    schedule_key_to_dates: dict[int, list[str]],
) -> None:
    jst = timezone(timedelta(hours=9))

    for item in games:
        game = item.get("game")
        if not isinstance(game, dict):
            continue

        schedule_key = item.get("schedule_key") or game.get("ScheduleKey")
        if schedule_key is None:
            continue

        try:
            schedule_key_int = int(schedule_key)
        except Exception:
            continue

        candidate_dates = schedule_key_to_dates.get(schedule_key_int)
        if not candidate_dates:
            continue

        raw_ts = game.get("GameDateTime")
        if raw_ts is None:
            continue

        try:
            original_jst = datetime.fromtimestamp(int(raw_ts), tz=jst)
        except Exception:
            continue

        chosen_date = original_jst.date().isoformat()
        if chosen_date not in candidate_dates:
            chosen_date = candidate_dates[0]

        try:
            year, month, day = map(int, chosen_date.split("-"))
            normalized_jst = datetime(
                year,
                month,
                day,
                original_jst.hour,
                original_jst.minute,
                original_jst.second,
                tzinfo=jst,
            )
            game["GameDateTime"] = str(int(normalized_jst.timestamp()))
        except Exception:
            continue


def scrape_date_range_games_parallel(
    start_date: date,
    end_date: date,
    season: str,
    options: ScrapeOptions | None = None,
) -> dict[str, Any]:
    options = options or ScrapeOptions()

    day_to_keys: dict[str, list[int]] = {}
    all_keys: list[int] = []
    seen: set[int] = set()

    schedule_api_year = _resolve_schedule_api_year(season, start_date)

    current = start_date
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

    schedule_key_to_dates = _build_schedule_key_to_dates(day_to_keys)

    games: list[dict[str, Any]] = []
    if all_keys:
        with ThreadPoolExecutor(max_workers=max(1, options.max_workers)) as executor:
            futures = {
                executor.submit(
                    _fetch_single_game,
                    schedule_key,
                    schedule_key_to_dates.get(schedule_key),
                    options,
                ): schedule_key
                for schedule_key in all_keys
            }

            for future in as_completed(futures):
                games.append(future.result())

        order_map = {key: i for i, key in enumerate(all_keys)}
        games.sort(key=lambda item: order_map.get(int(item.get("schedule_key", -1)), 10**9))

    _apply_mapped_date_to_game_datetimes(games, schedule_key_to_dates)

    failed_keys = [item["schedule_key"] for item in games if item.get("error")]

    return {
        "season": season,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "include_play_by_play": options.include_play_by_play,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "date_to_schedule_keys": day_to_keys,
        "game_count": len(games),
        "failed_schedule_keys": failed_keys,
        "games": games,
    }


def output_path_for_date_range(output_dir: Path, season: str, start_date: date, end_date: date) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if start_date == end_date:
        return output_dir / f"games_{season}_{start_date.isoformat()}.json"
    return output_dir / f"games_{season}_{start_date.isoformat()}_{end_date.isoformat()}.json"


def save_date_range_games_parallel(
    start_date: date,
    end_date: date,
    season: str,
    output_dir: Path,
    options: ScrapeOptions | None = None,
) -> Path:
    payload = scrape_date_range_games_parallel(
        start_date=start_date,
        end_date=end_date,
        season=season,
        options=options,
    )
    out_path = output_path_for_date_range(output_dir, season, start_date, end_date)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
