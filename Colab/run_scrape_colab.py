from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from bleague_parallel_scraper import ScrapeOptions, save_date_range_games_parallel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B.League scraper for Google Colab")
    parser.add_argument("--date", type=str, help="Single date: YYYY-MM-DD")
    parser.add_argument("--start-date", type=str, help="Start date: YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="End date: YYYY-MM-DD")
    parser.add_argument("--season", type=str, default="2024-25", help="Season label, e.g. 2024-25")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/content/drive/MyDrive/B_Stats_Site/scraper/data",
        help="Output directory for scraped JSON",
    )
    parser.add_argument(
        "--include-play-by-play",
        action="store_true",
        help="Include play-by-play records",
    )
    parser.add_argument("--max-workers", type=int, default=8, help="Parallel workers for game_detail")
    parser.add_argument("--min-delay-sec", type=float, default=0.2, help="Per-task random minimum delay")
    parser.add_argument("--max-delay-sec", type=float, default=0.8, help="Per-task random maximum delay")
    parser.add_argument("--request-timeout-sec", type=int, default=60, help="HTTP timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=3, help="Retry count for each game_detail request")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.date:
        start = date.fromisoformat(args.date)
        end = start
    elif args.start_date and args.end_date:
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
    elif args.start_date or args.end_date:
        raise SystemExit("Use both --start-date and --end-date together")
    else:
        raise SystemExit("Set either --date or both --start-date and --end-date")

    if start > end:
        raise SystemExit("start date must be less than or equal to end date")

    options = ScrapeOptions(
        include_play_by_play=args.include_play_by_play,
        max_workers=max(1, args.max_workers),
        request_timeout_sec=max(1, args.request_timeout_sec),
        min_delay_sec=max(0.0, args.min_delay_sec),
        max_delay_sec=max(args.min_delay_sec, args.max_delay_sec),
        max_retries=max(1, args.max_retries),
    )

    out = save_date_range_games_parallel(
        start_date=start,
        end_date=end,
        season=args.season,
        output_dir=Path(args.output_dir),
        options=options,
    )

    print(f"Saved JSON: {out}")


if __name__ == "__main__":
    main()
