#!/usr/bin/env python3
"""Fix GameDateTime in exported JSON by using mapped_date for the date
and keeping the original time (in JST). Produces a new JSON file with
`_original_GameDateTime` metadata for traceability.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


def fix_file(input_path: Path, output_path: Path) -> None:
    payload = json.loads(input_path.read_text(encoding='utf-8'))

    # build schedule_key -> mapped_date candidates map
    # Keep the list of occurrences in JSON iteration order. When a schedule_key
    # appears on multiple days we will prefer a candidate that matches the
    # contexts' original GameDateTime date when fixing.
    rev: dict[int, list[str]] = {}
    for d, keys in payload.get('date_to_schedule_keys', {}).items():
        for k in keys:
            try:
                kk = int(k)
            except Exception:
                continue
            rev.setdefault(kk, []).append(d)

    jst = timezone(timedelta(hours=9))
    fixed_count = 0
    total = 0

    for item in payload.get('games', []):
        total += 1
        game = item.get('game') or {}
        schedule_key = item.get('schedule_key') or game.get('ScheduleKey')
        if schedule_key is None:
            continue
        try:
            sk = int(schedule_key)
        except Exception:
            continue

        candidate_dates = rev.get(sk)
        if not candidate_dates:
            continue

        raw = game.get('GameDateTime')
        if raw is None:
            continue
        try:
            ts = int(raw)
        except Exception:
            # skip non-int values
            continue

        # original JST datetime
        orig_jst = datetime.fromtimestamp(ts, tz=jst)
        orig_date_iso = orig_jst.date().isoformat()

        # Prefer a candidate that matches the contexts' original JST date
        if orig_date_iso in candidate_dates:
            mapped_date = orig_date_iso
        else:
            mapped_date = candidate_dates[0]

        # use mapped_date (YYYY-MM-DD) for date, keep time from orig_jst
        try:
            y, m, d = map(int, mapped_date.split('-'))
            new_jst = datetime(y, m, d, orig_jst.hour, orig_jst.minute, orig_jst.second, tzinfo=jst)
        except Exception:
            continue

        new_ts = int(new_jst.timestamp())

        # store original for traceability
        game['_original_GameDateTime'] = str(ts)
        game['_fixed_GameDateTime_source_mapped_date'] = mapped_date
        game['GameDateTime'] = str(new_ts)
        fixed_count += 1

    # update generated_at
    payload['generated_at'] = datetime.now(timezone.utc).isoformat()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Processed {total} games, fixed {fixed_count} GameDateTime entries')


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print('Usage: fix_game_datetimes.py <input.json> [output.json]')
        return 2
    input_path = Path(argv[1])
    if len(argv) >= 3:
        output_path = Path(argv[2])
    else:
        output_path = input_path.with_name(input_path.stem + '_fixed' + input_path.suffix)

    fix_file(input_path, output_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
