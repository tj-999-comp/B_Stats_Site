-- games テーブルに game_date カラム（JST, YYYY-MM-DD 形式）を追加
ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_date TEXT;
