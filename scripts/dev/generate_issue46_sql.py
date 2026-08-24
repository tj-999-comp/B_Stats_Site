"""Issue #46 のdry-run結果から4本構成のデータパッチSQLを生成する。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.db.upsert_games import (
    _extract_game_team_stats,
    _extract_games,
    _extract_player_game_stats,
    _extract_players,
    _extract_teams,
)
from scripts.dev.dry_run_issue46_games import (
    DEFAULT_MANIFEST,
    REPO_ROOT,
    _load_manifest,
    _season_sort_key,
    _select_games,
)


SQL_DIR = REPO_ROOT / 'supabase/sql'
DATE = '20260824'
ISSUE = 'issue46'
INPUT_PREFIX = f'data_patch_{ISSUE}'
BACKUP_PREFIX = f'data_patch_backup_{DATE}_{ISSUE}'

TABLES = (
    'teams',
    'games',
    'game_team_stats',
    'players',
    'player_game_stats',
)

HISTORY_TABLES = (
    'team_name_history',
    'player_name_history',
    'player_affiliations',
)

TARGET_EXTRAS = {
    'teams': {'created_at', 'updated_at'},
    'games': {'scraped_at', 'created_at', 'updated_at'},
    'game_team_stats': {
        'dunks',
        'ft_d_pct',
        'perimeter_pts_pct',
        'live_tov_pct',
        'dead_tov_pct',
        'live_tov_share',
        'dead_tov_share',
        'off_success_count',
        'or_chances',
        'dr_chances',
        'tom',
        'vps',
        'home_efg_pct',
        'away_efg_pct',
        'home_ts_pct',
        'away_ts_pct',
        'home_off_rtg',
        'away_off_rtg',
        'pythagorean_win_pct',
        'opp_success_count',
        'opp_ft_d_pct',
        'opp_ft_rate',
        'opp_perimeter_pts_pct',
        'opp_vps',
        'home_opp_efg_pct',
        'away_opp_efg_pct',
        'home_opp_ts_pct',
        'away_opp_ts_pct',
        'created_at',
        'updated_at',
    },
    'players': {
        'player_slot_category',
        'league_registered_nationality',
        'birthplace',
        'old_player_id',
        'entity_type',
        'created_at',
        'updated_at',
        'batch_order',
    },
    'player_game_stats': {'created_at', 'updated_at'},
}

NUMERIC_TYPES = {
    'game_team_stats': {
        **{column: 'NUMERIC(8, 4)' for column in (
            'fg_pct', 'fg2_pct', 'fg3_pct', 'ft_pct', 'efg_pct', 'ts_pct',
            'ast_pct', 'tov_pct', 'play_pct', 'ft_d_pct', 'ft_freq', 'ft_rate',
            'orb_pct', 'drb_pct', 'pft_pct', 'fbp_pct', 'scp_pct', 'pitp_pct',
            'perimeter_pts_pct', 'pt2_attempt_pct', 'pt3_attempt_pct',
            'pt2_points_share', 'pt3_points_share', 'ft_points_share',
            'live_tov_pct', 'dead_tov_pct', 'live_tov_share', 'dead_tov_share',
            'home_efg_pct', 'away_efg_pct', 'home_ts_pct', 'away_ts_pct',
            'pythagorean_win_pct', 'opp_efg_pct', 'opp_ts_pct', 'opp_fg2_pct',
            'opp_fg3_pct', 'opp_pt2_attempt_pct', 'opp_pt3_attempt_pct',
            'opp_pt2_points_share', 'opp_pt3_points_share', 'opp_ft_points_share',
            'opp_ast_pct', 'opp_tov_pct', 'opp_orb_pct', 'opp_drb_pct',
            'opp_ft_d_pct', 'opp_ft_rate', 'opp_fbp_pct', 'opp_scp_pct',
            'opp_pitp_pct', 'opp_perimeter_pts_pct', 'opp_pft_pct',
            'home_opp_efg_pct', 'away_opp_efg_pct', 'home_opp_ts_pct',
            'away_opp_ts_pct',
        )},
        **{column: 'NUMERIC(10, 4)' for column in (
            'possession', 'pace', 'off_rtg', 'def_rtg', 'net_rtg', 'ast_rtg',
            'tov_rtg', 'pft_rtg', 'scp_rtg', 'ast_tov_ratio', 'shot_chances',
            'off_success_count', 'or_chances', 'dr_chances', 'tom', 'eff', 'vps',
            'home_off_rtg', 'away_off_rtg', 'opp_possession',
            'opp_ast_tov_ratio', 'opp_ast_rtg', 'opp_shot_chances',
            'opp_success_count', 'opp_scp_rtg', 'opp_pft_rtg', 'opp_vps',
        )},
    },
    'player_game_stats': {
        column: 'NUMERIC(8, 4)' for column in (
            'fg_pct', 'fg2_pct', 'fg3_pct', 'ft_pct', 'ast_to_ratio', 'efg_pct',
            'ts_pct', 'usg_pct',
        )
    },
}


def _game_sort_key(item: dict[str, Any]) -> tuple[int, int]:
    game = item.get('game', {})
    raw_datetime = game.get('GameDateTime')
    try:
        game_datetime = int(raw_datetime)
    except (TypeError, ValueError):
        game_datetime = 2**63 - 1
    raw_schedule_key = item.get('schedule_key') or game.get('ScheduleKey')
    try:
        schedule_key = int(raw_schedule_key)
    except (TypeError, ValueError):
        schedule_key = 2**63 - 1
    return game_datetime, schedule_key


def _collect_rows() -> dict[str, list[dict[str, Any]]]:
    manifest_rows = _load_manifest(DEFAULT_MANIFEST)
    selected_by_season = _select_games(manifest_rows)

    teams_by_id: dict[str, dict[str, Any]] = {}
    games: list[dict[str, Any]] = []
    game_team_stats: list[dict[str, Any]] = []
    players: list[dict[str, Any]] = []
    player_game_stats: list[dict[str, Any]] = []

    for batch_order, season in enumerate(
        sorted(selected_by_season, key=_season_sort_key)
    ):
        payload = {
            'season': season,
            'games': sorted(selected_by_season[season], key=_game_sort_key),
        }
        for team in _extract_teams(payload):
            teams_by_id[team['team_id']] = team
        games.extend(_extract_games(payload))
        game_team_stats.extend(_extract_game_team_stats(payload))
        players.extend(
            {**player, 'batch_order': batch_order}
            for player in _extract_players(payload)
        )
        player_game_stats.extend(_extract_player_game_stats(payload))

    rows = {
        'teams': list(teams_by_id.values()),
        'games': games,
        'game_team_stats': game_team_stats,
        'players': players,
        'player_game_stats': player_game_stats,
    }

    expected = {
        'teams': len(rows['teams']),
        'games': 40,
        'game_team_stats': 78,
        'players': 687,
        'player_game_stats': 917,
    }
    actual = {table: len(table_rows) for table, table_rows in rows.items()}
    if actual != expected:
        raise ValueError(f'変換件数が想定外です: expected={expected} actual={actual}')

    if len({row['schedule_key'] for row in rows['games']}) != 40:
        raise ValueError('gamesのschedule_keyが重複しています')
    if len({(row['schedule_key'], row['team_id']) for row in rows['game_team_stats']}) != 78:
        raise ValueError('game_team_statsの主キーが重複しています')
    if len({(row['schedule_key'], row['player_id']) for row in rows['player_game_stats']}) != 917:
        raise ValueError('player_game_statsのdry-run主キーが重複しています')

    return rows


def _sql_literal(value: Any) -> str:
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def _column_type(table: str, column: str, values: list[Any]) -> str:
    if column in NUMERIC_TYPES.get(table, {}):
        return NUMERIC_TYPES[table][column]
    non_null = [value for value in values if value is not None]
    if column in {'team_id', 'player_id', 'opponent_team_id'}:
        return 'TEXT'
    if column in {'is_home', 'is_starter', 'is_playing', 'game_ended_flg', 'record_fixed_flg', 'boxscore_exists_flg', 'play_by_play_exists_flg'}:
        return 'BOOLEAN'
    if column in {'schedule_key', 'game_datetime_unix', 'referee_id', 'sub_referee_id_1', 'sub_referee_id_2'}:
        return 'BIGINT'
    if column == 'setu':
        return 'TEXT'
    if column in {'max_period', 'game_current_period', 'source_tab', 'home_team_score_q1', 'home_team_score_q2', 'home_team_score_q3', 'home_team_score_q4', 'home_team_score_q5', 'away_team_score_q1', 'away_team_score_q2', 'away_team_score_q3', 'away_team_score_q4', 'away_team_score_q5'}:
        return 'SMALLINT'
    if column == 'batch_order':
        return 'INTEGER'
    if any(isinstance(value, float) for value in non_null):
        return 'NUMERIC'
    if non_null and all(isinstance(value, int) and not isinstance(value, bool) for value in non_null):
        return 'INTEGER'
    return 'TEXT'


def _create_input_table(table: str, rows: list[dict[str, Any]]) -> str:
    columns = list(rows[0])
    definitions = ',\n'.join(
        f'    {column} {_column_type(table, column, [row.get(column) for row in rows])}'
        for column in columns
    )
    values = ',\n'.join(
        '    (' + ', '.join(_sql_literal(row.get(column)) for column in columns) + ')'
        for row in rows
    )
    table_name = f'{INPUT_PREFIX}_{table}'
    return f"""CREATE TABLE public.{table_name} (
{definitions}
);

INSERT INTO public.{table_name} ({', '.join(columns)}) VALUES
{values};
"""


def _regclass_guard(table_names: list[str]) -> str:
    checks = '\n       OR '.join(
        f"TO_REGCLASS('public.{name}') IS NOT NULL" for name in table_names
    )
    return f"""    IF {checks} THEN
        RAISE EXCEPTION 'Issue #46 input or backup table already exists; inspect before re-running';
    END IF;
"""


def _backup_ctas(table: str) -> str:
    input_table = f'{INPUT_PREFIX}_{table}'
    backup_table = f'{BACKUP_PREFIX}_{table}'
    key = 'team_id' if table == 'teams' else 'schedule_key'
    return f"""    CREATE TABLE public.{backup_table} AS
        SELECT * FROM public.{table} WHERE FALSE;
    INSERT INTO public.{backup_table}
    SELECT live.*
      FROM public.{table} live
     WHERE live.{key} IN (SELECT {key} FROM public.{input_table});
"""


def _player_backup_ctas() -> str:
    return f"""    CREATE TABLE public.{BACKUP_PREFIX}_players AS
        SELECT * FROM public.players WHERE FALSE;
    INSERT INTO public.{BACKUP_PREFIX}_players
    SELECT live.*
      FROM public.players live
     WHERE live.player_id IN (SELECT player_id FROM issue46_backup_player_ids);

    CREATE TABLE public.{BACKUP_PREFIX}_player_name_history AS
        SELECT * FROM public.player_name_history WHERE FALSE;
    INSERT INTO public.{BACKUP_PREFIX}_player_name_history
    SELECT live.*
      FROM public.player_name_history live
     WHERE live.player_id IN (SELECT player_id FROM issue46_backup_player_ids);

    CREATE TABLE public.{BACKUP_PREFIX}_player_affiliations AS
        SELECT * FROM public.player_affiliations WHERE FALSE;
    INSERT INTO public.{BACKUP_PREFIX}_player_affiliations
    SELECT live.*
      FROM public.player_affiliations live
     WHERE live.player_id IN (SELECT player_id FROM issue46_backup_player_ids);
"""


def _player_id_map_backup_ctas() -> str:
    return f"""    CREATE TABLE public.{BACKUP_PREFIX}_player_id_map AS
        SELECT * FROM public.player_id_map WHERE FALSE;
    INSERT INTO public.{BACKUP_PREFIX}_player_id_map
    SELECT live.*
      FROM public.player_id_map live
     WHERE live.old_player_id IN (
         SELECT DISTINCT player_id FROM public.{INPUT_PREFIX}_players
     );
"""


def _team_history_backup_ctas() -> str:
    return f"""    CREATE TABLE public.{BACKUP_PREFIX}_team_name_history AS
        SELECT * FROM public.team_name_history WHERE FALSE;
    INSERT INTO public.{BACKUP_PREFIX}_team_name_history
    SELECT live.*
      FROM public.team_name_history live
     WHERE live.team_id IN (SELECT team_id FROM public.{INPUT_PREFIX}_teams);
"""


def _json_strip(alias: str, columns: set[str]) -> str:
    expression = f'to_jsonb({alias})'
    for column in sorted(columns):
        expression += f" - '{column}'"
    return expression


def _player_mapped_cte(
    *,
    source_alias: str = 'i',
    map_table: str = 'public.player_id_map',
) -> str:
    return f"""WITH mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, {source_alias}.player_id))
           COALESCE(m.player_id, {source_alias}.player_id) AS player_id,
           {source_alias}.player_name_j,
           {source_alias}.player_name_e,
           {source_alias}.last_seen_team_id,
           {source_alias}.last_seen_jersey_number
      FROM public.{INPUT_PREFIX}_players {source_alias}
      LEFT JOIN {map_table} m
        ON m.old_player_id = {source_alias}.player_id
     ORDER BY COALESCE(m.player_id, {source_alias}.player_id), {source_alias}.batch_order DESC
)"""


def _upsert_sql(
    table: str,
    columns: list[str],
    *,
    mapped_players: bool = False,
    map_table: str = 'public.player_id_map',
) -> str:
    input_table = f'public.{INPUT_PREFIX}_{table}'
    target_columns = ', '.join(columns)
    update_columns = [column for column in columns if column not in {'team_id', 'player_id', 'schedule_key'}]
    if table == 'players':
        return f"""    {_player_mapped_cte(map_table=map_table)}
    INSERT INTO public.players (player_id, player_name_j, player_name_e, last_seen_team_id, last_seen_jersey_number)
    SELECT player_id, player_name_j, player_name_e, last_seen_team_id, last_seen_jersey_number
      FROM mapped_players
    ON CONFLICT (player_id) DO UPDATE SET
        player_name_j = EXCLUDED.player_name_j,
        player_name_e = EXCLUDED.player_name_e,
        last_seen_team_id = EXCLUDED.last_seen_team_id,
        last_seen_jersey_number = EXCLUDED.last_seen_jersey_number,
        updated_at = NOW();
"""
    select = f'SELECT {target_columns} FROM {input_table}'
    order = ''
    if table == 'player_game_stats':
        select = (
            f"SELECT i.{', i.'.join(columns[:-1])}, "
            f"COALESCE(m.player_id, i.player_id) AS player_id"
        )
        # player_id is the second column in this table; rebuild the select explicitly.
        select_columns = [
            'i.schedule_key',
            'COALESCE(m.player_id, i.player_id) AS player_id',
            *[f'i.{column}' for column in columns if column not in {'schedule_key', 'player_id'}],
        ]
        select = 'SELECT ' + ', '.join(select_columns)
        select += f' FROM {input_table} i LEFT JOIN {map_table} m ON m.old_player_id = i.player_id'
        order = (
            ' ORDER BY (SELECT g.game_datetime_unix FROM public.games g '
            'WHERE g.schedule_key = i.schedule_key) NULLS LAST, '
            'i.schedule_key, COALESCE(m.player_id, i.player_id)'
        )
    elif table == 'game_team_stats':
        order = ' ORDER BY schedule_key, team_id'
    update = ',\n        '.join(
        f'{column} = EXCLUDED.{column}' for column in update_columns
    )
    if update:
        update += ',\n        updated_at = NOW()'
    conflict_columns = (
        ['schedule_key', 'player_id']
        if table == 'player_game_stats'
        else [column for column in ('schedule_key', 'team_id', 'player_id') if column in columns]
    )
    return f"""    INSERT INTO public.{table} ({target_columns})
    {select}{order}
    ON CONFLICT ({', '.join(conflict_columns)}) DO UPDATE SET
        {update};
"""


def _generate_backup(rows: dict[str, list[dict[str, Any]]]) -> str:
    input_tables = [f'{INPUT_PREFIX}_{table}' for table in TABLES]
    backup_tables = [f'{BACKUP_PREFIX}_{table}' for table in TABLES]
    all_tables = input_tables + backup_tables + [
        f'{BACKUP_PREFIX}_player_id_map',
        f'{BACKUP_PREFIX}_team_name_history',
        f'{BACKUP_PREFIX}_player_name_history',
        f'{BACKUP_PREFIX}_player_affiliations',
        f'{BACKUP_PREFIX}_meta',
    ]
    input_sql = '\n'.join(_create_input_table(table, rows[table]) for table in TABLES)
    backup_sql = '\n'.join(
        _backup_ctas(table)
        for table in ('teams', 'games', 'game_team_stats', 'player_game_stats')
    )
    return f"""-- Issue #46: 欠落B1試合40件のUpsert用入力固定・バックアップ
-- 作成日: {DATE}
-- 実行順: 本SQL → verify（PRE_FIX）→ fix → verify（POST_FIX）
-- 対象: 40 games / 78 game_team_stats / 917 player_game_stats
-- 注意: live DBへの変更はバックアップ表と入力表の作成だけ。既存オブジェクトがあれば停止する。

DO $issue_46_backup$
BEGIN
{_regclass_guard(all_tables)}
    CREATE TABLE public.{BACKUP_PREFIX}_meta (
        issue_name TEXT PRIMARY KEY,
        captured_at TIMESTAMPTZ NOT NULL
    );
    INSERT INTO public.{BACKUP_PREFIX}_meta (issue_name, captured_at)
    VALUES ('Issue #46', CLOCK_TIMESTAMP());

{input_sql}
{_player_id_map_backup_ctas()}
    CREATE TEMP TABLE issue46_backup_player_ids (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue46_backup_player_ids (player_id)
    SELECT DISTINCT COALESCE(m.player_id, i.player_id)
      FROM public.{INPUT_PREFIX}_players i
      LEFT JOIN public.player_id_map m ON m.old_player_id = i.player_id;

{backup_sql}
{_player_backup_ctas()}
{_team_history_backup_ctas()}

    IF (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_teams) <> {len(rows['teams'])}
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_games) <> 40
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_game_team_stats) <> 78
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_players) <> 687
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_player_game_stats) <> 917 THEN
        RAISE EXCEPTION 'Issue #46 input row-count guard failed';
    END IF;
END;
$issue_46_backup$;

SELECT 'input_teams' AS item, COUNT(*) AS row_count FROM public.{INPUT_PREFIX}_teams
UNION ALL SELECT 'input_games', COUNT(*) FROM public.{INPUT_PREFIX}_games
UNION ALL SELECT 'input_game_team_stats', COUNT(*) FROM public.{INPUT_PREFIX}_game_team_stats
UNION ALL SELECT 'input_players_raw', COUNT(*) FROM public.{INPUT_PREFIX}_players
UNION ALL SELECT 'input_player_game_stats', COUNT(*) FROM public.{INPUT_PREFIX}_player_game_stats
UNION ALL SELECT 'backup_teams', COUNT(*) FROM public.{BACKUP_PREFIX}_teams
UNION ALL SELECT 'backup_games', COUNT(*) FROM public.{BACKUP_PREFIX}_games
UNION ALL SELECT 'backup_game_team_stats', COUNT(*) FROM public.{BACKUP_PREFIX}_game_team_stats
UNION ALL SELECT 'backup_players', COUNT(*) FROM public.{BACKUP_PREFIX}_players
UNION ALL SELECT 'backup_player_game_stats', COUNT(*) FROM public.{BACKUP_PREFIX}_player_game_stats
UNION ALL SELECT 'backup_player_id_map', COUNT(*) FROM public.{BACKUP_PREFIX}_player_id_map
UNION ALL SELECT 'backup_team_name_history', COUNT(*) FROM public.{BACKUP_PREFIX}_team_name_history
UNION ALL SELECT 'backup_player_name_history', COUNT(*) FROM public.{BACKUP_PREFIX}_player_name_history
UNION ALL SELECT 'backup_player_affiliations', COUNT(*) FROM public.{BACKUP_PREFIX}_player_affiliations;
"""


def _pre_fix_guard(
    table: str,
    key_columns: list[str],
    *,
    scope_column: str,
) -> str:
    input_table = f'public.{INPUT_PREFIX}_{table}'
    backup_table = f'{BACKUP_PREFIX}_{table}'
    join = ' AND '.join(
        f'live.{column} = backup.{column}' for column in key_columns
    )
    backup_key_match = ' AND '.join(
        f'backup.{column} = live.{column}' for column in key_columns
    )
    return f"""    SELECT COUNT(*) INTO n
      FROM public.{table} live
      JOIN public.{backup_table} backup ON {join}
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION '{table} changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.{backup_table} backup
     WHERE NOT EXISTS (
           SELECT 1 FROM public.{table} live WHERE {join}
       );
    IF n <> 0 THEN
        RAISE EXCEPTION '{table} rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.{table} live
     WHERE live.{scope_column} IN (SELECT {scope_column} FROM {input_table})
       AND NOT EXISTS (
           SELECT 1 FROM public.{backup_table} backup WHERE {backup_key_match}
       );
    IF n <> 0 THEN
        RAISE EXCEPTION '{table} contains rows not present in backup: % rows', n;
    END IF;
"""


def _history_pre_fix_guard(*, map_table: str) -> str:
    player_scope = (
        f"SELECT DISTINCT COALESCE(m.player_id, i.player_id) "
        f"FROM public.{INPUT_PREFIX}_players i "
        f"LEFT JOIN {map_table} m ON m.old_player_id = i.player_id"
    )
    checks = (
        (
            'team_name_history', 'history_id', 'team_id',
            f'SELECT team_id FROM public.{INPUT_PREFIX}_teams',
        ),
        ('player_name_history', 'history_id', 'player_id', player_scope),
        ('player_affiliations', 'affiliation_id', 'player_id', player_scope),
    )
    statements: list[str] = []
    for table, id_column, scope_column, scope_query in checks:
        backup_table = f'{BACKUP_PREFIX}_{table}'
        statements.append(
            f"""    SELECT COUNT(*) INTO n
      FROM public.{table} live
      JOIN public.{backup_table} backup ON live.{id_column} = backup.{id_column}
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION '{table} changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.{backup_table} backup
     WHERE NOT EXISTS (
         SELECT 1 FROM public.{table} live WHERE live.{id_column} = backup.{id_column}
     );
    IF n <> 0 THEN
        RAISE EXCEPTION '{table} rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.{table} live
     WHERE live.{scope_column} IN ({scope_query})
       AND NOT EXISTS (
           SELECT 1 FROM public.{backup_table} backup WHERE backup.{id_column} = live.{id_column}
       );
    IF n <> 0 THEN
        RAISE EXCEPTION '{table} contains rows not present in backup: % rows', n;
    END IF;
"""
        )
    return ''.join(statements)


def _post_mismatch(
    table: str,
    key_columns: list[str],
    *,
    map_table: str = 'public.player_id_map',
) -> str:
    input_table = f'public.{INPUT_PREFIX}_{table}'
    extras = TARGET_EXTRAS[table]
    join = ' AND '.join(f'live.{column} = input.{column}' for column in key_columns)
    current = _json_strip('live', extras)
    expected = _json_strip('input', set())
    if table == 'players':
        raise ValueError('players uses a dedicated post mismatch expression')
    if table == 'games':
        return f"""SELECT COUNT(*) AS mismatch_rows
  FROM {input_table} input
  LEFT JOIN public.{table} live ON live.schedule_key = input.schedule_key
 WHERE live.schedule_key IS NULL
    OR {current} IS DISTINCT FROM
       ({expected} || jsonb_build_object('setu', input.setu::TEXT))"""
    if table == 'player_game_stats':
        return f"""SELECT COUNT(*) AS mismatch_rows
  FROM (
      SELECT i.*, COALESCE(m.player_id, i.player_id) AS mapped_player_id
        FROM {input_table} i
        LEFT JOIN {map_table} m ON m.old_player_id = i.player_id
  ) input
  LEFT JOIN public.{table} live
    ON live.schedule_key = input.schedule_key
   AND live.player_id = input.mapped_player_id
 WHERE live.schedule_key IS NULL
    OR to_jsonb(live) - 'created_at' - 'updated_at' IS DISTINCT FROM
       ((to_jsonb(input) - 'mapped_player_id') || jsonb_build_object('player_id', input.mapped_player_id))"""
    return f"""SELECT COUNT(*) AS mismatch_rows
  FROM {input_table} input
  LEFT JOIN public.{table} live ON {join}
 WHERE live.{key_columns[0]} IS NULL
    OR {current} IS DISTINCT FROM {expected}"""


def _players_post_mismatch(*, map_table: str = 'public.player_id_map') -> str:
    return f"""WITH mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, i.player_id))
           COALESCE(m.player_id, i.player_id) AS player_id,
           i.player_name_j,
           i.player_name_e,
           i.last_seen_team_id,
           i.last_seen_jersey_number
      FROM public.{INPUT_PREFIX}_players i
      LEFT JOIN {map_table} m ON m.old_player_id = i.player_id
     ORDER BY COALESCE(m.player_id, i.player_id), i.batch_order DESC
)
SELECT COUNT(*) AS mismatch_rows
  FROM mapped_players input
  LEFT JOIN public.players live USING (player_id)
 WHERE live.player_id IS NULL
    OR (to_jsonb(live) - ARRAY['batch_order', 'player_slot_category', 'league_registered_nationality', 'birthplace', 'old_player_id', 'entity_type', 'created_at', 'updated_at']::text[])
       IS DISTINCT FROM to_jsonb(input)"""


def _mapped_player_stats_cte() -> str:
    return f"""WITH mapped_stats AS (
    SELECT i.*,
           COALESCE(m.player_id, i.player_id) AS mapped_player_id
      FROM public.{INPUT_PREFIX}_player_game_stats i
      LEFT JOIN public.player_id_map m ON m.old_player_id = i.player_id
)"""


def _generate_fix(rows: dict[str, list[dict[str, Any]]]) -> str:
    columns = {table: list(rows[table][0]) for table in TABLES}
    fixed_map = f'public.{BACKUP_PREFIX}_player_id_map'
    all_tables = [f'{INPUT_PREFIX}_{table}' for table in TABLES]
    all_tables += [f'{BACKUP_PREFIX}_{table}' for table in TABLES]
    all_tables += [
        f'{BACKUP_PREFIX}_player_id_map',
        f'{BACKUP_PREFIX}_team_name_history',
        f'{BACKUP_PREFIX}_player_name_history',
        f'{BACKUP_PREFIX}_player_affiliations',
        f'{BACKUP_PREFIX}_meta',
    ]
    guard = _regclass_guard([]).replace(
        "IF  THEN", 'IF '
    )
    guard = '    IF ' + '\n       OR '.join(
        f"TO_REGCLASS('public.{name}') IS NULL" for name in all_tables
    ) + " THEN\n        RAISE EXCEPTION 'Issue #46 input or backup table is missing';\n    END IF;\n"
    pre_guard = (
        _pre_fix_guard('teams', ['team_id'], scope_column='team_id')
        + _pre_fix_guard('games', ['schedule_key'], scope_column='schedule_key')
        + _pre_fix_guard(
            'game_team_stats', ['schedule_key', 'team_id'], scope_column='schedule_key'
        )
        + _pre_fix_guard(
            'player_game_stats', ['schedule_key', 'player_id'], scope_column='schedule_key'
        )
        + _history_pre_fix_guard(map_table=fixed_map)
    )
    teams_upsert = _upsert_sql('teams', columns['teams'])
    games_upsert = _upsert_sql('games', columns['games'])
    players_upsert = _upsert_sql(
        'players', columns['players'], mapped_players=True, map_table=fixed_map
    )
    game_stats_upsert = _upsert_sql('game_team_stats', columns['game_team_stats'])
    player_stats_upsert = _upsert_sql(
        'player_game_stats', columns['player_game_stats'],
        mapped_players=True, map_table=fixed_map,
    )
    return f"""-- Issue #46: 欠落B1試合40件のUpsert
-- 作成日: {DATE}
-- 実行順: backup → verify（PRE_FIX）→ 本SQL → verify（POST_FIX）
-- 注意: live DBを変更する。接続先、backup結果、verify（PRE_FIX）を確認してから実行する。
-- play_by_playは対象外。

BEGIN;

DO $issue_46_fix$
DECLARE
    n BIGINT;
    expected_players BIGINT;
BEGIN
{guard}
    IF (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_teams) <> {len(rows['teams'])}
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_games) <> 40
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_game_team_stats) <> 78
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_players) <> 687
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_player_game_stats) <> 917 THEN
        RAISE EXCEPTION 'Issue #46 input row-count guard failed';
    END IF;

    {_player_mapped_cte(map_table=fixed_map)}
    SELECT COUNT(*) INTO expected_players FROM mapped_players;
    IF EXISTS (
        SELECT 1
          FROM public.{INPUT_PREFIX}_player_game_stats i
          LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
         GROUP BY i.schedule_key, COALESCE(m.player_id, i.player_id)
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Issue #46 player_game_stats primary-key conflict after player_id_map';
    END IF;

{pre_guard}
{teams_upsert}
{games_upsert}
{players_upsert}
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n <> expected_players THEN
        RAISE EXCEPTION 'Issue #46 players upsert row-count mismatch: % <> %', n, expected_players;
    END IF;
{game_stats_upsert}
{player_stats_upsert}
END;
$issue_46_fix$;

SELECT 'games' AS item, COUNT(*) AS row_count
  FROM public.games g JOIN public.{INPUT_PREFIX}_games i USING (schedule_key)
UNION ALL SELECT 'game_team_stats', COUNT(*)
  FROM public.game_team_stats s JOIN public.{INPUT_PREFIX}_game_team_stats i
    USING (schedule_key, team_id)
UNION ALL SELECT 'player_game_stats', COUNT(*)
  FROM public.player_game_stats s
  JOIN public.{INPUT_PREFIX}_player_game_stats i
    ON s.schedule_key = i.schedule_key
  LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
 WHERE s.player_id = COALESCE(m.player_id, i.player_id);

COMMIT;
"""


def _generate_verify(rows: dict[str, list[dict[str, Any]]]) -> str:
    fixed_map = f'public.{BACKUP_PREFIX}_player_id_map'
    all_tables = [f'{INPUT_PREFIX}_{table}' for table in TABLES]
    all_tables += [f'{BACKUP_PREFIX}_{table}' for table in TABLES]
    all_tables += [
        f'{BACKUP_PREFIX}_player_id_map',
        f'{BACKUP_PREFIX}_team_name_history',
        f'{BACKUP_PREFIX}_player_name_history',
        f'{BACKUP_PREFIX}_player_affiliations',
        f'{BACKUP_PREFIX}_meta',
    ]
    guard = '    IF ' + '\n       OR '.join(
        f"TO_REGCLASS('public.{name}') IS NULL" for name in all_tables
    ) + " THEN\n        RAISE EXCEPTION 'Issue #46 input or backup table is missing';\n    END IF;\n"
    return f"""-- Issue #46: 欠落B1試合Upsertの実行前・実行後・ロールバック後検証
-- 作成日: {DATE}
-- 実行順: backup後（PRE_FIX）、fix後（POST_FIX）、rollback後（ROLLED_BACK）に同じSQLを実行する。
-- このSQLはpublicテーブルを変更しない。

BEGIN;

DO $issue_46_verify_guard$
BEGIN
{guard}
    IF (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_teams) <> {len(rows['teams'])}
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_games) <> 40
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_game_team_stats) <> 78
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_players) <> 687
       OR (SELECT COUNT(*) FROM public.{INPUT_PREFIX}_player_game_stats) <> 917 THEN
        RAISE EXCEPTION 'Issue #46 input row-count guard failed';
    END IF;
END;
$issue_46_verify_guard$;

WITH pre AS (
    SELECT 'teams' AS table_name,
           (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_teams) AS backup_rows,
           (SELECT COUNT(*) FROM public.teams t JOIN public.{INPUT_PREFIX}_teams i USING (team_id)) AS current_rows,
           (SELECT COUNT(*) FROM public.teams t JOIN public.{BACKUP_PREFIX}_teams b USING (team_id)
             WHERE to_jsonb(t) IS DISTINCT FROM to_jsonb(b)) AS backup_value_mismatches,
           (SELECT COUNT(*) FROM public.teams t JOIN public.{INPUT_PREFIX}_teams i USING (team_id)
             WHERE NOT EXISTS (SELECT 1 FROM public.{BACKUP_PREFIX}_teams b WHERE b.team_id = t.team_id)) AS new_rows
    UNION ALL
    SELECT 'players',
           (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_players),
           (SELECT COUNT(*) FROM public.players p JOIN public.{BACKUP_PREFIX}_players b USING (player_id)),
           (SELECT COUNT(*) FROM public.players p JOIN public.{BACKUP_PREFIX}_players b USING (player_id)
             WHERE to_jsonb(p) IS DISTINCT FROM to_jsonb(b)),
           (SELECT COUNT(*) FROM public.players p
             WHERE p.player_id IN (
                 SELECT DISTINCT COALESCE(m.player_id, i.player_id)
                   FROM public.{INPUT_PREFIX}_players i
                   LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
             )
               AND NOT EXISTS (SELECT 1 FROM public.{BACKUP_PREFIX}_players b WHERE b.player_id = p.player_id))
    UNION ALL
    SELECT 'games' AS table_name,
           (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_games) AS backup_rows,
           (SELECT COUNT(*) FROM public.games g JOIN public.{INPUT_PREFIX}_games i USING (schedule_key)) AS current_rows,
           (SELECT COUNT(*) FROM public.games g JOIN public.{BACKUP_PREFIX}_games b USING (schedule_key)
             WHERE to_jsonb(g) IS DISTINCT FROM to_jsonb(b)) AS backup_value_mismatches,
           (SELECT COUNT(*) FROM public.games g JOIN public.{INPUT_PREFIX}_games i USING (schedule_key)
             WHERE NOT EXISTS (SELECT 1 FROM public.{BACKUP_PREFIX}_games b WHERE b.schedule_key = g.schedule_key)) AS new_rows
    UNION ALL
    SELECT 'game_team_stats',
           (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_game_team_stats),
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.{INPUT_PREFIX}_game_team_stats i USING (schedule_key, team_id)),
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.{BACKUP_PREFIX}_game_team_stats b USING (schedule_key, team_id)
             WHERE to_jsonb(g) IS DISTINCT FROM to_jsonb(b)),
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.{INPUT_PREFIX}_game_team_stats i USING (schedule_key, team_id)
             WHERE NOT EXISTS (SELECT 1 FROM public.{BACKUP_PREFIX}_game_team_stats b WHERE b.schedule_key = g.schedule_key AND b.team_id = g.team_id))
    UNION ALL
    SELECT 'player_game_stats',
           (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_player_game_stats),
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.{INPUT_PREFIX}_player_game_stats i
              ON g.schedule_key = i.schedule_key
             LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
            WHERE g.player_id = COALESCE(m.player_id, i.player_id)),
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.{BACKUP_PREFIX}_player_game_stats b USING (schedule_key, player_id)
             WHERE to_jsonb(g) IS DISTINCT FROM to_jsonb(b)),
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.{INPUT_PREFIX}_player_game_stats i
              ON g.schedule_key = i.schedule_key
             LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
            WHERE g.player_id = COALESCE(m.player_id, i.player_id)
              AND NOT EXISTS (SELECT 1 FROM public.{BACKUP_PREFIX}_player_game_stats b WHERE b.schedule_key = g.schedule_key AND b.player_id = g.player_id))
), post AS (
    SELECT 'teams' AS table_name,
           {len(rows['teams'])}::BIGINT AS expected_rows,
           (SELECT COUNT(*) FROM public.teams t JOIN public.{INPUT_PREFIX}_teams i USING (team_id)) AS current_rows,
           ({_post_mismatch('teams', ['team_id'])}) AS value_mismatches
    UNION ALL
    SELECT 'games' AS table_name,
           40::BIGINT AS expected_rows,
           (SELECT COUNT(*) FROM public.games g JOIN public.{INPUT_PREFIX}_games i USING (schedule_key)) AS current_rows,
           ({_post_mismatch('games', ['schedule_key'], map_table=fixed_map)}) AS value_mismatches
    UNION ALL
    SELECT 'game_team_stats',
           78,
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.{INPUT_PREFIX}_game_team_stats i USING (schedule_key, team_id)),
           ({_post_mismatch('game_team_stats', ['schedule_key', 'team_id'], map_table=fixed_map)})
    UNION ALL
    SELECT 'player_game_stats',
           917,
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.{INPUT_PREFIX}_player_game_stats i
              ON g.schedule_key = i.schedule_key
             LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
            WHERE g.player_id = COALESCE(m.player_id, i.player_id)),
           ({_post_mismatch('player_game_stats', ['schedule_key', 'mapped_player_id'], map_table=fixed_map)})
), mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, i.player_id))
           COALESCE(m.player_id, i.player_id) AS player_id,
           i.player_name_j, i.player_name_e, i.last_seen_team_id, i.last_seen_jersey_number
      FROM public.{INPUT_PREFIX}_players i
      LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id
     ORDER BY COALESCE(m.player_id, i.player_id), i.batch_order DESC
), player_state AS (
    SELECT 'players' AS table_name,
           (SELECT COUNT(*) FROM mapped_players) AS expected_rows,
           (SELECT COUNT(*) FROM public.players p JOIN mapped_players i USING (player_id)) AS current_rows,
           ({_players_post_mismatch(map_table=fixed_map)}) AS value_mismatches
)
SELECT table_name,
       'PRE_FIX_OR_ROLLED_BACK' AS expected_state,
       backup_rows,
       current_rows,
       backup_value_mismatches AS value_mismatches,
       new_rows
  FROM pre
UNION ALL
SELECT table_name,
       'POST_FIX' AS expected_state,
       expected_rows,
       current_rows,
       value_mismatches,
       NULL::BIGINT
  FROM post
UNION ALL
SELECT table_name,
       'POST_FIX' AS expected_state,
       expected_rows,
       current_rows,
       value_mismatches,
       NULL::BIGINT
  FROM player_state
ORDER BY table_name, expected_state;

SELECT 'history_and_affiliation_counts' AS check_name,
       (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_team_name_history) AS backup_team_history_rows,
       (SELECT COUNT(*) FROM public.team_name_history h
         WHERE h.team_id IN (SELECT team_id FROM public.{INPUT_PREFIX}_teams)) AS current_team_history_rows,
       (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_player_name_history) AS backup_player_history_rows,
       (SELECT COUNT(*) FROM public.player_name_history h
         WHERE h.player_id IN (SELECT player_id FROM public.{BACKUP_PREFIX}_players)) AS current_player_history_rows,
       (SELECT COUNT(*) FROM public.{BACKUP_PREFIX}_player_affiliations) AS backup_affiliation_rows,
       (SELECT COUNT(*) FROM public.player_affiliations a
         WHERE a.player_id IN (SELECT player_id FROM public.{BACKUP_PREFIX}_players)) AS current_affiliation_rows;

SELECT 'open_affiliation_duplicates' AS check_name, player_id, COUNT(*) AS open_rows
  FROM public.player_affiliations
 WHERE valid_to IS NULL
   AND player_id IN (SELECT player_id FROM public.{BACKUP_PREFIX}_players)
 GROUP BY player_id
HAVING COUNT(*) > 1;

COMMIT;
"""


def _generate_rollback(rows: dict[str, list[dict[str, Any]]]) -> str:
    fixed_map = f'public.{BACKUP_PREFIX}_player_id_map'
    all_tables = [f'{INPUT_PREFIX}_{table}' for table in TABLES]
    all_tables += [f'{BACKUP_PREFIX}_{table}' for table in TABLES]
    all_tables += [
        f'{BACKUP_PREFIX}_player_id_map',
        f'{BACKUP_PREFIX}_team_name_history',
        f'{BACKUP_PREFIX}_player_name_history',
        f'{BACKUP_PREFIX}_player_affiliations',
        f'{BACKUP_PREFIX}_meta',
    ]
    guard = '    IF ' + '\n       OR '.join(
        f"TO_REGCLASS('public.{name}') IS NULL" for name in all_tables
    ) + " THEN\n        RAISE EXCEPTION 'Issue #46 input or backup table is missing';\n    END IF;\n"
    player_columns = [
        'player_id', 'player_name_j', 'player_name_e', 'player_slot_category',
        'league_registered_nationality', 'birthplace', 'last_seen_team_id',
        'last_seen_jersey_number', 'old_player_id', 'entity_type', 'created_at', 'updated_at',
    ]
    team_columns = ['team_id', 'team_name_j', 'team_name_e', 'team_short_name_j', 'team_short_name_e', 'created_at', 'updated_at']
    player_set = ',\n           '.join(f'{column} = backup.{column}' for column in player_columns if column != 'player_id')
    team_set = ',\n           '.join(f'{column} = backup.{column}' for column in team_columns if column != 'team_id')
    return f"""-- Issue #46: 欠落B1試合Upsertのロールバック
-- 作成日: {DATE}
-- 実行順: fix → verify（POST_FIX）→ 問題時のみ本SQL → verify（ROLLED_BACK）
-- 注意: POST_FIX状態とバックアップ表を確認してから実行する。play_by_playは変更しない。

BEGIN;

DO $issue_46_rollback$
DECLARE
    n BIGINT;
BEGIN
{guard}
    IF (SELECT COUNT(*) FROM public.teams live
          JOIN public.{INPUT_PREFIX}_teams input USING (team_id)) <> {len(rows['teams'])}
       OR (SELECT COUNT(*) FROM public.games live
             JOIN public.{INPUT_PREFIX}_games input USING (schedule_key)) <> 40
       OR (SELECT COUNT(*) FROM public.game_team_stats live
             JOIN public.{INPUT_PREFIX}_game_team_stats input
               USING (schedule_key, team_id)) <> 78
       OR (SELECT COUNT(*)
             FROM public.player_game_stats live
             JOIN public.{INPUT_PREFIX}_player_game_stats input
               ON live.schedule_key = input.schedule_key
             LEFT JOIN {fixed_map} m ON m.old_player_id = input.player_id
            WHERE live.player_id = COALESCE(m.player_id, input.player_id)) <> 917
       OR ({_post_mismatch('teams', ['team_id'], map_table=fixed_map)}) <> 0
       OR ({_post_mismatch('games', ['schedule_key'], map_table=fixed_map)}) <> 0
       OR ({_post_mismatch('game_team_stats', ['schedule_key', 'team_id'], map_table=fixed_map)}) <> 0
       OR ({_post_mismatch('player_game_stats', ['schedule_key', 'mapped_player_id'], map_table=fixed_map)}) <> 0
       OR ({_players_post_mismatch(map_table=fixed_map)}) <> 0 THEN
        RAISE EXCEPTION 'Issue #46 target rows are not in the expected POST_FIX state';
    END IF;
    DELETE FROM public.player_game_stats
     WHERE schedule_key IN (SELECT schedule_key FROM public.{INPUT_PREFIX}_player_game_stats);
    DELETE FROM public.game_team_stats
     WHERE schedule_key IN (SELECT schedule_key FROM public.{INPUT_PREFIX}_game_team_stats);

    CREATE TEMP TABLE issue46_rollback_mapped_players (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue46_rollback_mapped_players (player_id)
    SELECT DISTINCT COALESCE(m.player_id, i.player_id)
      FROM public.{INPUT_PREFIX}_players i
      LEFT JOIN {fixed_map} m ON m.old_player_id = i.player_id;

    DELETE FROM public.player_name_history
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    DELETE FROM public.player_affiliations
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    DELETE FROM public.team_name_history
     WHERE team_id IN (SELECT team_id FROM public.{INPUT_PREFIX}_teams);

    UPDATE public.players live
       SET {player_set}
      FROM public.{BACKUP_PREFIX}_players backup
     WHERE live.player_id = backup.player_id;

    DELETE FROM public.players live
     WHERE live.player_id IN (SELECT player_id FROM issue46_rollback_mapped_players)
       AND NOT EXISTS (
           SELECT 1 FROM public.{BACKUP_PREFIX}_players backup WHERE backup.player_id = live.player_id
       );

    DELETE FROM public.games live
     WHERE live.schedule_key IN (SELECT schedule_key FROM public.{INPUT_PREFIX}_games)
       AND NOT EXISTS (
           SELECT 1 FROM public.{BACKUP_PREFIX}_games backup WHERE backup.schedule_key = live.schedule_key
       );

    UPDATE public.teams live
       SET {team_set}
      FROM public.{BACKUP_PREFIX}_teams backup
     WHERE live.team_id = backup.team_id;

    DELETE FROM public.teams live
     WHERE live.team_id IN (SELECT team_id FROM public.{INPUT_PREFIX}_teams)
       AND NOT EXISTS (
           SELECT 1 FROM public.{BACKUP_PREFIX}_teams backup WHERE backup.team_id = live.team_id
       );

    UPDATE public.games live
       SET season = backup.season,
           code = backup.code,
           convention_key = backup.convention_key,
           convention_name_j = backup.convention_name_j,
           convention_name_e = backup.convention_name_e,
           year = backup.year,
           setu = backup.setu,
           game_type = backup.game_type,
           max_period = backup.max_period,
           game_current_period = backup.game_current_period,
           game_datetime_unix = backup.game_datetime_unix,
           game_datetime = backup.game_datetime,
           game_date = backup.game_date,
           stadium_cd = backup.stadium_cd,
           stadium_name_j = backup.stadium_name_j,
           stadium_name_e = backup.stadium_name_e,
           attendance = backup.attendance,
           game_ended_flg = backup.game_ended_flg,
           record_fixed_flg = backup.record_fixed_flg,
           boxscore_exists_flg = backup.boxscore_exists_flg,
           play_by_play_exists_flg = backup.play_by_play_exists_flg,
           home_team_id = backup.home_team_id,
           away_team_id = backup.away_team_id,
           home_team_score_q1 = backup.home_team_score_q1,
           home_team_score_q2 = backup.home_team_score_q2,
           home_team_score_q3 = backup.home_team_score_q3,
           home_team_score_q4 = backup.home_team_score_q4,
           home_team_score_q5 = backup.home_team_score_q5,
           home_team_score_total = backup.home_team_score_total,
           away_team_score_q1 = backup.away_team_score_q1,
           away_team_score_q2 = backup.away_team_score_q2,
           away_team_score_q3 = backup.away_team_score_q3,
           away_team_score_q4 = backup.away_team_score_q4,
           away_team_score_q5 = backup.away_team_score_q5,
           away_team_score_total = backup.away_team_score_total,
           referee_id = backup.referee_id,
           referee_name_j = backup.referee_name_j,
           sub_referee_id_1 = backup.sub_referee_id_1,
           sub_referee_name_j_1 = backup.sub_referee_name_j_1,
           sub_referee_id_2 = backup.sub_referee_id_2,
           sub_referee_name_j_2 = backup.sub_referee_name_j_2,
           source_tab = backup.source_tab,
           scraped_at = backup.scraped_at,
           updated_at = backup.updated_at
      FROM public.{BACKUP_PREFIX}_games backup
     WHERE live.schedule_key = backup.schedule_key;

    INSERT INTO public.game_team_stats
    SELECT backup.* FROM public.{BACKUP_PREFIX}_game_team_stats backup;
    INSERT INTO public.player_game_stats
    SELECT backup.* FROM public.{BACKUP_PREFIX}_player_game_stats backup;

    -- Restore the history/affiliation snapshot after all trigger-producing writes.
    DELETE FROM public.team_name_history
     WHERE team_id IN (SELECT team_id FROM public.{INPUT_PREFIX}_teams);
    DELETE FROM public.player_name_history
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    DELETE FROM public.player_affiliations
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    INSERT INTO public.team_name_history
    SELECT backup.* FROM public.{BACKUP_PREFIX}_team_name_history backup;
    INSERT INTO public.player_name_history
    SELECT backup.* FROM public.{BACKUP_PREFIX}_player_name_history backup;
    INSERT INTO public.player_affiliations
    SELECT backup.* FROM public.{BACKUP_PREFIX}_player_affiliations backup;
END;
$issue_46_rollback$;

SELECT 'restored_games' AS item, COUNT(*) AS row_count
  FROM public.games live JOIN public.{BACKUP_PREFIX}_games backup USING (schedule_key)
UNION ALL SELECT 'restored_game_team_stats', COUNT(*)
  FROM public.game_team_stats live JOIN public.{BACKUP_PREFIX}_game_team_stats backup
    USING (schedule_key, team_id)
UNION ALL SELECT 'restored_player_game_stats', COUNT(*)
  FROM public.player_game_stats live JOIN public.{BACKUP_PREFIX}_player_game_stats backup
    USING (schedule_key, player_id);

COMMIT;
"""


def main() -> None:
    rows = _collect_rows()
    outputs = {
        SQL_DIR / f'{DATE}_backup_{ISSUE}_missing_b1_games.sql': _generate_backup(rows),
        SQL_DIR / f'{DATE}_fix_{ISSUE}_missing_b1_games.sql': _generate_fix(rows),
        SQL_DIR / f'{DATE}_verify_{ISSUE}_missing_b1_games.sql': _generate_verify(rows),
        SQL_DIR / f'{DATE}_rollback_fix_{ISSUE}_missing_b1_games.sql': _generate_rollback(rows),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding='utf-8')
        print(f'generated={path} bytes={path.stat().st_size}')
    print('counts=' + json.dumps({table: len(table_rows) for table, table_rows in rows.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
