-- Issue #25: player_id重複統合
-- 作成日: 2026-08-19
-- 実行順: backup → verify（PRE_FIX）→ 本SQL → verify（POST_FIX）
-- 対象: players、player_game_stats、player_name_history、player_affiliations、player_id_map
-- 注意: 本SQLはLive DBを変更する。事前に接続先とverify結果を確認すること。

DO $issue_25_fix$
DECLARE
    n BIGINT;
    updated_stats BIGINT;
    deleted_names BIGINT;
    deleted_affiliations BIGINT;
    deleted_players BIGINT;
    inserted_maps BIGINT;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_id_merge_map') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_players') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_affiliations') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_id_map') IS NULL THEN
        RAISE EXCEPTION 'Issue #25 backup tables are missing';
    END IF;

    SELECT COUNT(*) INTO n FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = p.player_id;
    IF n <> 18 THEN RAISE EXCEPTION 'expected 18 old players, actual=%', n; END IF;
    SELECT COUNT(*) INTO n FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = p.player_id;
    IF n <> 18 THEN RAISE EXCEPTION 'expected 18 canonical players, actual=%', n; END IF;

    SELECT COUNT(*) INTO n
      FROM public.player_game_stats old_s
      JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = old_s.player_id
      JOIN public.player_game_stats new_s
        ON new_s.player_id = m.player_id
       AND new_s.schedule_key = old_s.schedule_key;
    IF n <> 0 THEN RAISE EXCEPTION 'player_game_stats conflicts before fix: %', n; END IF;

    SELECT COUNT(*) INTO n FROM public.player_id_map x JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = x.old_player_id;
    IF n <> 0 THEN RAISE EXCEPTION 'target old IDs already exist in player_id_map: %', n; END IF;

    SELECT COUNT(*) INTO n
      FROM public.players p
      JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = p.player_id
      WHERE p.old_player_id IS NOT NULL AND p.old_player_id IS DISTINCT FROM m.old_player_id;
    IF n <> 0 THEN RAISE EXCEPTION 'canonical players have conflicting old_player_id values: %', n; END IF;

    UPDATE public.players p
       SET old_player_id = m.old_player_id,
           updated_at = NOW()
      FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map m
     WHERE p.player_id = m.player_id
       AND p.old_player_id IS NULL;

    UPDATE public.player_game_stats s
       SET player_id = m.player_id,
           updated_at = NOW()
      FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map m
     WHERE s.player_id = m.old_player_id;
    GET DIAGNOSTICS updated_stats = ROW_COUNT;

    DELETE FROM public.player_name_history h
     USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m
     WHERE h.player_id = m.old_player_id;
    GET DIAGNOSTICS deleted_names = ROW_COUNT;

    DELETE FROM public.player_affiliations a
     USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m
     WHERE a.player_id = m.old_player_id;
    GET DIAGNOSTICS deleted_affiliations = ROW_COUNT;

    DELETE FROM public.players p
     USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m
     WHERE p.player_id = m.old_player_id;
    GET DIAGNOSTICS deleted_players = ROW_COUNT;

    INSERT INTO public.player_id_map (old_player_id, player_id, note)
    SELECT old_player_id, player_id, 'Issue #25 merged after reviewed identity match: ' || player_name_j
      FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map;
    GET DIAGNOSTICS inserted_maps = ROW_COUNT;

    IF updated_stats <> (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_game_stats WHERE player_id IN (SELECT old_player_id FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map))
       OR deleted_names <> (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_name_history WHERE player_id IN (SELECT old_player_id FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map))
       OR deleted_affiliations <> (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_affiliations WHERE player_id IN (SELECT old_player_id FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map))
       OR deleted_players <> 18
       OR inserted_maps <> 18 THEN
        RAISE EXCEPTION 'fix row-count guard failed: stats=%, names=%, affiliations=%, players=%, maps=%', updated_stats, deleted_names, deleted_affiliations, deleted_players, inserted_maps;
    END IF;

    RAISE NOTICE 'Issue #25 fix complete: stats=%, old histories deleted=%, old affiliations deleted=%, old players deleted=%, maps inserted=%', updated_stats, deleted_names, deleted_affiliations, deleted_players, inserted_maps;
END;
$issue_25_fix$;

SELECT 'old_players_remaining' AS item, COUNT(*) AS row_count FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = p.player_id
UNION ALL SELECT 'canonical_players', COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = p.player_id
UNION ALL SELECT 'old_stats_remaining', COUNT(*) FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = s.player_id
UNION ALL SELECT 'canonical_stats', COUNT(*) FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = s.player_id
UNION ALL SELECT 'target_player_id_map_rows', COUNT(*) FROM public.player_id_map x JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = x.old_player_id;
