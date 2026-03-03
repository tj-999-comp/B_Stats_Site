-- games テーブルに game_datetime カラム（JST, YYYY-MM-DD HH:MM 形式）を追加
ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_datetime TEXT;
