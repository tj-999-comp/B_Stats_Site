-- Issue #25: rollback player profile patch
-- Date: 2026-08-20
-- Run only after the post-fix state has been verified.
-- Restores the profile columns covered by this patch from the backup snapshot.

BEGIN;

DO $issue_25_profile_rollback$
DECLARE
    backup_rows INTEGER; patch_rows INTEGER; target_rows INTEGER;
    post_mismatches INTEGER; changed_rows INTEGER; restored_rows INTEGER;
    rollback_mismatches INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260820_issue25_player_profiles') IS NULL
       OR TO_REGCLASS('public.data_patch_issue25_player_profiles') IS NULL THEN
        RAISE EXCEPTION 'Issue #25 backup and patch tables are required';
    END IF;

    SELECT COUNT(*) INTO backup_rows FROM public.data_patch_backup_20260820_issue25_player_profiles;
    SELECT COUNT(*) INTO patch_rows FROM public.data_patch_issue25_player_profiles;
    SELECT COUNT(*) INTO target_rows
      FROM public.players p JOIN public.data_patch_issue25_player_profiles patch USING (player_id);
    IF backup_rows <> 281 OR patch_rows <> 281 OR target_rows <> 281 THEN
        RAISE EXCEPTION 'row count mismatch: backup=% patch=% target=%', backup_rows, patch_rows, target_rows;
    END IF;

    SELECT COUNT(*) INTO post_mismatches
      FROM public.players p
      JOIN public.data_patch_issue25_player_profiles patch USING (player_id)
      JOIN public.data_patch_backup_20260820_issue25_player_profiles b USING (player_id)
     WHERE p.player_name_j IS DISTINCT FROM b.player_name_j
        OR p.player_name_e IS DISTINCT FROM b.player_name_e
        OR p.league_registered_nationality IS DISTINCT FROM
           CASE WHEN NULLIF(patch.proposed_league_registered_nationality, '') IS NOT NULL
                     AND NULLIF(b.league_registered_nationality, '') IS NULL
                THEN patch.proposed_league_registered_nationality ELSE b.league_registered_nationality END
        OR p.birthplace IS DISTINCT FROM
           CASE WHEN NULLIF(patch.proposed_birthplace, '') IS NOT NULL
                     AND NULLIF(b.birthplace, '') IS NULL
                THEN patch.proposed_birthplace ELSE b.birthplace END
        OR p.player_slot_category IS DISTINCT FROM patch.normalized_player_slot_category
        OR p.old_player_id IS DISTINCT FROM b.old_player_id
        OR p.created_at IS DISTINCT FROM b.created_at;
    IF post_mismatches <> 0 THEN
        RAISE EXCEPTION 'rollback target is not the expected post-fix state: % rows', post_mismatches;
    END IF;

    SELECT COUNT(*) INTO changed_rows
      FROM public.players p
      JOIN public.data_patch_backup_20260820_issue25_player_profiles b USING (player_id)
     WHERE p.league_registered_nationality IS DISTINCT FROM b.league_registered_nationality
        OR p.birthplace IS DISTINCT FROM b.birthplace
        OR p.player_slot_category IS DISTINCT FROM b.player_slot_category;
    IF changed_rows = 0 THEN
        RAISE EXCEPTION 'Issue #25 profile fix does not appear to be applied';
    END IF;

    UPDATE public.players p
       SET player_slot_category = b.player_slot_category,
           league_registered_nationality = b.league_registered_nationality,
           birthplace = b.birthplace,
           updated_at = b.updated_at
      FROM public.data_patch_backup_20260820_issue25_player_profiles b
     WHERE p.player_id = b.player_id;

    GET DIAGNOSTICS restored_rows = ROW_COUNT;
    IF restored_rows <> 281 THEN
        RAISE EXCEPTION 'rollback restore count mismatch: expected=281 actual=%', restored_rows;
    END IF;

    SELECT COUNT(*) INTO rollback_mismatches
      FROM public.players p
      JOIN public.data_patch_backup_20260820_issue25_player_profiles b USING (player_id)
     WHERE p.player_slot_category IS DISTINCT FROM b.player_slot_category
        OR p.league_registered_nationality IS DISTINCT FROM b.league_registered_nationality
        OR p.birthplace IS DISTINCT FROM b.birthplace
        OR p.updated_at IS DISTINCT FROM b.updated_at;
    IF rollback_mismatches <> 0 THEN
        RAISE EXCEPTION 'rollback postcheck mismatch: % rows', rollback_mismatches;
    END IF;
END;
$issue_25_profile_rollback$;

SELECT 'restored_player_profiles' AS check_name, COUNT(*) AS row_count
  FROM public.players p
  JOIN public.data_patch_backup_20260820_issue25_player_profiles b USING (player_id);

COMMIT;
