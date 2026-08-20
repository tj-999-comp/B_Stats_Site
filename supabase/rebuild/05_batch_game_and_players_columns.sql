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

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS entity_type TEXT NOT NULL DEFAULT 'player';

UPDATE players
SET entity_type = 'player'
WHERE entity_type IS NULL;

ALTER TABLE players
    ALTER COLUMN entity_type SET NOT NULL;

ALTER TABLE players
    DROP CONSTRAINT IF EXISTS players_entity_type_check;

ALTER TABLE players
    ADD CONSTRAINT players_entity_type_check
    CHECK (entity_type IN ('player', 'staff', 'placeholder', 'unresolved'));

UPDATE players
SET player_slot_category = CASE player_slot_category
    WHEN '日本' THEN '日本人選手'
    WHEN '帰化選手枠' THEN '帰化選手'
    ELSE player_slot_category
END
WHERE player_slot_category IN ('日本', '帰化選手枠');

ALTER TABLE players
    DROP CONSTRAINT IF EXISTS players_player_slot_category_check;

ALTER TABLE players
    ADD CONSTRAINT players_player_slot_category_check
    CHECK (player_slot_category IS NULL OR player_slot_category IN ('日本人選手', '外国籍選手', '帰化選手'));
-- 既存データがある場合のみ game_type をバックフィル
UPDATE games
SET game_type = CASE
    WHEN setu::integer <= 100 THEN 'RS'
    ELSE 'CS'
END
WHERE setu IS NOT NULL;
