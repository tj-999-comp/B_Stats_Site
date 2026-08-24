-- Issue #46: 欠落B1試合Upsertのロールバック
-- 作成日: 20260824
-- 実行順: fix → verify（POST_FIX）→ 問題時のみ本SQL → verify（ROLLED_BACK）
-- 注意: POST_FIX状態とバックアップ表を確認してから実行する。play_by_playは変更しない。

BEGIN;

DO $issue_46_rollback$
DECLARE
    n BIGINT;
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

    IF (SELECT COUNT(*) FROM public.teams live
          JOIN public.data_patch_issue46_teams input USING (team_id)) <> 27
       OR (SELECT COUNT(*) FROM public.games live
             JOIN public.data_patch_issue46_games input USING (schedule_key)) <> 40
       OR (SELECT COUNT(*) FROM public.game_team_stats live
             JOIN public.data_patch_issue46_game_team_stats input
               USING (schedule_key, team_id)) <> 78
       OR (SELECT COUNT(*)
             FROM public.player_game_stats live
             JOIN public.data_patch_issue46_player_game_stats input
               ON live.schedule_key = input.schedule_key
             LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = input.player_id
            WHERE live.player_id = COALESCE(m.player_id, input.player_id)) <> 917
       OR (SELECT COUNT(*) AS mismatch_rows
  FROM public.data_patch_issue46_teams input
  LEFT JOIN public.teams live ON live.team_id = input.team_id
 WHERE live.team_id IS NULL
    OR to_jsonb(live) - 'created_at' - 'updated_at' IS DISTINCT FROM to_jsonb(input)) <> 0
       OR (SELECT COUNT(*) AS mismatch_rows
  FROM public.data_patch_issue46_games input
  LEFT JOIN public.games live ON live.schedule_key = input.schedule_key
 WHERE live.schedule_key IS NULL
    OR to_jsonb(live) - 'created_at' - 'scraped_at' - 'updated_at' IS DISTINCT FROM
       (to_jsonb(input) || jsonb_build_object('setu', input.setu::TEXT))) <> 0
       OR (SELECT COUNT(*) AS mismatch_rows
  FROM public.data_patch_issue46_game_team_stats input
  LEFT JOIN public.game_team_stats live ON live.schedule_key = input.schedule_key AND live.team_id = input.team_id
 WHERE live.schedule_key IS NULL
    OR to_jsonb(live) - 'away_efg_pct' - 'away_off_rtg' - 'away_opp_efg_pct' - 'away_opp_ts_pct' - 'away_ts_pct' - 'created_at' - 'dead_tov_pct' - 'dead_tov_share' - 'dr_chances' - 'dunks' - 'ft_d_pct' - 'home_efg_pct' - 'home_off_rtg' - 'home_opp_efg_pct' - 'home_opp_ts_pct' - 'home_ts_pct' - 'live_tov_pct' - 'live_tov_share' - 'off_success_count' - 'opp_ft_d_pct' - 'opp_ft_rate' - 'opp_perimeter_pts_pct' - 'opp_success_count' - 'opp_vps' - 'or_chances' - 'perimeter_pts_pct' - 'pythagorean_win_pct' - 'tom' - 'updated_at' - 'vps' IS DISTINCT FROM to_jsonb(input)) <> 0
       OR (SELECT COUNT(*) AS mismatch_rows
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
       ((to_jsonb(input) - 'mapped_player_id') || jsonb_build_object('player_id', input.mapped_player_id))) <> 0
       OR (WITH mapped_players AS (
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
       IS DISTINCT FROM to_jsonb(input)) <> 0 THEN
        RAISE EXCEPTION 'Issue #46 target rows are not in the expected POST_FIX state';
    END IF;
    DELETE FROM public.player_game_stats
     WHERE schedule_key IN (SELECT schedule_key FROM public.data_patch_issue46_player_game_stats);
    DELETE FROM public.game_team_stats
     WHERE schedule_key IN (SELECT schedule_key FROM public.data_patch_issue46_game_team_stats);

    CREATE TEMP TABLE issue46_rollback_mapped_players (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue46_rollback_mapped_players (player_id)
    SELECT DISTINCT COALESCE(m.player_id, i.player_id)
      FROM public.data_patch_issue46_players i
      LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id;

    DELETE FROM public.player_name_history
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    DELETE FROM public.player_affiliations
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    DELETE FROM public.team_name_history
     WHERE team_id IN (SELECT team_id FROM public.data_patch_issue46_teams);

    UPDATE public.players live
       SET player_name_j = backup.player_name_j,
           player_name_e = backup.player_name_e,
           player_slot_category = backup.player_slot_category,
           league_registered_nationality = backup.league_registered_nationality,
           birthplace = backup.birthplace,
           last_seen_team_id = backup.last_seen_team_id,
           last_seen_jersey_number = backup.last_seen_jersey_number,
           old_player_id = backup.old_player_id,
           entity_type = backup.entity_type,
           created_at = backup.created_at,
           updated_at = backup.updated_at
      FROM public.data_patch_backup_20260824_issue46_players backup
     WHERE live.player_id = backup.player_id;

    DELETE FROM public.players live
     WHERE live.player_id IN (SELECT player_id FROM issue46_rollback_mapped_players)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_players backup WHERE backup.player_id = live.player_id
       );

    DELETE FROM public.games live
     WHERE live.schedule_key IN (SELECT schedule_key FROM public.data_patch_issue46_games)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_games backup WHERE backup.schedule_key = live.schedule_key
       );

    UPDATE public.teams live
       SET team_name_j = backup.team_name_j,
           team_name_e = backup.team_name_e,
           team_short_name_j = backup.team_short_name_j,
           team_short_name_e = backup.team_short_name_e,
           created_at = backup.created_at,
           updated_at = backup.updated_at
      FROM public.data_patch_backup_20260824_issue46_teams backup
     WHERE live.team_id = backup.team_id;

    DELETE FROM public.teams live
     WHERE live.team_id IN (SELECT team_id FROM public.data_patch_issue46_teams)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_teams backup WHERE backup.team_id = live.team_id
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
      FROM public.data_patch_backup_20260824_issue46_games backup
     WHERE live.schedule_key = backup.schedule_key;

    INSERT INTO public.game_team_stats
    SELECT backup.* FROM public.data_patch_backup_20260824_issue46_game_team_stats backup;
    INSERT INTO public.player_game_stats
    SELECT backup.* FROM public.data_patch_backup_20260824_issue46_player_game_stats backup;

    -- Restore the history/affiliation snapshot after all trigger-producing writes.
    DELETE FROM public.team_name_history
     WHERE team_id IN (SELECT team_id FROM public.data_patch_issue46_teams);
    DELETE FROM public.player_name_history
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    DELETE FROM public.player_affiliations
     WHERE player_id IN (SELECT player_id FROM issue46_rollback_mapped_players);
    INSERT INTO public.team_name_history
    SELECT backup.* FROM public.data_patch_backup_20260824_issue46_team_name_history backup;
    INSERT INTO public.player_name_history
    SELECT backup.* FROM public.data_patch_backup_20260824_issue46_player_name_history backup;
    INSERT INTO public.player_affiliations
    SELECT backup.* FROM public.data_patch_backup_20260824_issue46_player_affiliations backup;
END;
$issue_46_rollback$;

SELECT 'restored_games' AS item, COUNT(*) AS row_count
  FROM public.games live JOIN public.data_patch_backup_20260824_issue46_games backup USING (schedule_key)
UNION ALL SELECT 'restored_game_team_stats', COUNT(*)
  FROM public.game_team_stats live JOIN public.data_patch_backup_20260824_issue46_game_team_stats backup
    USING (schedule_key, team_id)
UNION ALL SELECT 'restored_player_game_stats', COUNT(*)
  FROM public.player_game_stats live JOIN public.data_patch_backup_20260824_issue46_player_game_stats backup
    USING (schedule_key, player_id);

COMMIT;
