"""Validate the structure and failure state of a daily scrape JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('payload must be an object')

    required = ('season', 'start_date', 'end_date', 'game_count', 'failed_schedule_keys', 'games')
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f'missing required fields: {missing}')
    if payload['start_date'] != payload['end_date']:
        raise ValueError('daily batch must contain one target date')
    if not isinstance(payload['failed_schedule_keys'], list):
        raise ValueError('failed_schedule_keys must be a list')
    if payload['failed_schedule_keys']:
        raise ValueError(f"failed schedule keys remain: {payload['failed_schedule_keys']}")

    games = payload['games']
    if not isinstance(games, list):
        raise ValueError('games must be a list')
    if payload['game_count'] != len(games):
        raise ValueError(
            f"game_count={payload['game_count']} does not match games={len(games)}"
        )

    schedule_keys: set[int] = set()
    for item in games:
        if not isinstance(item, dict):
            raise ValueError('each game item must be an object')
        raw_key = item.get('schedule_key')
        try:
            schedule_key = int(raw_key)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'invalid schedule_key: {raw_key!r}') from exc
        if schedule_key in schedule_keys:
            raise ValueError(f'duplicate schedule_key: {schedule_key}')
        schedule_keys.add(schedule_key)

        game = item.get('game')
        if not isinstance(game, dict) or not game.get('GameDateTime'):
            raise ValueError(f'schedule_key={schedule_key}: GameDateTime is missing')
        play_by_plays = item.get('play_by_plays', [])
        if play_by_plays:
            raise ValueError(f'schedule_key={schedule_key}: play_by_plays must be empty')

    return {
        'season': payload['season'],
        'target_date': payload['start_date'],
        'game_count': len(games),
        'schedule_keys': sorted(schedule_keys),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='日次取得JSONの構造と失敗状態を検証する')
    parser.add_argument('--input', required=True, type=Path)
    args = parser.parse_args()
    summary = validate_payload(args.input)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
