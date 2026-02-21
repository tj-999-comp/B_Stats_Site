"""DB接続・INSERT/UPSERT処理"""

from typing import Any
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


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
