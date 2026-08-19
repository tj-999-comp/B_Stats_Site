-- Issue #25: verify player profile patch
-- Date: 2026-08-20
-- Run after backup, before fix, after fix, and after rollback.
-- Read-only against public.players.

BEGIN;

DO $issue_25_profile_verify_guard$
DECLARE backup_rows INTEGER; patch_rows INTEGER; target_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260820_issue25_player_profiles') IS NULL
       OR TO_REGCLASS('public.data_patch_issue25_player_profiles') IS NULL THEN
        RAISE EXCEPTION 'Issue #25 profile backup and patch tables are required';
    END IF;
    SELECT COUNT(*) INTO backup_rows FROM public.data_patch_backup_20260820_issue25_player_profiles;
    SELECT COUNT(*) INTO patch_rows FROM public.data_patch_issue25_player_profiles;
    SELECT COUNT(*) INTO target_rows
      FROM public.players p JOIN public.data_patch_issue25_player_profiles patch USING (player_id);
    IF backup_rows <> 281 OR patch_rows <> 281 OR target_rows <> 281 THEN
        RAISE EXCEPTION 'row count mismatch: backup=% patch=% target=%', backup_rows, patch_rows, target_rows;
    END IF;
END;
$issue_25_profile_verify_guard$;

WITH expected AS (
    SELECT b.player_id,
           b.player_name_j,
           b.player_name_e,
           CASE WHEN NULLIF(patch.proposed_league_registered_nationality, '') IS NOT NULL
                     AND NULLIF(b.league_registered_nationality, '') IS NULL
                THEN patch.proposed_league_registered_nationality
                ELSE b.league_registered_nationality END AS league_registered_nationality,
           CASE WHEN NULLIF(patch.proposed_birthplace, '') IS NOT NULL
                     AND NULLIF(b.birthplace, '') IS NULL
                THEN patch.proposed_birthplace
                ELSE b.birthplace END AS birthplace,
           patch.normalized_player_slot_category
      FROM public.data_patch_backup_20260820_issue25_player_profiles b
      JOIN public.data_patch_issue25_player_profiles patch USING (player_id)
), current_state AS (
    SELECT p.player_id, p.player_name_j, p.player_name_e,
           p.league_registered_nationality, p.birthplace,
           p.player_slot_category,
           b.player_name_j AS backup_player_name_j,
           b.player_name_e AS backup_player_name_e,
           b.league_registered_nationality AS backup_league_registered_nationality,
           b.birthplace AS backup_birthplace,
           b.player_slot_category AS backup_player_slot_category
      FROM public.players p
      JOIN public.data_patch_backup_20260820_issue25_player_profiles b USING (player_id)
), summary AS (
    SELECT
      COUNT(*) AS target_rows,
      COUNT(*) FILTER (WHERE current_state.player_name_j IS DISTINCT FROM current_state.backup_player_name_j
                         OR current_state.player_name_e IS DISTINCT FROM current_state.backup_player_name_e
                         OR current_state.league_registered_nationality IS DISTINCT FROM current_state.backup_league_registered_nationality
                         OR current_state.birthplace IS DISTINCT FROM current_state.backup_birthplace
                         OR current_state.player_slot_category IS DISTINCT FROM current_state.backup_player_slot_category) AS before_mismatches,
      COUNT(*) FILTER (WHERE current_state.player_name_j IS DISTINCT FROM expected.player_name_j
                         OR current_state.player_name_e IS DISTINCT FROM expected.player_name_e
                         OR current_state.league_registered_nationality IS DISTINCT FROM expected.league_registered_nationality
                         OR current_state.birthplace IS DISTINCT FROM expected.birthplace
                         OR current_state.player_slot_category IS DISTINCT FROM expected.normalized_player_slot_category) AS after_mismatches,
      COUNT(*) FILTER (WHERE expected.league_registered_nationality IS DISTINCT FROM current_state.backup_league_registered_nationality
                         OR expected.birthplace IS DISTINCT FROM current_state.backup_birthplace
                         OR expected.normalized_player_slot_category IS DISTINCT FROM current_state.backup_player_slot_category) AS expected_changed_rows,
      COUNT(*) FILTER (WHERE current_state.player_slot_category IN ('日本人選手','外国籍選手','帰化選手')) AS standardized_category_rows
    FROM current_state
    JOIN expected USING (player_id)
)
SELECT 'ISSUE25_PROFILE' AS check_name, target_rows, before_mismatches,
       after_mismatches, expected_changed_rows, standardized_category_rows
  FROM summary;

COMMIT;
