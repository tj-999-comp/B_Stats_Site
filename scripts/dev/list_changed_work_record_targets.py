#!/usr/bin/env python3
"""List numbered work-record basenames changed between two commits."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from scripts.dev.validate_work_record_source import parse_metadata


ROOT = Path(__file__).resolve().parents[2]
TARGET_PATH_RE = re.compile(
    r"^work-records/(?:md/|metadata/)?(work_record_[0-9]{3})\.(?:md|yml|html)$"
)


def changed_targets(before: str, after: str, *, publish_only: bool = False) -> list[str]:
    """Return sorted numbered work-record basenames touched by a commit range."""
    if set(before) == {"0"}:
        return []

    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            before,
            after,
            "--",
            "work-records",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    targets = set()
    for path in result.stdout.splitlines():
        match = TARGET_PATH_RE.fullmatch(path)
        if match:
            targets.add(match.group(1))
    selected = sorted(targets)
    if not publish_only:
        return selected

    publishable: list[str] = []
    for target in selected:
        metadata_path = ROOT / "work-records" / "metadata" / f"{target}.yml"
        try:
            metadata = parse_metadata(metadata_path)
        except (OSError, ValueError):
            continue
        if metadata.get("publish") is True:
            publishable.append(target)
    return publishable


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List numbered work-record basenames changed between two commits."
    )
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument(
        "--publish-only",
        action="store_true",
        help="Keep only targets whose current metadata has publish: true.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            changed_targets(args.before, args.after, publish_only=args.publish_only),
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
