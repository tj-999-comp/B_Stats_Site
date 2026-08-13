-- Issue #12: playersプロフィール補完・スタッフ行整理のロールバック
-- 作成日: 2026-08-11
-- 目的: 20260811_fix_issue_12_players.sql のプロフィール更新と削除を元に戻す。
-- 前提: 反映SQLが作成した5つのバックアップ表が存在し、対象IDが反映後の状態であること。
-- 再実行: 不可。復元対象が既に存在する場合や件数が合わない場合は停止する。
-- 注意: SQL Editor/DBeaverではファイル全体を一括実行すること。

DO $issue_12_rollback$
DECLARE
    profile_rows INTEGER;
    deleted_player_rows INTEGER;
    stat_rows INTEGER;
    name_rows INTEGER;
    affiliation_rows INTEGER;
    existing_deleted_players INTEGER;
    existing_deleted_stats INTEGER;
    existing_deleted_names INTEGER;
    existing_deleted_affiliations INTEGER;
    missing_profile_rows INTEGER;
    restored_players INTEGER;
    restored_stats INTEGER;
    restored_names INTEGER;
    restored_affiliations INTEGER;
    profile_mismatches INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_profiles') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_players_deleted') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_affiliations') IS NULL THEN
        RAISE EXCEPTION 'Issue #12 backup tables are required';
    END IF;

    SELECT COUNT(*) INTO profile_rows FROM public.data_patch_backup_20260811_issue_12_player_profiles;
    SELECT COUNT(*) INTO deleted_player_rows FROM public.data_patch_backup_20260811_issue_12_players_deleted;
    SELECT COUNT(*) INTO stat_rows FROM public.data_patch_backup_20260811_issue_12_player_game_stats;
    SELECT COUNT(*) INTO name_rows FROM public.data_patch_backup_20260811_issue_12_player_name_history;
    SELECT COUNT(*) INTO affiliation_rows FROM public.data_patch_backup_20260811_issue_12_player_affiliations;
    IF profile_rows <> 166 OR deleted_player_rows <> 48 OR stat_rows <> 4060
       OR name_rows <> 59 OR affiliation_rows <> 70 THEN
        RAISE EXCEPTION 'backup row count mismatch: profiles=% players=% stats=% names=% affiliations=%',
            profile_rows, deleted_player_rows, stat_rows, name_rows, affiliation_rows;
    END IF;

    CREATE TEMP TABLE issue_12_delete_ids (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue_12_delete_ids (player_id)
        SELECT player_id FROM public.data_patch_backup_20260811_issue_12_players_deleted;

    SELECT COUNT(*) INTO existing_deleted_players
      FROM public.players p JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO existing_deleted_stats
      FROM public.player_game_stats s JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO existing_deleted_names
      FROM public.player_name_history h JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO existing_deleted_affiliations
      FROM public.player_affiliations a JOIN issue_12_delete_ids d USING (player_id);
    IF existing_deleted_players <> 0 OR existing_deleted_stats <> 0
       OR existing_deleted_names <> 0 OR existing_deleted_affiliations <> 0 THEN
        RAISE EXCEPTION 'rollback targets already exist: players=% stats=% names=% affiliations=%',
            existing_deleted_players, existing_deleted_stats, existing_deleted_names, existing_deleted_affiliations;
    END IF;

    SELECT COUNT(*) INTO missing_profile_rows
      FROM public.data_patch_backup_20260811_issue_12_player_profiles b
      LEFT JOIN public.players p USING (player_id)
     WHERE p.player_id IS NULL;
    IF missing_profile_rows <> 0 THEN
        RAISE EXCEPTION 'profile rollback targets missing from players: %', missing_profile_rows;
    END IF;

    INSERT INTO public.players
        SELECT b.* FROM public.data_patch_backup_20260811_issue_12_players_deleted b;
    GET DIAGNOSTICS restored_players = ROW_COUNT;
    IF restored_players <> 48 THEN
        RAISE EXCEPTION 'player restore count mismatch: expected=48 actual=%', restored_players;
    END IF;

    UPDATE public.players p
       SET player_name_j = b.player_name_j,
           player_name_e = b.player_name_e,
           player_slot_category = b.player_slot_category,
           league_registered_nationality = b.league_registered_nationality,
           birthplace = b.birthplace,
           last_seen_team_id = b.last_seen_team_id,
           last_seen_jersey_number = b.last_seen_jersey_number,
           old_player_id = b.old_player_id,
           created_at = b.created_at,
           updated_at = b.updated_at
      FROM public.data_patch_backup_20260811_issue_12_player_profiles b
     WHERE p.player_id = b.player_id;

    INSERT INTO public.player_game_stats
        SELECT b.* FROM public.data_patch_backup_20260811_issue_12_player_game_stats b;
    GET DIAGNOSTICS restored_stats = ROW_COUNT;
    IF restored_stats <> 4060 THEN
        RAISE EXCEPTION 'player_game_stats restore count mismatch: expected=4060 actual=%', restored_stats;
    END IF;

    -- stats INSERTの履歴トリガーが作った行を含め、対象IDの履歴をバックアップ状態へ戻す。
    DELETE FROM public.player_name_history h USING issue_12_delete_ids d WHERE h.player_id = d.player_id;
    INSERT INTO public.player_name_history
        SELECT b.* FROM public.data_patch_backup_20260811_issue_12_player_name_history b;
    GET DIAGNOSTICS restored_names = ROW_COUNT;
    IF restored_names <> 59 THEN
        RAISE EXCEPTION 'player_name_history restore count mismatch: expected=59 actual=%', restored_names;
    END IF;

    DELETE FROM public.player_affiliations a USING issue_12_delete_ids d WHERE a.player_id = d.player_id;
    INSERT INTO public.player_affiliations
        SELECT b.* FROM public.data_patch_backup_20260811_issue_12_player_affiliations b;
    GET DIAGNOSTICS restored_affiliations = ROW_COUNT;
    IF restored_affiliations <> 70 THEN
        RAISE EXCEPTION 'player_affiliations restore count mismatch: expected=70 actual=%', restored_affiliations;
    END IF;

    SELECT COUNT(*) INTO profile_mismatches
      FROM public.players p
      JOIN public.data_patch_backup_20260811_issue_12_player_profiles b USING (player_id)
     WHERE p.player_name_j IS DISTINCT FROM b.player_name_j
        OR p.player_name_e IS DISTINCT FROM b.player_name_e
        OR p.player_slot_category IS DISTINCT FROM b.player_slot_category
        OR p.league_registered_nationality IS DISTINCT FROM b.league_registered_nationality
        OR p.birthplace IS DISTINCT FROM b.birthplace
        OR p.last_seen_team_id IS DISTINCT FROM b.last_seen_team_id
        OR p.last_seen_jersey_number IS DISTINCT FROM b.last_seen_jersey_number
        OR p.old_player_id IS DISTINCT FROM b.old_player_id
        OR p.created_at IS DISTINCT FROM b.created_at
        OR p.updated_at IS DISTINCT FROM b.updated_at;
    IF profile_mismatches <> 0 THEN
        RAISE EXCEPTION 'profile rollback postcheck mismatch: %', profile_mismatches;
    END IF;
END;
$issue_12_rollback$;

SELECT 'restored_players' AS check_name, COUNT(*) AS row_count
  FROM public.data_patch_backup_20260811_issue_12_players_deleted b
  JOIN public.players p USING (player_id)
UNION ALL
SELECT 'restored_player_game_stats', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_game_stats b
  JOIN public.player_game_stats s USING (schedule_key, player_id)
UNION ALL
SELECT 'restored_name_history', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_name_history b
  JOIN public.player_name_history h USING (history_id)
UNION ALL
SELECT 'restored_affiliations', COUNT(*)
  FROM public.data_patch_backup_20260811_issue_12_player_affiliations b
  JOIN public.player_affiliations a USING (affiliation_id)
ORDER BY check_name;
