-- Issue #13: backup non-canonical player_slot_category values.
-- Date: 2026-08-20
-- Run before the verify/fix SQL. NULL means unconfirmed and is not targeted.

DO $issue_13_backup$
DECLARE
    target_rows INTEGER;
    backup_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260820_issue13_player_slot_category') IS NOT NULL THEN
        RAISE EXCEPTION 'Issue #13 backup table already exists; inspect before re-running';
    END IF;

    SELECT COUNT(*) INTO target_rows
      FROM public.players
     WHERE player_slot_category IN ('日本', '帰化選手枠');
    IF target_rows = 0 THEN
        RAISE EXCEPTION 'no non-canonical player_slot_category rows remain';
    END IF;

    CREATE TABLE public.data_patch_backup_20260820_issue13_player_slot_category AS
        SELECT p.*
          FROM public.players p
         WHERE p.player_slot_category IN ('日本', '帰化選手枠');

    SELECT COUNT(*) INTO backup_rows
      FROM public.data_patch_backup_20260820_issue13_player_slot_category;
    IF backup_rows <> target_rows THEN
        RAISE EXCEPTION 'backup row count mismatch: target=% backup=%', target_rows, backup_rows;
    END IF;
END;
$issue_13_backup$;

SELECT player_slot_category, COUNT(*) AS row_count
  FROM public.data_patch_backup_20260820_issue13_player_slot_category
 GROUP BY player_slot_category
 ORDER BY player_slot_category;
