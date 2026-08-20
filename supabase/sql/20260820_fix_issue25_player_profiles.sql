-- Issue #25: apply reviewed player profile patch
-- Date: 2026-08-20
-- Source: persistent patch table created by backup SQL.
-- Blank proposed nationality/birthplace values are ignored.
-- player_slot_category is normalized to the three existing terms.

BEGIN;

DO $issue_25_profile_fix$
DECLARE
    backup_rows INTEGER; patch_rows INTEGER; target_rows INTEGER;
    backup_mismatches INTEGER; ready_rows INTEGER; updated_rows INTEGER;
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

    SELECT COUNT(*) INTO backup_mismatches
      FROM public.players p
      JOIN public.data_patch_backup_20260820_issue25_player_profiles b USING (player_id)
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
    IF backup_mismatches <> 0 THEN
        RAISE EXCEPTION 'target rows changed after backup: % rows', backup_mismatches;
    END IF;

    SELECT COUNT(*) INTO ready_rows
      FROM public.players p
      JOIN public.data_patch_issue25_player_profiles patch USING (player_id)
     WHERE (NULLIF(p.league_registered_nationality, '') IS NULL
            AND NULLIF(patch.proposed_league_registered_nationality, '') IS NOT NULL)
        OR (NULLIF(p.birthplace, '') IS NULL
            AND NULLIF(patch.proposed_birthplace, '') IS NOT NULL)
        OR p.player_slot_category IS DISTINCT FROM patch.normalized_player_slot_category;
    IF ready_rows = 0 THEN
        RAISE EXCEPTION 'no Issue #25 profile changes remain; fix may already be applied';
    END IF;

    UPDATE public.players AS p
       SET league_registered_nationality = CASE
               WHEN NULLIF(p.league_registered_nationality, '') IS NULL
                AND NULLIF(patch.proposed_league_registered_nationality, '') IS NOT NULL
                   THEN patch.proposed_league_registered_nationality
               ELSE p.league_registered_nationality
           END,
           birthplace = CASE
               WHEN NULLIF(p.birthplace, '') IS NULL
                AND NULLIF(patch.proposed_birthplace, '') IS NOT NULL
                   THEN patch.proposed_birthplace
               ELSE p.birthplace
           END,
           player_slot_category = patch.normalized_player_slot_category
      FROM public.data_patch_issue25_player_profiles patch
     WHERE p.player_id = patch.player_id;

    GET DIAGNOSTICS updated_rows = ROW_COUNT;
    IF updated_rows <> 281 THEN
        RAISE EXCEPTION 'updated row count mismatch: expected=281 actual=%', updated_rows;
    END IF;
END;
$issue_25_profile_fix$;

SELECT 'updated_player_profiles' AS check_name, COUNT(*) AS row_count
  FROM public.players p
  JOIN public.data_patch_issue25_player_profiles patch USING (player_id)
 WHERE p.player_slot_category = patch.normalized_player_slot_category;

COMMIT;
