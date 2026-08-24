-- Issue #46: 欠落B1試合Upsertの実行前・実行後・ロールバック後検証
-- 作成日: 20260824
-- 実行順: backup後（PRE_FIX）、fix後（POST_FIX）、rollback後（ROLLED_BACK）に同じSQLを実行する。
-- このSQLはpublicテーブルを変更しない。

BEGIN;

DO $issue_46_verify_guard$
BEGIN
    IF TO_REGCLASS('public.data_patch_issue46_teams') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_games') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_game_team_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_players') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_teams') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_games') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_game_team_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_players') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_id_map') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_team_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_affiliations') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_meta') IS NULL THEN
        RAISE EXCEPTION 'Issue #46 input or backup table is missing';
    END IF;

    IF (SELECT COUNT(*) FROM public.data_patch_issue46_teams) <> 27
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_games) <> 40
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_game_team_stats) <> 78
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_players) <> 687
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_player_game_stats) <> 917 THEN
        RAISE EXCEPTION 'Issue #46 input row-count guard failed';
    END IF;
END;
$issue_46_verify_guard$;

WITH pre AS (
    SELECT 'teams' AS table_name,
           (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_teams) AS backup_rows,
           (SELECT COUNT(*) FROM public.teams t JOIN public.data_patch_issue46_teams i USING (team_id)) AS current_rows,
           (SELECT COUNT(*) FROM public.teams t JOIN public.data_patch_backup_20260824_issue46_teams b USING (team_id)
             WHERE to_jsonb(t) IS DISTINCT FROM to_jsonb(b)) AS backup_value_mismatches,
           (SELECT COUNT(*) FROM public.teams t JOIN public.data_patch_issue46_teams i USING (team_id)
             WHERE NOT EXISTS (SELECT 1 FROM public.data_patch_backup_20260824_issue46_teams b WHERE b.team_id = t.team_id)) AS new_rows
    UNION ALL
    SELECT 'players',
           (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_players),
           (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260824_issue46_players b USING (player_id)),
           (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260824_issue46_players b USING (player_id)
             WHERE to_jsonb(p) IS DISTINCT FROM to_jsonb(b)),
           (SELECT COUNT(*) FROM public.players p
             WHERE p.player_id IN (
                 SELECT DISTINCT COALESCE(m.player_id, i.player_id)
                   FROM public.data_patch_issue46_players i
                   LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
             )
               AND NOT EXISTS (SELECT 1 FROM public.data_patch_backup_20260824_issue46_players b WHERE b.player_id = p.player_id))
    UNION ALL
    SELECT 'games' AS table_name,
           (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_games) AS backup_rows,
           (SELECT COUNT(*) FROM public.games g JOIN public.data_patch_issue46_games i USING (schedule_key)) AS current_rows,
           (SELECT COUNT(*) FROM public.games g JOIN public.data_patch_backup_20260824_issue46_games b USING (schedule_key)
             WHERE to_jsonb(g) IS DISTINCT FROM to_jsonb(b)) AS backup_value_mismatches,
           (SELECT COUNT(*) FROM public.games g JOIN public.data_patch_issue46_games i USING (schedule_key)
             WHERE NOT EXISTS (SELECT 1 FROM public.data_patch_backup_20260824_issue46_games b WHERE b.schedule_key = g.schedule_key)) AS new_rows
    UNION ALL
    SELECT 'game_team_stats',
           (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_game_team_stats),
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.data_patch_issue46_game_team_stats i USING (schedule_key, team_id)),
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.data_patch_backup_20260824_issue46_game_team_stats b USING (schedule_key, team_id)
             WHERE to_jsonb(g) IS DISTINCT FROM to_jsonb(b)),
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.data_patch_issue46_game_team_stats i USING (schedule_key, team_id)
             WHERE NOT EXISTS (SELECT 1 FROM public.data_patch_backup_20260824_issue46_game_team_stats b WHERE b.schedule_key = g.schedule_key AND b.team_id = g.team_id))
    UNION ALL
    SELECT 'player_game_stats',
           (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_player_game_stats),
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.data_patch_issue46_player_game_stats i
              ON g.schedule_key = i.schedule_key
             LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
            WHERE g.player_id = COALESCE(m.player_id, i.player_id)),
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.data_patch_backup_20260824_issue46_player_game_stats b USING (schedule_key, player_id)
             WHERE to_jsonb(g) IS DISTINCT FROM to_jsonb(b)),
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.data_patch_issue46_player_game_stats i
              ON g.schedule_key = i.schedule_key
             LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
            WHERE g.player_id = COALESCE(m.player_id, i.player_id)
              AND NOT EXISTS (SELECT 1 FROM public.data_patch_backup_20260824_issue46_player_game_stats b WHERE b.schedule_key = g.schedule_key AND b.player_id = g.player_id))
), post AS (
    SELECT 'teams' AS table_name,
           27::BIGINT AS expected_rows,
           (SELECT COUNT(*) FROM public.teams t JOIN public.data_patch_issue46_teams i USING (team_id)) AS current_rows,
           (SELECT COUNT(*) AS mismatch_rows
  FROM public.data_patch_issue46_teams input
  LEFT JOIN public.teams live ON live.team_id = input.team_id
 WHERE live.team_id IS NULL
    OR to_jsonb(live) - 'created_at' - 'updated_at' IS DISTINCT FROM to_jsonb(input)) AS value_mismatches
    UNION ALL
    SELECT 'games' AS table_name,
           40::BIGINT AS expected_rows,
           (SELECT COUNT(*) FROM public.games g JOIN public.data_patch_issue46_games i USING (schedule_key)) AS current_rows,
           (SELECT COUNT(*) AS mismatch_rows
  FROM public.data_patch_issue46_games input
  LEFT JOIN public.games live ON live.schedule_key = input.schedule_key
 WHERE live.schedule_key IS NULL
    OR to_jsonb(live) - 'created_at' - 'scraped_at' - 'updated_at' IS DISTINCT FROM
       (to_jsonb(input) || jsonb_build_object('setu', input.setu::TEXT))) AS value_mismatches
    UNION ALL
    SELECT 'game_team_stats',
           78,
           (SELECT COUNT(*) FROM public.game_team_stats g JOIN public.data_patch_issue46_game_team_stats i USING (schedule_key, team_id)),
           (SELECT COUNT(*) AS mismatch_rows
  FROM public.data_patch_issue46_game_team_stats input
  LEFT JOIN public.game_team_stats live ON live.schedule_key = input.schedule_key AND live.team_id = input.team_id
 WHERE live.schedule_key IS NULL
    OR to_jsonb(live) - 'away_efg_pct' - 'away_off_rtg' - 'away_opp_efg_pct' - 'away_opp_ts_pct' - 'away_ts_pct' - 'created_at' - 'dead_tov_pct' - 'dead_tov_share' - 'dr_chances' - 'dunks' - 'ft_d_pct' - 'home_efg_pct' - 'home_off_rtg' - 'home_opp_efg_pct' - 'home_opp_ts_pct' - 'home_ts_pct' - 'live_tov_pct' - 'live_tov_share' - 'off_success_count' - 'opp_ft_d_pct' - 'opp_ft_rate' - 'opp_perimeter_pts_pct' - 'opp_success_count' - 'opp_vps' - 'or_chances' - 'perimeter_pts_pct' - 'pythagorean_win_pct' - 'tom' - 'updated_at' - 'vps' IS DISTINCT FROM to_jsonb(input))
    UNION ALL
    SELECT 'player_game_stats',
           917,
           (SELECT COUNT(*) FROM public.player_game_stats g JOIN public.data_patch_issue46_player_game_stats i
              ON g.schedule_key = i.schedule_key
             LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
            WHERE g.player_id = COALESCE(m.player_id, i.player_id)),
           (SELECT COUNT(*) AS mismatch_rows
  FROM (
      SELECT i.*, COALESCE(m.player_id, i.player_id) AS mapped_player_id
        FROM public.data_patch_issue46_player_game_stats i
        LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
  ) input
  LEFT JOIN public.player_game_stats live
    ON live.schedule_key = input.schedule_key
   AND live.player_id = input.mapped_player_id
 WHERE live.schedule_key IS NULL
    OR to_jsonb(live) - 'created_at' - 'updated_at' IS DISTINCT FROM
       ((to_jsonb(input) - 'mapped_player_id') || jsonb_build_object('player_id', input.mapped_player_id)))
), mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, i.player_id))
           COALESCE(m.player_id, i.player_id) AS player_id,
           i.player_name_j, i.player_name_e, i.last_seen_team_id, i.last_seen_jersey_number
      FROM public.data_patch_issue46_players i
      LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
     ORDER BY COALESCE(m.player_id, i.player_id), i.batch_order DESC
), player_state AS (
    SELECT 'players' AS table_name,
           (SELECT COUNT(*) FROM mapped_players) AS expected_rows,
           (SELECT COUNT(*) FROM public.players p JOIN mapped_players i USING (player_id)) AS current_rows,
           (WITH mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, i.player_id))
           COALESCE(m.player_id, i.player_id) AS player_id,
           i.player_name_j,
           i.player_name_e,
           i.last_seen_team_id,
           i.last_seen_jersey_number
      FROM public.data_patch_issue46_players i
      LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
     ORDER BY COALESCE(m.player_id, i.player_id), i.batch_order DESC
)
SELECT COUNT(*) AS mismatch_rows
  FROM mapped_players input
  LEFT JOIN public.players live USING (player_id)
 WHERE live.player_id IS NULL
    OR (to_jsonb(live) - ARRAY['batch_order', 'player_slot_category', 'league_registered_nationality', 'birthplace', 'old_player_id', 'entity_type', 'created_at', 'updated_at']::text[])
       IS DISTINCT FROM to_jsonb(input)) AS value_mismatches
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
       (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_team_name_history) AS backup_team_history_rows,
       (SELECT COUNT(*) FROM public.team_name_history h
         WHERE h.team_id IN (SELECT team_id FROM public.data_patch_issue46_teams)) AS current_team_history_rows,
       (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_player_name_history) AS backup_player_history_rows,
       (SELECT COUNT(*) FROM public.player_name_history h
         WHERE h.player_id IN (SELECT player_id FROM public.data_patch_backup_20260824_issue46_players)) AS current_player_history_rows,
       (SELECT COUNT(*) FROM public.data_patch_backup_20260824_issue46_player_affiliations) AS backup_affiliation_rows,
       (SELECT COUNT(*) FROM public.player_affiliations a
         WHERE a.player_id IN (SELECT player_id FROM public.data_patch_backup_20260824_issue46_players)) AS current_affiliation_rows;

SELECT 'open_affiliation_duplicates' AS check_name, player_id, COUNT(*) AS open_rows
  FROM public.player_affiliations
 WHERE valid_to IS NULL
   AND player_id IN (SELECT player_id FROM public.data_patch_backup_20260824_issue46_players)
 GROUP BY player_id
HAVING COUNT(*) > 1;

COMMIT;
