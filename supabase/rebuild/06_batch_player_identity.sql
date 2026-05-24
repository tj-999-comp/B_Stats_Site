-- 作成日: 2026-05-24
-- 目的: player_id 変更追跡関連を一括適用する（Step7,8,11 の統合）

-- players: 旧ID保持カラム
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS old_player_id TEXT;

-- 旧 migration で player_id_aliases が残っている場合にのみリネーム
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'player_id_aliases'
    ) THEN
        EXECUTE 'ALTER TABLE player_id_aliases RENAME TO player_id_map';
    END IF;
END $$;

-- player_id_map が未作成なら作成
CREATE TABLE IF NOT EXISTS player_id_map (
    old_player_id TEXT PRIMARY KEY,
    player_id     TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    note          TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_id_map_player_id
    ON player_id_map(player_id);

-- 旧列名があるケースを新列へ統一
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'player_id_map'
          AND column_name = 'alias_id'
    ) THEN
        EXECUTE 'ALTER TABLE player_id_map RENAME COLUMN alias_id TO old_player_id';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'player_id_map'
          AND column_name = 'canonical_player_id'
    ) THEN
        EXECUTE 'ALTER TABLE player_id_map RENAME COLUMN canonical_player_id TO player_id';
    END IF;
END $$;

-- players.player_id 更新時に関連テーブルへ連鎖するよう FK を再定義
ALTER TABLE player_game_stats
    DROP CONSTRAINT IF EXISTS player_game_stats_player_id_fkey,
    ADD CONSTRAINT player_game_stats_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE player_name_history
    DROP CONSTRAINT IF EXISTS player_name_history_player_id_fkey,
    ADD CONSTRAINT player_name_history_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE player_affiliations
    DROP CONSTRAINT IF EXISTS player_affiliations_player_id_fkey,
    ADD CONSTRAINT player_affiliations_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE CASCADE;
