-- Issue #13: normalize player_slot_category to the three canonical values.
-- Date: 2026-08-20
-- NULL is retained for unconfirmed/missing classification.

BEGIN;

DO $issue_13_fix$
DECLARE
    backup_rows INTEGER;
    updated_rows INTEGER;
    remaining_noncanonical INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260820_issue13_player_slot_category') IS NULL THEN
        RAISE EXCEPTION 'Issue #13 backup table is required';
    END IF;

    SELECT COUNT(*) INTO backup_rows
      FROM public.data_patch_backup_20260820_issue13_player_slot_category;
    IF backup_rows = 0 THEN
        RAISE EXCEPTION 'Issue #13 backup table is empty';
    END IF;

    SELECT COUNT(*) INTO remaining_noncanonical
      FROM public.players
     WHERE player_slot_category IS NOT NULL
       AND player_slot_category NOT IN ('日本人選手', '外国籍選手', '帰化選手', '日本', '帰化選手枠');
    IF remaining_noncanonical <> 0 THEN
        RAISE EXCEPTION 'unexpected player_slot_category values remain: % rows', remaining_noncanonical;
    END IF;

    UPDATE public.players AS p
       SET player_slot_category = CASE p.player_slot_category
           WHEN '日本' THEN '日本人選手'
           WHEN '帰化選手枠' THEN '帰化選手'
           ELSE p.player_slot_category
       END
     WHERE p.player_slot_category IN ('日本', '帰化選手枠');
    GET DIAGNOSTICS updated_rows = ROW_COUNT;
    IF updated_rows <> backup_rows THEN
        RAISE EXCEPTION 'updated row count mismatch: expected=% actual=%', backup_rows, updated_rows;
    END IF;

    ALTER TABLE public.players
        DROP CONSTRAINT IF EXISTS players_player_slot_category_check;
    ALTER TABLE public.players
        ADD CONSTRAINT players_player_slot_category_check
        CHECK (player_slot_category IS NULL OR player_slot_category IN ('日本人選手', '外国籍選手', '帰化選手'));
END;
$issue_13_fix$;

SELECT player_slot_category, COUNT(*) AS row_count
  FROM public.players
 GROUP BY player_slot_category
 ORDER BY player_slot_category NULLS LAST;

COMMIT;
