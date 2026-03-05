#!/usr/bin/env python3
"""Delete games from Supabase by date range or explicit GameIDs (schedule_key).

Usage examples:
  # dry-run (default) - list matching schedule_keys
  python delete_games_by_date.py --start 2026-01-01 --end 2026-02-15

  # actually delete after confirmation
  python delete_games_by_date.py --start 2026-01-01 --end 2026-02-15 --yes

  # delete explicit ids
  python delete_games_by_date.py --ids 505116,505140 --yes

This script requires environment variables `SUPABASE_URL` and `SUPABASE_SECRET_KEYS`
to be set (the project already loads them via `scraper/src/config.py`).
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, List

from supabase import create_client

from scraper.src.config import SUPABASE_URL, SUPABASE_SECRET_KEYS


def get_client():
    if not SUPABASE_URL or not SUPABASE_SECRET_KEYS:
        raise RuntimeError('SUPABASE_URL / SUPABASE_SECRET_KEYS must be set in environment')
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEYS)


def chunked(iterable: Iterable, size: int) -> Iterable[List]:
    it = list(iterable)
    for i in range(0, len(it), size):
        yield it[i:i + size]


def find_schedule_keys_in_range(client, start_date: str, end_date: str) -> List[int]:
    # Query games where game_date between start_date and end_date (inclusive)
    resp = client.table('games').select('schedule_key,game_date').filter('game_date', 'gte', start_date).filter('game_date', 'lte', end_date).execute()
    if resp.error:
        raise RuntimeError(f'Query error: {resp.error}')
    rows = resp.data or []
    return [int(r['schedule_key']) for r in rows if r.get('schedule_key')]


def delete_by_schedule_keys(client, schedule_keys: List[int], yes: bool = False) -> None:
    if not schedule_keys:
        print('No schedule_keys to delete')
        return

    print(f'Preparing to delete {len(schedule_keys)} schedule_keys')
    sample = schedule_keys[:10]
    print('sample:', sample)

    if not yes:
        resp = input('Proceed with deletion? type YES to confirm: ')
        if resp.strip() != 'YES':
            print('Aborted')
            return

    tables = ['play_by_play', 'player_game_stats', 'game_team_stats', 'games']
    for table in tables:
        print(f'Deleting from {table}...')
        for chunk in chunked(schedule_keys, 100):
            # supabase-py supports in_ operator
            resp = client.table(table).delete().in_('schedule_key', chunk).execute()
            if resp.error:
                print(f'Error deleting chunk from {table}:', resp.error)
            else:
                # resp.count may be unavailable; print ok
                print(f'  deleted chunk size {len(chunk)} from {table}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Delete games from Supabase by date range or GameIDs')
    parser.add_argument('--start', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--end', type=str, help='End date YYYY-MM-DD')
    parser.add_argument('--ids', type=str, help='Comma-separated schedule_key ids to delete')
    parser.add_argument('--yes', action='store_true', help='Confirm deletion without interactive prompt')
    args = parser.parse_args()

    client = get_client()

    schedule_keys: List[int] = []
    if args.ids:
        schedule_keys = [int(x) for x in args.ids.split(',') if x.strip()]
    elif args.start and args.end:
        schedule_keys = find_schedule_keys_in_range(client, args.start, args.end)
    else:
        print('Either --ids or both --start and --end must be provided')
        return 2

    if not schedule_keys:
        print('No matching games found')
        return 0

    delete_by_schedule_keys(client, schedule_keys, yes=args.yes)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
