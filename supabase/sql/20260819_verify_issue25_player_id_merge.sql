-- Issue #25: player_id重複統合の実行前・実行後・ロールバック後検証
-- 作成日: 2026-08-19
-- SELECTと一時表のみ。永続データは変更しない。

WITH b AS (
    SELECT
        (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_players) AS backup_players,
        (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_game_stats) AS backup_stats,
        (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_name_history) AS backup_names,
        (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_affiliations) AS backup_affiliations,
        (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_id_map) AS backup_map
), c AS (
    SELECT
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = p.player_id) AS old_players,
        (SELECT COUNT(*) FROM public.players p JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = p.player_id) AS canonical_players,
        (SELECT COUNT(*) FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = s.player_id) AS old_stats,
        (SELECT COUNT(*) FROM public.player_game_stats s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = s.player_id) AS canonical_stats,
        (SELECT COUNT(*) FROM public.player_name_history h JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = h.player_id) AS old_names,
        (SELECT COUNT(*) FROM public.player_name_history h JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = h.player_id) AS canonical_names,
        (SELECT COUNT(*) FROM public.player_affiliations a JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = a.player_id) AS old_affiliations,
        (SELECT COUNT(*) FROM public.player_affiliations a JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = a.player_id) AS canonical_affiliations,
        (SELECT COUNT(*) FROM public.player_id_map x JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = x.old_player_id) AS target_map_rows,
        (SELECT COUNT(*) FROM public.player_game_stats old_s JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.old_player_id = old_s.player_id JOIN public.player_game_stats new_s ON new_s.player_id = m.player_id AND new_s.schedule_key = old_s.schedule_key) AS stat_conflicts
)
SELECT
    CASE
        WHEN c.old_players = 18
         AND c.canonical_players = 18
         AND c.old_stats + c.canonical_stats = b.backup_stats
         AND c.old_names + c.canonical_names = b.backup_names
         AND c.old_affiliations + c.canonical_affiliations = b.backup_affiliations
         AND c.target_map_rows = b.backup_map
         AND c.stat_conflicts = 0
        THEN 'PRE_FIX'
        WHEN c.old_players = 0
         AND c.canonical_players = 18
         AND c.old_stats = 0
         AND c.canonical_stats = b.backup_stats
         AND c.old_names = 0
         AND c.canonical_names = (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_name_history h JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = h.player_id)
         AND c.old_affiliations = 0
         AND c.canonical_affiliations = (SELECT COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_affiliations a JOIN public.data_patch_backup_20260819_issue_25_player_id_merge_map m ON m.player_id = a.player_id)
         AND c.target_map_rows = 18
         AND c.stat_conflicts = 0
        THEN 'POST_FIX'
        WHEN c.old_players = 18
         AND c.canonical_players = 18
         AND c.old_stats + c.canonical_stats = b.backup_stats
         AND c.old_names + c.canonical_names = b.backup_names
         AND c.old_affiliations + c.canonical_affiliations = b.backup_affiliations
         AND c.target_map_rows = b.backup_map
        THEN 'ROLLED_BACK_OR_PRE_FIX'
        ELSE 'UNEXPECTED_STATE'
    END AS verification_status,
    b.*, c.*
FROM b CROSS JOIN c;

SELECT m.old_player_id, m.player_id,
       p_old.player_id IS NOT NULL AS old_player_exists,
       p_new.player_id IS NOT NULL AS canonical_player_exists,
       (SELECT COUNT(*) FROM public.player_game_stats s WHERE s.player_id = m.old_player_id) AS old_stats,
       (SELECT COUNT(*) FROM public.player_game_stats s WHERE s.player_id = m.player_id) AS canonical_stats,
       (SELECT COUNT(*) FROM public.player_id_map x WHERE x.old_player_id = m.old_player_id) AS map_rows
FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map m
LEFT JOIN public.players p_old ON p_old.player_id = m.old_player_id
LEFT JOIN public.players p_new ON p_new.player_id = m.player_id
ORDER BY m.old_player_id;
