-- 作成日: 2026-05-24
-- 目的: games / players の付加カラムを一括適用する（Step4,5,6,9 の統合）

-- games: 日時・日付・試合区分
ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_datetime TEXT;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_date TEXT;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_type TEXT;

-- players: プロフィール項目
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS player_slot_category TEXT;

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS league_registered_nationality TEXT;

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS birthplace TEXT;

-- 既存データがある場合のみ game_type をバックフィル
UPDATE games
SET game_type = CASE
    WHEN setu::integer <= 100 THEN 'RS'
    ELSE 'CS'
END
WHERE setu IS NOT NULL;
