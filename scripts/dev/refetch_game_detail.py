"""指定したScheduleKeyのgame_detailを詳細データ必須で再取得するCLI。"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.scraping.game_scraper import fetch_game_context


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_tabs(value: str) -> list[str | None]:
    tabs: list[str | None] = []
    for token in value.split(','):
        normalized = token.strip().lower()
        if not normalized:
            continue
        tabs.append(None if normalized == 'default' else token.strip())
    if not tabs:
        raise argparse.ArgumentTypeError('少なくとも1つのtabを指定してください')
    return tabs


def _has_full_detail(result: dict[str, Any]) -> bool:
    return (
        not result.get('error')
        and result.get('source_tab') != 'fallback_html'
        and bool(result.get('game'))
        and bool(result.get('summaries'))
        and bool(result.get('home_boxscores'))
        and bool(result.get('away_boxscores'))
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='指定ScheduleKeyのgame_detailを再取得し、完全な詳細がなければ失敗にする'
    )
    parser.add_argument('--schedule-key', required=True, type=int)
    parser.add_argument('--date', required=True, help='JST候補日 (YYYY-MM-DD)')
    parser.add_argument('--season', required=True, help='記録用のシーズン識別子')
    parser.add_argument(
        '--tabs',
        type=_parse_tabs,
        default=_parse_tabs('4,2,3,1,default'),
        help='試行するtabをカンマ区切りで指定 (default: 4,2,3,1,default)',
    )
    parser.add_argument('--max-retries', type=int, default=8)
    parser.add_argument('--include-play-by-play', action='store_true')
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('/tmp/refetched_game_detail.json'),
        help='再取得結果のJSON出力先',
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.max_retries < 1:
        raise SystemExit('--max-retriesは1以上を指定してください')

    fetch_audit: dict[int, dict[str, Any]] = {}
    result = fetch_game_context(
        args.schedule_key,
        include_play_by_play=args.include_play_by_play,
        max_retries=args.max_retries,
        candidate_dates=[args.date],
        fetch_audit=fetch_audit,
        tab_candidates=args.tabs,
    )
    payload: dict[str, Any] = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'season': args.season,
        'candidate_date': args.date,
        'schedule_key': args.schedule_key,
        'tab_candidates': [tab if tab is not None else 'default' for tab in args.tabs],
        'max_retries': args.max_retries,
        'full_detail': _has_full_detail(result),
        'result': result,
        'fetch_audit': fetch_audit.get(args.schedule_key, {}),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    logger.info(
        'Saved %s: source_tab=%s full_detail=%s',
        args.output,
        result.get('source_tab'),
        payload['full_detail'],
    )
    if not payload['full_detail']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
