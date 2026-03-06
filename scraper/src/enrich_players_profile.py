"""players.json の nationality / player_slot_category を補完する。"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, HEADERS


ROSTER_DETAIL_URL = f'{BASE_URL}/roster_detail/'

JAPAN_PREFECTURES = (
    '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
    '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
    '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
    '岐阜県', '静岡県', '愛知県', '三重県',
    '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
    '鳥取県', '島根県', '岡山県', '広島県', '山口県',
    '徳島県', '香川県', '愛媛県', '高知県',
    '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県',
)

JAPAN_PLACE_HINTS_EN = (
    'japan', 'tokyo', 'hokkaido', 'osaka', 'kyoto', 'fukuoka', 'okinawa',
)


def _norm_text(value: str | None) -> str:
    if value is None:
        return ''
    return ' '.join(value.replace('\u3000', ' ').split())


def _is_index_like(value: str) -> bool:
    return bool(re.fullmatch(r'\d{1,2}\.?', value))


def _extract_from_dt_dd(soup: BeautifulSoup, label: str) -> str | None:
    for dt in soup.find_all('dt'):
        if _norm_text(dt.get_text(' ', strip=True)) != label:
            continue
        dd = dt.find_next_sibling('dd')
        if not dd:
            continue
        value = _norm_text(dd.get_text(' ', strip=True))
        if value:
            return value
    return None


def _extract_from_th_td(soup: BeautifulSoup, label: str) -> str | None:
    for th in soup.find_all('th'):
        if _norm_text(th.get_text(' ', strip=True)) != label:
            continue
        td = th.find_next_sibling('td')
        if not td:
            continue
        value = _norm_text(td.get_text(' ', strip=True))
        if value:
            return value
    return None


def _extract_from_li_strings(soup: BeautifulSoup, label: str) -> str | None:
    for li in soup.find_all('li'):
        strings = [_norm_text(text) for text in li.stripped_strings]
        strings = [text for text in strings if text]
        if label not in strings:
            continue
        label_index = strings.index(label)
        for candidate in strings[label_index + 1:]:
            if _is_index_like(candidate):
                continue
            if candidate == label:
                continue
            return candidate
    return None


def extract_profile_value(soup: BeautifulSoup, label: str) -> str | None:
    for extractor in (_extract_from_dt_dd, _extract_from_th_td, _extract_from_li_strings):
        value = extractor(soup, label)
        if value:
            return value
    return None


def is_japan_nationality(value: str | None) -> bool:
    normalized = _norm_text(value).lower()
    if not normalized:
        return False
    return '日本' in normalized or 'japan' in normalized or normalized == 'jpn'


def is_japanese_place(value: str | None) -> bool:
    place = _norm_text(value)
    if not place:
        return False

    lower_place = place.lower()
    if '日本' in place:
        return True
    if any(prefecture in place for prefecture in JAPAN_PREFECTURES):
        return True
    if any(hint in lower_place for hint in JAPAN_PLACE_HINTS_EN):
        return True
    if re.search(r'[一-龥ぁ-んァ-ン]', place) and any(token in place for token in ('都', '道', '府', '県')):
        return True
    return False


def map_profile_fields(league_nationality: str | None, birthplace: str | None) -> tuple[str | None, str | None]:
    if birthplace and is_japanese_place(birthplace):
        return '日本', '日本人選手'

    if birthplace and not is_japanese_place(birthplace) and league_nationality and not is_japan_nationality(league_nationality):
        return birthplace, '外国籍選手'

    return None, None


def enrich_players(
    players: list[dict[str, Any]],
    *,
    timeout: int = 30,
    delay: float = 0.2,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    session = requests.Session()
    target_players = players[:limit] if limit is not None else players
    total = len(target_players)

    for index, player in enumerate(target_players, start=1):
        player_id = _norm_text(str(player.get('player_id') or ''))
        if not player_id:
            raise RuntimeError(f'player_id is missing: player={player!r}')

        response = session.get(
            ROSTER_DETAIL_URL,
            params={'PlayerID': player_id},
            headers=HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        league_nationality = extract_profile_value(soup, 'リーグ登録国籍')
        birthplace = extract_profile_value(soup, '出身地')
        nationality, player_slot_category = map_profile_fields(league_nationality, birthplace)

        player['nationality'] = nationality
        player['player_slot_category'] = player_slot_category

        print(
            f'[{index}/{total}] player_id={player_id} '
            f'league_nationality={league_nationality!r} birthplace={birthplace!r} '
            f'=> nationality={nationality!r} player_slot_category={player_slot_category!r}'
        )

        if delay > 0 and index < total:
            time.sleep(delay)

    return players


def load_players(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, list):
        raise RuntimeError(f'Expected list JSON: path={path}')
    for row in payload:
        if not isinstance(row, dict):
            raise RuntimeError(f'Expected list[dict] JSON: path={path}')
    return payload


def write_players(path: Path, players: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding='utf-8')


def run(
    input_path: Path,
    output_path: Path,
    *,
    timeout: int,
    delay: float,
    limit: int | None,
) -> None:
    players = load_players(input_path)
    enriched = enrich_players(players, timeout=timeout, delay=delay, limit=limit)
    write_players(output_path, enriched)
    print(f'written={output_path} players={len(enriched)}')


def main() -> None:
    parser = argparse.ArgumentParser(description='players.json の nationality / player_slot_category を補完する')
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('scraper/data/players.json'),
        help='Input players JSON path',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output JSON path (default: overwrite input)',
    )
    parser.add_argument('--timeout', type=int, default=30, help='HTTP timeout seconds')
    parser.add_argument('--delay', type=float, default=0.2, help='Sleep seconds between requests')
    parser.add_argument('--limit', type=int, default=None, help='Process only first N players for test run')
    args = parser.parse_args()

    output_path = args.output or args.input
    run(
        input_path=args.input,
        output_path=output_path,
        timeout=args.timeout,
        delay=args.delay,
        limit=args.limit,
    )


if __name__ == '__main__':
    main()
