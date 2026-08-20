-- Issue #13: read-only verification for player_slot_category normalization.
-- Run after backup, before/after fix, and after rollback.

BEGIN;

DO $issue_13_verify_guard$
DECLARE backup_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260820_issue13_player_slot_category') IS NULL THEN
        RAISE EXCEPTION 'Issue #13 backup table is required';
    END IF;
    SELECT COUNT(*) INTO backup_rows
      FROM public.data_patch_backup_20260820_issue13_player_slot_category;
    IF backup_rows = 0 THEN
        RAISE EXCEPTION 'Issue #13 backup table is empty';
    END IF;
END;
$issue_13_verify_guard$;

WITH expected AS (
    SELECT player_id,
           player_slot_category AS backup_category,
           CASE player_slot_category
               WHEN '日本' THEN '日本人選手'
               WHEN '帰化選手枠' THEN '帰化選手'
           END AS expected_category
      FROM public.data_patch_backup_20260820_issue13_player_slot_category
), current_state AS (
    SELECT e.player_id, e.backup_category, e.expected_category,
           p.player_slot_category AS current_category
      FROM expected e
      LEFT JOIN public.players p USING (player_id)
), summary AS (
    SELECT COUNT(*) AS target_rows,
           COUNT(*) FILTER (WHERE current_category IS NULL) AS missing_rows,
           COUNT(*) FILTER (WHERE current_category IS DISTINCT FROM backup_category) AS changed_from_backup,
           COUNT(*) FILTER (WHERE current_category IS DISTINCT FROM expected_category) AS not_normalized_rows,
           COUNT(*) FILTER (WHERE current_category IN ('日本人選手','外国籍選手','帰化選手')) AS canonical_target_rows
      FROM current_state
)
SELECT 'ISSUE13_PLAYER_SLOT_CATEGORY' AS check_name,
       target_rows, missing_rows, changed_from_backup,
       not_normalized_rows, canonical_target_rows,
       EXISTS (
           SELECT 1
             FROM pg_constraint c
             JOIN pg_class t ON t.oid = c.conrelid
             JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
              AND t.relname = 'players'
              AND c.conname = 'players_player_slot_category_check'
       ) AS category_check_exists,
       (
           SELECT pg_get_constraintdef(c.oid)
             FROM pg_constraint c
             JOIN pg_class t ON t.oid = c.conrelid
             JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
              AND t.relname = 'players'
              AND c.conname = 'players_player_slot_category_check'
       ) AS category_check_definition
  FROM summary;

SELECT player_slot_category, COUNT(*) AS row_count
  FROM public.players
 GROUP BY player_slot_category
 ORDER BY player_slot_category NULLS LAST;

COMMIT;
