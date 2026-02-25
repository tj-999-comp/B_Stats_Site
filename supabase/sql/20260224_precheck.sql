-- Pre-check for migration 20260224_identity_history
-- Read-only queries

-- 1) required base tables
SELECT
  table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('teams', 'players', 'games', 'player_game_stats')
ORDER BY table_name;

-- 2) object existence before apply
SELECT
  'table' AS object_type,
  table_name AS object_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('team_name_history', 'player_name_history', 'player_affiliations')
UNION ALL
SELECT
  'view' AS object_type,
  table_name AS object_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('v_teams_current', 'v_players_current', 'v_player_transfer_events')
ORDER BY object_type, object_name;

-- 3) current data volume
SELECT 'teams' AS table_name, COUNT(*) AS row_count FROM teams
UNION ALL
SELECT 'players' AS table_name, COUNT(*) AS row_count FROM players
UNION ALL
SELECT 'player_game_stats' AS table_name, COUNT(*) AS row_count FROM player_game_stats;
