-- Issue #13: restore player_slot_category from the persistent backup.
-- Run only when the normalized result is rejected.

BEGIN;

DO $issue_13_rollback$
DECLARE
    backup_rows INTEGER;
    updated_rows INTEGER;
    unexpected_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260820_issue13_player_slot_category') IS NULL THEN
        RAISE EXCEPTION 'Issue #13 backup table is required';
    END IF;

    SELECT COUNT(*) INTO backup_rows
      FROM public.data_patch_backup_20260820_issue13_player_slot_category;
    SELECT COUNT(*) INTO unexpected_rows
      FROM public.players p
      JOIN public.data_patch_backup_20260820_issue13_player_slot_category b USING (player_id)
     WHERE p.player_slot_category IS DISTINCT FROM CASE b.player_slot_category
           WHEN '日本' THEN '日本人選手'
           WHEN '帰化選手枠' THEN '帰化選手'
           ELSE b.player_slot_category
       END;
    IF unexpected_rows <> 0 THEN
        RAISE EXCEPTION 'target rows are not in expected post-fix state: % rows', unexpected_rows;
    END IF;

    ALTER TABLE public.players
        DROP CONSTRAINT IF EXISTS players_player_slot_category_check;

    UPDATE public.players AS p
       SET player_slot_category = b.player_slot_category
      FROM public.data_patch_backup_20260820_issue13_player_slot_category b
     WHERE p.player_id = b.player_id;
    GET DIAGNOSTICS updated_rows = ROW_COUNT;
    IF updated_rows <> backup_rows THEN
        RAISE EXCEPTION 'rollback row count mismatch: expected=% actual=%', backup_rows, updated_rows;
    END IF;
END;
$issue_13_rollback$;

SELECT player_slot_category, COUNT(*) AS row_count
  FROM public.data_patch_backup_20260820_issue13_player_slot_category
 GROUP BY player_slot_category
 ORDER BY player_slot_category;

COMMIT;
