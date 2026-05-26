#!/usr/bin/env python3
"""Validate issue log markdown filenames under issues/.

Rule:
- Files that start with "Issue" must follow: Issue_ex_###.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ISSUES_DIR = Path("issues")
ISSUE_PREFIX = "Issue"
VALID_NAME_RE = re.compile(r"^Issue_ex_\d{3}\.md$")


def main() -> int:
    if not ISSUES_DIR.exists():
        print("issues/ directory not found; skip validation.")
        return 0

    violations: list[str] = []

    for path in sorted(ISSUES_DIR.glob("*.md")):
        name = path.name
        if not name.startswith(ISSUE_PREFIX):
            continue
        if not VALID_NAME_RE.match(name):
            violations.append(name)

    if violations:
        print("Issue log filename rule violation detected.")
        print("Expected pattern: Issue_ex_###.md")
        print("Invalid filenames:")
        for name in violations:
            print(f"- {name}")
        return 1

    print("Issue log filename validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
