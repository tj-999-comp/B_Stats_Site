-- player_id_aliases テーブルの列名・テーブル名をわかりやすくリネームする
-- alias_id          → old_player_id
-- canonical_player_id → player_id
-- player_id_aliases → player_id_map

ALTER TABLE player_id_aliases RENAME TO player_id_map;
ALTER TABLE player_id_map RENAME COLUMN alias_id TO old_player_id;
ALTER TABLE player_id_map RENAME COLUMN canonical_player_id TO player_id;
