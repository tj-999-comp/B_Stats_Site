-- Issue #21: backup of player profile patch targets
-- Date: 2026-08-13
-- Related issues: #12, #21
-- Source: supabase/patches/20260813_issue21_missing_player_profiles.csv
-- Scope: 117 players; blank source cells are retained in the source CSV.
-- Run this file first. It does not update or delete rows from public.players.
-- Re-run guard: the persistent backup table must be inspected before replacement.

DO $issue_21_backup$
DECLARE
    target_rows INTEGER;
    backup_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260813_issue_21_player_profiles') IS NOT NULL THEN
        RAISE EXCEPTION 'Issue #21 backup table already exists; inspect before re-running';
    END IF;

    CREATE TEMP TABLE issue_21_profile_ids (
        player_id TEXT PRIMARY KEY
    ) ON COMMIT DROP;

    INSERT INTO issue_21_profile_ids (player_id) VALUES
    ('8469'),
    ('8520'),
    ('8594'),
    ('8596'),
    ('8651'),
    ('8689'),
    ('8835'),
    ('9382'),
    ('9392'),
    ('9431'),
    ('9474'),
    ('9476'),
    ('9477'),
    ('9478'),
    ('9479'),
    ('9480'),
    ('9481'),
    ('9482'),
    ('9483'),
    ('9484'),
    ('9485'),
    ('9486'),
    ('10256'),
    ('12642'),
    ('18429'),
    ('20033'),
    ('25149'),
    ('26909'),
    ('33042'),
    ('40153'),
    ('45848'),
    ('45849'),
    ('45850'),
    ('45851'),
    ('45852'),
    ('45853'),
    ('45854'),
    ('45855'),
    ('45856'),
    ('45857'),
    ('45858'),
    ('45859'),
    ('45860'),
    ('45861'),
    ('45862'),
    ('45863'),
    ('45864'),
    ('45865'),
    ('45866'),
    ('45867'),
    ('45868'),
    ('45869'),
    ('45870'),
    ('45871'),
    ('52433'),
    ('51000114'),
    ('51000161'),
    ('51000192'),
    ('51000218'),
    ('51000219'),
    ('51000225'),
    ('51000226'),
    ('51000229'),
    ('51000241'),
    ('51000261'),
    ('51000262'),
    ('51000321'),
    ('51000334'),
    ('51000340'),
    ('51000352'),
    ('51000359'),
    ('51000369'),
    ('51000533'),
    ('51000578'),
    ('55000009'),
    ('55000015'),
    ('55000067'),
    ('55000076'),
    ('55000077'),
    ('55000174'),
    ('55000219'),
    ('55000308'),
    ('55000363'),
    ('55000423'),
    ('55000424'),
    ('55000450'),
    ('55000453'),
    ('55000463'),
    ('55000510'),
    ('55000565'),
    ('55000566'),
    ('55000569'),
    ('55000570'),
    ('55000571'),
    ('55000572'),
    ('55000574'),
    ('55000576'),
    ('55000752'),
    ('55000811'),
    ('55000818'),
    ('55000826'),
    ('55000845'),
    ('55000868'),
    ('55000960'),
    ('55000961'),
    ('55000963'),
    ('55000964'),
    ('55000973'),
    ('55000974'),
    ('55000975'),
    ('55000976'),
    ('55000977'),
    ('55000978'),
    ('55000979'),
    ('55000980'),
    ('55000981'),
    ('5100000064');

    IF EXISTS (
        SELECT 1
          FROM issue_21_profile_ids
         WHERE player_id IN ('45873', '999999999')
    ) THEN
        RAISE EXCEPTION 'Issue #12 excluded staff/dummy ID is present in backup target';
    END IF;

    SELECT COUNT(*) INTO target_rows
      FROM public.players p
      JOIN issue_21_profile_ids i USING (player_id);
    IF target_rows <> 117 THEN
        RAISE EXCEPTION 'backup target row count mismatch: expected=117 actual=%', target_rows;
    END IF;

    CREATE TABLE public.data_patch_backup_20260813_issue_21_player_profiles AS
        SELECT p.* FROM public.players p WHERE FALSE;

    INSERT INTO public.data_patch_backup_20260813_issue_21_player_profiles
        SELECT p.*
          FROM public.players p
          JOIN issue_21_profile_ids i USING (player_id);

    SELECT COUNT(*) INTO backup_rows
      FROM public.data_patch_backup_20260813_issue_21_player_profiles;
    IF backup_rows <> 117 THEN
        RAISE EXCEPTION 'backup row count mismatch: expected=117 actual=%', backup_rows;
    END IF;

    REVOKE ALL ON TABLE public.data_patch_backup_20260813_issue_21_player_profiles
        FROM anon, authenticated;
END;
$issue_21_backup$;

SELECT 'player_profiles' AS backup_scope, COUNT(*) AS row_count
  FROM public.data_patch_backup_20260813_issue_21_player_profiles;
