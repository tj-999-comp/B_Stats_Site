-- Issue #25: player_id重複統合のバックアップ
-- 作成日: 2026-08-19
-- 実行順: 本SQL → 20260819_verify_issue25_player_id_merge.sql → fix
-- 注意: live DBを変更するのはバックアップ表の作成だけ。既存のバックアップ表があれば停止する。

DO $issue_25_backup$
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_id_merge_map') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_players') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_game_stats') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_name_history') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_affiliations') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260819_issue_25_player_id_map') IS NOT NULL THEN
        RAISE EXCEPTION 'Issue #25 backup table already exists; inspect before re-running';
    END IF;
END;
$issue_25_backup$;

DO $issue_25_backup$
DECLARE
    mapping_rows BIGINT;
    player_rows BIGINT;
    stat_rows BIGINT;
    name_rows BIGINT;
    affiliation_rows BIGINT;
    id_map_rows BIGINT;
BEGIN
    CREATE TEMP TABLE issue_25_player_id_map (
        old_player_id TEXT PRIMARY KEY,
        player_id TEXT UNIQUE NOT NULL,
        player_name_j TEXT NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO issue_25_player_id_map (old_player_id, player_id, player_name_j) VALUES
        ('45848', '5100000069', 'レイ・パークスジュニア'),
        ('45849', '51000259', 'カイ・ソット'),
        ('45850', '51000332', 'チュアンシン・リュウ'),
        ('45851', '5100000062', 'キーファー・ラベナ'),
        ('45852', '51000102', 'ドワイト・ラモス'),
        ('45853', '51000185', 'グレゴリー・スローター'),
        ('45854', '51000306', 'チャン ミンクク'),
        ('45855', '51000260', 'カール・タマヨ'),
        ('45856', '51000333', 'シェンゼ・リー'),
        ('45857', '51000314', 'イ デソン'),
        ('45858', '51000324', '劉 駿霆'),
        ('45859', '51000187', 'マシュー・ライト'),
        ('45860', '51000308', 'ロン･ジェイ･アバリエントス'),
        ('45861', '5100000041', '王 偉嘉'),
        ('45862', '5100000012', '荒谷 裕秀'),
        ('45863', '51000137', '上田 隼輔'),
        ('45864', '51000113', '飯尾 文哉'),
        ('45865', '5100000024', 'キング 開');

    SELECT COUNT(*) INTO mapping_rows FROM issue_25_player_id_map;
    IF mapping_rows <> 18 THEN
        RAISE EXCEPTION 'unexpected mapping rows: %', mapping_rows;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM issue_25_player_id_map m
        WHERE NOT EXISTS (SELECT 1 FROM public.players p WHERE p.player_id = m.old_player_id)
           OR NOT EXISTS (SELECT 1 FROM public.players p WHERE p.player_id = m.player_id)
    ) THEN
        RAISE EXCEPTION 'one or more old/canonical player IDs are missing';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM issue_25_player_id_map m
        JOIN public.players p_old ON p_old.player_id = m.old_player_id
        JOIN public.players p_new ON p_new.player_id = m.player_id
        WHERE replace(replace(p_old.player_name_j, ' ', ''), '　', '') IS DISTINCT FROM replace(replace(m.player_name_j, ' ', ''), '　', '')
           OR replace(replace(p_new.player_name_j, ' ', ''), '　', '') IS DISTINCT FROM replace(replace(m.player_name_j, ' ', ''), '　', '')
           OR (p_new.old_player_id IS NOT NULL AND p_new.old_player_id IS DISTINCT FROM m.old_player_id)
    ) THEN
        RAISE EXCEPTION 'player name or existing old_player_id does not match the reviewed mapping';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.player_game_stats old_stats
        JOIN issue_25_player_id_map m ON m.old_player_id = old_stats.player_id
        JOIN public.player_game_stats new_stats
          ON new_stats.player_id = m.player_id
         AND new_stats.schedule_key = old_stats.schedule_key
    ) THEN
        RAISE EXCEPTION 'player_game_stats primary-key conflict exists before merge';
    END IF;

    SELECT COUNT(*) INTO id_map_rows
      FROM public.player_id_map x
      JOIN issue_25_player_id_map m ON m.old_player_id = x.old_player_id;
    IF id_map_rows <> 0 THEN
        RAISE EXCEPTION 'target old IDs already exist in player_id_map: %', id_map_rows;
    END IF;

    CREATE TABLE public.data_patch_backup_20260819_issue_25_player_id_merge_map AS
        SELECT * FROM issue_25_player_id_map;
    CREATE TABLE public.data_patch_backup_20260819_issue_25_players AS
        SELECT p.*
        FROM public.players p
        WHERE p.player_id IN (SELECT old_player_id FROM issue_25_player_id_map)
           OR p.player_id IN (SELECT player_id FROM issue_25_player_id_map);
    CREATE TABLE public.data_patch_backup_20260819_issue_25_player_game_stats AS
        SELECT s.*
        FROM public.player_game_stats s
        WHERE s.player_id IN (SELECT old_player_id FROM issue_25_player_id_map)
           OR s.player_id IN (SELECT player_id FROM issue_25_player_id_map);
    CREATE TABLE public.data_patch_backup_20260819_issue_25_player_name_history AS
        SELECT h.*
        FROM public.player_name_history h
        WHERE h.player_id IN (SELECT old_player_id FROM issue_25_player_id_map)
           OR h.player_id IN (SELECT player_id FROM issue_25_player_id_map);
    CREATE TABLE public.data_patch_backup_20260819_issue_25_player_affiliations AS
        SELECT a.*
        FROM public.player_affiliations a
        WHERE a.player_id IN (SELECT old_player_id FROM issue_25_player_id_map)
           OR a.player_id IN (SELECT player_id FROM issue_25_player_id_map);
    CREATE TABLE public.data_patch_backup_20260819_issue_25_player_id_map AS
        SELECT x.*
        FROM public.player_id_map x
        WHERE x.old_player_id IN (SELECT old_player_id FROM issue_25_player_id_map);

    SELECT COUNT(*) INTO player_rows FROM public.data_patch_backup_20260819_issue_25_players;
    IF player_rows <> 36 THEN
        RAISE EXCEPTION 'players backup row mismatch: expected=36 actual=%', player_rows;
    END IF;

    SELECT COUNT(*) INTO stat_rows FROM public.data_patch_backup_20260819_issue_25_player_game_stats;
    SELECT COUNT(*) INTO name_rows FROM public.data_patch_backup_20260819_issue_25_player_name_history;
    SELECT COUNT(*) INTO affiliation_rows FROM public.data_patch_backup_20260819_issue_25_player_affiliations;

    RAISE NOTICE 'Issue #25 backup complete: mappings=%, players=%, stats=%, name_history=%, affiliations=%',
        mapping_rows, player_rows, stat_rows, name_rows, affiliation_rows;
END;
$issue_25_backup$;

SELECT 'mapping' AS item, COUNT(*) AS row_count FROM public.data_patch_backup_20260819_issue_25_player_id_merge_map
UNION ALL SELECT 'players', COUNT(*) FROM public.data_patch_backup_20260819_issue_25_players
UNION ALL SELECT 'player_game_stats', COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_game_stats
UNION ALL SELECT 'player_name_history', COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_name_history
UNION ALL SELECT 'player_affiliations', COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_affiliations
UNION ALL SELECT 'existing_player_id_map_rows', COUNT(*) FROM public.data_patch_backup_20260819_issue_25_player_id_map;
