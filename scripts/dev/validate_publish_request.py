#!/usr/bin/env python3
"""Validate the work record selected for a manual publish request."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from scripts.dev.validate_work_record_source import parse_metadata


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "B_Stats_Site"
TARGET_BASENAME_RE = re.compile(r"work_record_([0-9]{3})")


def validate_target(target_basename: str) -> tuple[str, Path, Path]:
    match = TARGET_BASENAME_RE.fullmatch(target_basename)
    if match is None or not 1 <= int(match.group(1)) <= 999:
        raise ValueError("target_basename must match work_record_001 through work_record_999")

    records_dir = ROOT / "work-records"
    markdown_path = records_dir / "md" / f"{target_basename}.md"
    metadata_path = records_dir / "metadata" / f"{target_basename}.yml"
    for path in (markdown_path, metadata_path):
        if not path.is_file():
            raise ValueError(f"selected publish file is missing: {path}")

    metadata = parse_metadata(metadata_path)
    if metadata.get("project_id") != PROJECT_ID:
        raise ValueError(f"{metadata_path}: project_id must be {PROJECT_ID}")
    if metadata.get("publish") is not True:
        raise ValueError(f"{metadata_path}: publish must be true for a publish request")
    return PROJECT_ID, markdown_path, metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a manual work-record publish request.")
    parser.add_argument("--target-basename", required=True)
    args = parser.parse_args()

    try:
        project_id, markdown_path, metadata_path = validate_target(args.target_basename)
    except ValueError as error:
        print(f"Publish request validation failed: {error}")
        return 1

    print(
        "Publish request validation passed: "
        f"project_id={project_id} target_basename={args.target_basename} "
        f"files={markdown_path.name},{metadata_path.name} (A-rendered HTML)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
