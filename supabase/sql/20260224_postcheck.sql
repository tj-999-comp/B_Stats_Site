-- Post-check for migration 20260224_identity_history
-- Read-only queries

-- 1) created tables
SELECT
  table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('team_name_history', 'player_name_history', 'player_affiliations')
ORDER BY table_name;

-- 2) created views
SELECT
  table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('v_teams_current', 'v_players_current', 'v_player_transfer_events')
ORDER BY table_name;

-- 3) created triggers
SELECT
  trigger_name,
  event_object_table,
  action_timing,
  event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN (
    'trg_track_team_name_history',
    'trg_track_player_name_history',
    'trg_track_player_affiliation'
  )
ORDER BY trigger_name;

-- 4) backfill counts
SELECT 'team_name_history' AS table_name, COUNT(*) AS row_count FROM team_name_history
UNION ALL
SELECT 'player_name_history' AS table_name, COUNT(*) AS row_count FROM player_name_history
UNION ALL
SELECT 'player_affiliations' AS table_name, COUNT(*) AS row_count FROM player_affiliations;

-- 5) open rows sanity check (ideally one open row per entity)
SELECT team_id, COUNT(*) AS open_rows
FROM team_name_history
WHERE valid_to IS NULL
GROUP BY team_id
HAVING COUNT(*) > 1;

SELECT player_id, COUNT(*) AS open_rows
FROM player_name_history
WHERE valid_to IS NULL
GROUP BY player_id
HAVING COUNT(*) > 1;

SELECT player_id, COUNT(*) AS open_rows
FROM player_affiliations
WHERE valid_to IS NULL
GROUP BY player_id
HAVING COUNT(*) > 1;

-- 6) sample views
SELECT * FROM v_teams_current LIMIT 10;
SELECT * FROM v_players_current LIMIT 10;
SELECT *
FROM v_player_transfer_events
WHERE from_team_id IS NOT NULL
LIMIT 20;
