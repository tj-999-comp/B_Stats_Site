-- ============================================================
-- 試合関連データ全削除 SQL
-- 対象: player_game_stats, game_team_stats,
--       player_affiliations, player_name_history, games
-- 残すもの: teams, players, player_id_map
-- ※ play_by_play は運用上使用しないため対象外
-- ============================================================
-- 実行前に必ずバックアップ（Supabaseスナップショット）を取ること
-- ============================================================

BEGIN;

-- 1. games を参照する子テーブルから先に削除
DELETE FROM player_game_stats;
DELETE FROM game_team_stats;

-- 2. games を参照している player_affiliations を削除
--    (first_schedule_key / last_schedule_key が games を参照、CASCADE なし)
DELETE FROM player_affiliations;

-- 3. player_name_history を削除
DELETE FROM player_name_history;

-- 4. games 本体を削除
DELETE FROM games;

COMMIT;