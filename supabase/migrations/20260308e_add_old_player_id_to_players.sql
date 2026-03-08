-- players テーブルに old_player_id カラムを追加する
-- PlayerID が変わった選手の旧IDを保持する（参照用）

ALTER TABLE players
  ADD COLUMN IF NOT EXISTS old_player_id TEXT;
