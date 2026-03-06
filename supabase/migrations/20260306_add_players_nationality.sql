-- Add optional nationality field to players.
-- Current game_detail JSON payload does not include nationality,
-- so existing and newly upserted rows can remain NULL until a source is added.

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS nationality TEXT;
