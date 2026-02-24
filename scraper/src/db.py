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
    for chunk in _chunked(rows, chunk_size):
        client.table(table_name).upsert(chunk, on_conflict=on_conflict).execute()


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
