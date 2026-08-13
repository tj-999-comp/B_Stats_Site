-- Issue #12: 反映前・反映後の件数検証
-- 作成日: 2026-08-11
-- 目的: バックアップ表を基準に、変更予定件数と現在の反映状態を読み取り確認する。
-- 前提: 20260811_backup_issue_12_players.sql を先に実行する。
-- 注意: このSQLはSELECTのみで、live DBのデータを変更しない。

DO $issue_12_verify$
DECLARE
    backup_profile_rows INTEGER;
    backup_player_rows INTEGER;
    backup_stat_rows INTEGER;
    backup_name_rows INTEGER;
    backup_affiliation_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_profiles') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_players_deleted') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_affiliations') IS NULL THEN
        RAISE EXCEPTION 'Issue #12 backup tables are required; run backup SQL first';
    END IF;

    SELECT COUNT(*) INTO backup_profile_rows FROM public.data_patch_backup_20260811_issue_12_player_profiles;
    SELECT COUNT(*) INTO backup_player_rows FROM public.data_patch_backup_20260811_issue_12_players_deleted;
    SELECT COUNT(*) INTO backup_stat_rows FROM public.data_patch_backup_20260811_issue_12_player_game_stats;
    SELECT COUNT(*) INTO backup_name_rows FROM public.data_patch_backup_20260811_issue_12_player_name_history;
    SELECT COUNT(*) INTO backup_affiliation_rows FROM public.data_patch_backup_20260811_issue_12_player_affiliations;

    IF backup_profile_rows <> 166 OR backup_player_rows <> 48 OR backup_stat_rows <> 4060
       OR backup_name_rows <> 59 OR backup_affiliation_rows <> 70 THEN
        RAISE EXCEPTION 'backup row count mismatch: profiles=% players=% stats=% names=% affiliations=%',
            backup_profile_rows, backup_player_rows, backup_stat_rows, backup_name_rows, backup_affiliation_rows;
    END IF;
END;
$issue_12_verify$;

-- 変更予定の内訳。profilesの「項目更新」はNULLから値が入る列数。
SELECT 'change_plan' AS check_group, 'players.profile_rows' AS item, COUNT(*)::BIGINT AS row_count
  FROM public.data_patch_backup_20260811_issue_12_player_profiles
UNION ALL
SELECT 'change_plan', 'players.player_slot_category', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_profiles WHERE player_slot_category IS NULL
UNION ALL
SELECT 'change_plan', 'players.league_registered_nationality', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_profiles WHERE league_registered_nationality IS NULL
UNION ALL
SELECT 'change_plan', 'players.birthplace', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_profiles WHERE birthplace IS NULL
UNION ALL
SELECT 'change_plan', 'players_deleted', COUNT(*)::BIGINT
  FROM public.data_patch_backup_20260811_issue_12_players_deleted
UNION ALL
SELECT 'change_plan', 'player_game_stats_deleted', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_game_stats
UNION ALL
SELECT 'change_plan', 'player_name_history_deleted', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_name_history
UNION ALL
SELECT 'change_plan', 'player_affiliations_deleted', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_affiliations
ORDER BY item;

-- 現在の対象状態。反映前／ロールバック後は対象行が残り、反映後は削除対象が0になる。
WITH target AS (
    SELECT
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260811_issue_12_player_profiles b USING (player_id)) AS profile_rows,
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260811_issue_12_players_deleted b USING (player_id)) AS deleted_players,
        (SELECT COUNT(*) FROM public.player_game_stats s JOIN public.data_patch_backup_20260811_issue_12_players_deleted b USING (player_id)) AS deleted_stats,
        (SELECT COUNT(*) FROM public.player_name_history h JOIN public.data_patch_backup_20260811_issue_12_players_deleted b USING (player_id)) AS deleted_names,
        (SELECT COUNT(*) FROM public.player_affiliations a JOIN public.data_patch_backup_20260811_issue_12_players_deleted b USING (player_id)) AS deleted_affiliations,
        (SELECT COUNT(*) FROM public.player_id_map m JOIN public.data_patch_backup_20260811_issue_12_players_deleted b ON m.player_id = b.player_id OR m.old_player_id = b.player_id) AS map_refs,
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260811_issue_12_player_profiles b USING (player_id) WHERE p.player_slot_category IS NULL) AS missing_slot,
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260811_issue_12_player_profiles b USING (player_id) WHERE p.league_registered_nationality IS NULL) AS missing_league,
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260811_issue_12_player_profiles b USING (player_id) WHERE p.birthplace IS NULL) AS missing_birthplace
)
SELECT
    CASE
        WHEN deleted_players = 48 AND deleted_stats = 4060 AND deleted_names = 59 AND deleted_affiliations = 70
             AND missing_slot = 166 AND missing_league = 1 AND missing_birthplace = 1 AND map_refs = 0
            THEN 'BEFORE_APPLY_OR_AFTER_ROLLBACK'
        WHEN deleted_players = 0 AND deleted_stats = 0 AND deleted_names = 0 AND deleted_affiliations = 0
             AND missing_slot = 0 AND missing_league = 0 AND missing_birthplace = 0 AND map_refs = 0
            THEN 'AFTER_APPLY'
        ELSE 'UNEXPECTED_STATE'
    END AS detected_state,
    profile_rows, deleted_players, deleted_stats, deleted_names, deleted_affiliations,
    missing_slot, missing_league, missing_birthplace, map_refs
FROM target;

-- 反映後にプロフィール値がバックアップ時点から意図せず変わっていないか確認。
SELECT
    COUNT(*) FILTER (WHERE p.player_name_j IS DISTINCT FROM b.player_name_j) AS name_changed_unexpectedly,
    COUNT(*) FILTER (WHERE p.player_name_e IS DISTINCT FROM b.player_name_e) AS english_name_changed_unexpectedly,
    COUNT(*) FILTER (WHERE p.last_seen_team_id IS DISTINCT FROM b.last_seen_team_id) AS team_changed_unexpectedly,
    COUNT(*) FILTER (WHERE p.last_seen_jersey_number IS DISTINCT FROM b.last_seen_jersey_number) AS jersey_changed_unexpectedly,
    COUNT(*) AS profile_rows_checked
FROM public.players p
JOIN public.data_patch_backup_20260811_issue_12_player_profiles b USING (player_id);
