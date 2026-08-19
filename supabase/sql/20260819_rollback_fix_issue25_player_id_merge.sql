-- Issue #25: player_id重複統合のロールバック
-- 作成日: 2026-08-19
-- 実行順: fix → verify（POST_FIX）→ 問題時のみ本SQL → verify（ROLLED_BACK）
-- 注意: backup表を基準に対象18組を変更前へ戻す。他のIDの行は変更しない。

DO $issue_25_rollback$
DECLARE
    n BIGINT;
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
    IF n <> 0 THEN RAISE EXCEPTION 'old players still exist; expected post-fix state'; END IF;
    SELECT COUNT(*) INTO n FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = p.player_id;
    IF n <> 18 THEN RAISE EXCEPTION 'canonical players mismatch: expected=18 actual=%', n; END IF;
    SELECT COUNT(*) INTO n FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = s.player_id;
    IF n <> 0 THEN RAISE EXCEPTION 'old stats still exist'; END IF;
    SELECT COUNT(*) INTO n FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = s.player_id;
    IF n <> (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_game_stats) THEN RAISE EXCEPTION 'canonical stats do not match backup total'; END IF;
    SELECT COUNT(*) INTO n FROM public.player_id_map x JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = x.old_player_id;
    IF n <> 18 THEN RAISE EXCEPTION 'target player_id_map rows mismatch: expected=18 actual=%', n; END IF;

    SELECT COUNT(*) INTO n
      FROM public.player_id_map x
      JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = x.player_id
     WHERE x.old_player_id NOT IN (SELECT old_player_id FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map);
    IF n <> 0 THEN RAISE EXCEPTION 'other player_id_map rows reference canonical IDs: %', n; END IF;

    DELETE FROM public.player_game_stats s USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m WHERE s.player_id = m.player_id;
    DELETE FROM public.player_name_history h USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m WHERE h.player_id = m.player_id;
    DELETE FROM public.player_affiliations a USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m WHERE a.player_id = m.player_id;
    DELETE FROM public.player_id_map x USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m WHERE x.old_player_id = m.old_player_id;
    DELETE FROM public.players p USING public.data_patch_backup_20260819_issue_25_player_id_merge_map m WHERE p.player_id = m.player_id;

    INSERT INTO public.players SELECT * FROM public.data_patch_backup_20260819_issue_25_players;
    INSERT INTO public.player_game_stats SELECT * FROM public.data_patch_backup_20260819_issue_25_player_game_stats;
    INSERT INTO public.player_name_history SELECT * FROM public.data_patch_backup_20260819_issue_25_player_name_history;
    INSERT INTO public.player_affiliations SELECT * FROM public.data_patch_backup_20260819_issue_25_player_affiliations;
    INSERT INTO public.player_id_map SELECT * FROM public.data_patch_backup_20260819_issue_25_player_id_map;

    SELECT COUNT(*) INTO n FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = p.player_id;
    IF n <> 18 THEN RAISE EXCEPTION 'rollback players restore mismatch: %', n; END IF;
    SELECT COUNT(*) INTO n FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = s.player_id;
    IF n <> (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_game_stats WHERE player_id IN (SELECT old_player_id FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map)) THEN RAISE EXCEPTION 'rollback stats restore mismatch'; END IF;

    RAISE NOTICE 'Issue #25 rollback complete';
END;
$issue_25_rollback$;

SELECT 'restored_players' AS item, COUNT(*) AS row_count FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = p.player_id
UNION ALL SELECT 'restored_old_stats', COUNT(*) FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = s.player_id
UNION ALL SELECT 'restored_old_name_history', COUNT(*) FROM public.player_name_history h JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = h.player_id
UNION ALL SELECT 'restored_old_affiliations', COUNT(*) FROM public.player_affiliations a JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = a.player_id;
