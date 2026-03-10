"""DB接続・INSERT/UPSERT処理"""

from typing import Any
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_SECRET_KEYS


def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SECRET_KEYS:
        raise RuntimeError('SUPABASE_URL / SUPABASE_SECRET_KEYS is not configured')
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEYS)


def upsert_player_stats(data: list[dict[str, Any]]) -> None:
    if not data:
        return
    client = get_client()
    client.table('player_stats').upsert(data).execute()


def upsert_team_stats(data: list[dict[str, Any]]) -> None:
    if not data:
        return
    client = get_client()
    client.table('team_stats').upsert(data).execute()


def upsert_rankings(data: list[dict[str, Any]]) -> None:
    if not data:
        return
    client = get_client()
    client.table('rankings').upsert(data).execute()


def _chunked(items: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    return [items[index:index + chunk_size] for index in range(0, len(items), chunk_size)]


def upsert_rows(
    table_name: str,
    rows: list[dict[str, Any]],
    *,
    on_conflict: str,
    chunk_size: int = 1000,
) -> None:
    if not rows:
        return
    client = get_client()

    def _try_upsert(chunk: list[dict[str, Any]]):
        try:
            client.table(table_name).upsert(chunk, on_conflict=on_conflict).execute()
            return
        except Exception as e:
            # If the chunk is a single row, re-raise with context so caller can inspect
            if len(chunk) <= 1:
                print(f'Upsert failed for single row in {table_name}: {chunk[0]!r} error={e}')
                raise
            # Otherwise, split the chunk and retry halves (binary search) to isolate bad rows
            mid = len(chunk) // 2
            _try_upsert(chunk[:mid])
            _try_upsert(chunk[mid:])

    for chunk in _chunked(rows, chunk_size):
        _try_upsert(chunk)


def upsert_teams(rows: list[dict[str, Any]]) -> None:
    upsert_rows('teams', rows, on_conflict='team_id')


def upsert_games(rows: list[dict[str, Any]]) -> None:
    upsert_rows('games', rows, on_conflict='schedule_key')


def upsert_play_by_play(rows: list[dict[str, Any]]) -> None:
    upsert_rows('play_by_play', rows, on_conflict='schedule_key,sequence_no')


def upsert_game_team_stats(rows: list[dict[str, Any]]) -> None:
    upsert_rows('game_team_stats', rows, on_conflict='schedule_key,team_id')


def upsert_players(rows: list[dict[str, Any]]) -> None:
    upsert_rows('players', rows, on_conflict='player_id')


def upsert_player_game_stats(rows: list[dict[str, Any]]) -> None:
    upsert_rows('player_game_stats', rows, on_conflict='schedule_key,player_id')


def fetch_player_id_map() -> dict[str, str]:
    """player_id_map テーブルから {old_player_id: player_id} のマップを返す。
    テーブルが存在しない場合は空 dict を返す。
    """
    client = get_client()
    try:
        res = client.table('player_id_map').select('old_player_id,player_id').execute()
        return {row['old_player_id']: row['player_id'] for row in (res.data or [])}
    except Exception:
        return {}


def fetch_all_players() -> list[dict[str, Any]]:
    """players テーブルの全レコードを返す。"""
    client = get_client()
    res = client.table('players').select('*').execute()
    return res.data or []
