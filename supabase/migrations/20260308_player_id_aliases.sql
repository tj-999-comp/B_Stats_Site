-- player_id_map: 旧PlayerIDから現PlayerIDへのマッピングテーブル
-- 同一選手のIDが変わった場合に旧IDを記録し、player_id（新ID）へ紐付ける。
-- 合わせて既存FKに ON UPDATE CASCADE を追加し、players.player_id 更新時に連鎖反映されるようにする。

-- =========================
-- 1) player_id_map テーブル
-- =========================

CREATE TABLE IF NOT EXISTS player_id_map (
    old_player_id TEXT PRIMARY KEY,                                                    -- 旧PlayerID
    player_id     TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,       -- 現PlayerID
    note          TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_id_map_player_id
    ON player_id_map(player_id);

-- =========================
-- 2) 既存FKに ON UPDATE CASCADE を追加
--    player_id が更新された際に関連テーブルへ自動連鎖させる
-- =========================

-- player_game_stats
ALTER TABLE player_game_stats
    DROP CONSTRAINT IF EXISTS player_game_stats_player_id_fkey,
    ADD CONSTRAINT player_game_stats_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

-- player_name_history (既存: ON DELETE CASCADE のみ → ON UPDATE CASCADE を追加)
ALTER TABLE player_name_history
    DROP CONSTRAINT IF EXISTS player_name_history_player_id_fkey,
    ADD CONSTRAINT player_name_history_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE CASCADE;

-- player_affiliations (既存: ON DELETE CASCADE のみ → ON UPDATE CASCADE を追加)
ALTER TABLE player_affiliations
    DROP CONSTRAINT IF EXISTS player_affiliations_player_id_fkey,
    ADD CONSTRAINT player_affiliations_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE CASCADE;
