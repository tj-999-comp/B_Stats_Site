"""Boxscoreの試合通算行から実選手行を判定する。"""

from __future__ import annotations

import re
from typing import Any


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "t", "yes"}


def _has_positive_play_time(value: Any) -> bool:
    normalized = str(value or "").strip()
    match = re.fullmatch(r"(\d+):(\d{2})", normalized)
    if not match:
        return False
    return int(match.group(1)) * 60 + int(match.group(2)) > 0


def is_full_game_total_boxscore(boxscore: dict[str, Any]) -> bool:
    try:
        return int(boxscore.get("PeriodCategory")) == 18
    except (TypeError, ValueError):
        return False


def is_player_total_boxscore(boxscore: dict[str, Any]) -> bool:
    """試合通算の実選手行だけを返す。

    過去データではコーチ等も PeriodCategory=18 で混入するが、
    それらは背番号が空、非出場、非先発、PlayTime=DNP である。
    正規のDNP選手は背番号があるため保持する。
    """
    if not is_full_game_total_boxscore(boxscore):
        return False
    if not _has_text(boxscore.get("PlayerID")):
        return False
    return any(
        (
            _has_text(boxscore.get("PlayerNo")),
            _is_true(boxscore.get("PlayingFlg")),
            _is_true(boxscore.get("StartingFlg")),
            _has_positive_play_time(boxscore.get("PlayTime")),
        )
    )
