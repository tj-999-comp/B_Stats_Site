-- Issue #12: playersプロフィール補完・スタッフ行整理
-- 作成日: 2026-08-11
-- 目的: 欠損プロフィール166件を補完し、スタッフ相当47 IDとダミー1 IDに紐づく行を削除する。
-- 前提: 20260811_backup_issue_12_players.sql を先に実行し、5バックアップ表が想定件数であること。
-- 想定更新・削除件数: profile 166、players 48、player_game_stats 4060、name_history 59、affiliations 70
-- 再実行: 不可。バックアップ表が存在する状態でのみ実行でき、対象件数やupdated_atが変わると停止する。
-- 注意: SQL Editor/DBeaverではファイル全体を一括実行すること。途中のDELETEだけを抜き出さない。

DO $issue_12_apply$
DECLARE
    backup_profile_rows INTEGER;
    backup_player_rows INTEGER;
    backup_stat_rows INTEGER;
    backup_name_rows INTEGER;
    backup_affiliation_rows INTEGER;
    profile_ready_rows INTEGER;
    live_player_rows INTEGER;
    live_stat_rows INTEGER;
    live_name_rows INTEGER;
    live_affiliation_rows INTEGER;
    map_ref_rows INTEGER;
    updated_profile_rows INTEGER;
    deleted_stat_rows INTEGER;
    deleted_name_rows INTEGER;
    deleted_affiliation_rows INTEGER;
    deleted_player_rows INTEGER;
    remaining_profile_mismatches INTEGER;
    remaining_deleted_players INTEGER;
    remaining_deleted_stats INTEGER;
    remaining_deleted_names INTEGER;
    remaining_deleted_affiliations INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_profiles') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_players_deleted') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_affiliations') IS NULL THEN
        RAISE EXCEPTION 'Issue #12 backup tables are required';
    END IF;

    SELECT COUNT(*) INTO backup_profile_rows FROM public.data_patch_backup_20260811_issue_12_player_profiles;
    SELECT COUNT(*) INTO backup_player_rows FROM public.data_patch_backup_20260811_issue_12_players_deleted;
    SELECT COUNT(*) INTO backup_stat_rows FROM public.data_patch_backup_20260811_issue_12_player_game_stats;
    SELECT COUNT(*) INTO backup_name_rows FROM public.data_patch_backup_20260811_issue_12_player_name_history;
    SELECT COUNT(*) INTO backup_affiliation_rows FROM public.data_patch_backup_20260811_issue_12_player_affiliations;
    IF backup_profile_rows <> 166 OR backup_player_rows <> 48 OR backup_stat_rows <> 4060
       OR backup_name_rows <> 59 OR backup_affiliation_rows <> 70 THEN
        RAISE EXCEPTION 'backup row count mismatch: profiles=% players=% stats=% names=% affiliations=%',
            backup_profile_rows, backup_player_rows, backup_stat_rows, backup_name_rows, backup_affiliation_rows;
    END IF;

    CREATE TEMP TABLE issue_12_profile_patch (
        player_id TEXT PRIMARY KEY,
        expected_updated_at TIMESTAMPTZ,
        league_value TEXT,
        birthplace_value TEXT,
        slot_value TEXT
    ) ON COMMIT DROP;
    INSERT INTO issue_12_profile_patch (player_id, expected_updated_at, league_value, birthplace_value, slot_value) VALUES
    ('10265', '2026-06-02T09:05:13.800482+00:00', NULL, NULL, '外国籍選手'),
    ('10817', '2026-06-02T09:05:32.732371+00:00', NULL, NULL, '外国籍選手'),
    ('10819', '2026-06-02T09:05:31.283798+00:00', NULL, NULL, '外国籍選手'),
    ('10823', '2026-06-02T09:05:31.99829+00:00', NULL, NULL, '外国籍選手'),
    ('10875', '2026-06-02T09:05:34.419648+00:00', NULL, NULL, '外国籍選手'),
    ('10886', '2026-06-02T09:05:33.078438+00:00', NULL, NULL, '外国籍選手'),
    ('10887', '2026-06-02T09:05:35.497448+00:00', NULL, NULL, '外国籍選手'),
    ('10897', '2026-06-02T09:05:37.151851+00:00', NULL, NULL, '外国籍選手'),
    ('12457', '2026-06-02T09:04:48.776954+00:00', NULL, NULL, '外国籍選手'),
    ('12459', '2026-06-02T09:05:00.09309+00:00', NULL, NULL, '外国籍選手'),
    ('12507', '2026-06-02T09:04:53.143243+00:00', NULL, NULL, '外国籍選手'),
    ('12508', '2026-06-02T09:04:50.321118+00:00', NULL, NULL, '外国籍選手'),
    ('12523', '2026-06-02T09:04:52.737338+00:00', NULL, NULL, '外国籍選手'),
    ('12578', '2026-06-02T09:04:51.410925+00:00', NULL, NULL, '外国籍選手'),
    ('12579', '2026-06-02T09:04:45.686212+00:00', NULL, NULL, '外国籍選手'),
    ('12580', '2026-06-02T09:04:49.193288+00:00', NULL, NULL, '外国籍選手'),
    ('12581', '2026-06-02T09:04:46.112614+00:00', NULL, NULL, '外国籍選手'),
    ('12583', '2026-06-02T09:04:48.356374+00:00', NULL, NULL, '外国籍選手'),
    ('12584', '2026-06-02T09:04:49.85639+00:00', NULL, NULL, '外国籍選手'),
    ('12585', '2026-06-02T09:04:52.430914+00:00', NULL, NULL, '外国籍選手'),
    ('12586', '2026-06-02T09:04:52.95609+00:00', NULL, NULL, '外国籍選手'),
    ('12594', '2026-06-02T09:04:46.549266+00:00', NULL, NULL, '外国籍選手'),
    ('12595', '2026-06-02T09:04:53.446597+00:00', NULL, NULL, '外国籍選手'),
    ('12596', '2026-06-02T09:04:54.409319+00:00', NULL, NULL, '外国籍選手'),
    ('12630', '2026-06-02T09:04:45.838691+00:00', NULL, NULL, '外国籍選手'),
    ('12636', '2026-06-02T09:04:49.19333+00:00', NULL, NULL, '外国籍選手'),
    ('12637', '2026-06-02T09:04:59.68596+00:00', NULL, NULL, '日本人選手'),
    ('12640', '2026-06-02T09:04:54.246455+00:00', NULL, NULL, '外国籍選手'),
    ('12648', '2026-06-02T09:05:09.721831+00:00', NULL, NULL, '外国籍選手'),
    ('12660', '2026-06-02T09:05:09.754986+00:00', NULL, NULL, '外国籍選手'),
    ('12663', '2026-06-02T09:04:54.854642+00:00', NULL, NULL, '外国籍選手'),
    ('15805', '2026-06-02T09:04:51.356942+00:00', NULL, NULL, '外国籍選手'),
    ('15809', '2026-06-02T09:04:52.737352+00:00', NULL, NULL, '外国籍選手'),
    ('15812', '2026-06-02T09:04:53.220887+00:00', NULL, NULL, '外国籍選手'),
    ('15814', '2026-06-02T09:04:54.27535+00:00', NULL, NULL, '外国籍選手'),
    ('15845', '2026-06-02T09:04:51.615295+00:00', NULL, NULL, '外国籍選手'),
    ('15847', '2026-06-02T09:04:52.016152+00:00', NULL, NULL, '外国籍選手'),
    ('15848', '2026-06-02T09:04:53.415239+00:00', NULL, NULL, '外国籍選手'),
    ('15849', '2026-06-02T09:04:57.625248+00:00', NULL, NULL, '日本人選手'),
    ('15852', '2026-06-02T09:05:10.50405+00:00', NULL, NULL, '外国籍選手'),
    ('18168', '2026-06-02T09:05:02.551924+00:00', NULL, NULL, '外国籍選手'),
    ('18169', '2026-06-02T09:04:56.620674+00:00', NULL, NULL, '外国籍選手'),
    ('18173', '2026-06-02T09:05:06.56877+00:00', NULL, NULL, '外国籍選手'),
    ('18397', '2026-06-02T09:05:03.137867+00:00', NULL, NULL, '外国籍選手'),
    ('18426', '2026-06-02T09:04:57.772644+00:00', NULL, NULL, '外国籍選手'),
    ('18427', '2026-06-02T09:04:57.804769+00:00', NULL, NULL, '外国籍選手'),
    ('18431', '2026-06-02T09:04:55.597706+00:00', NULL, NULL, '外国籍選手'),
    ('18432', '2026-06-02T09:05:08.300798+00:00', NULL, NULL, '外国籍選手'),
    ('18436', '2026-06-02T09:05:04.334835+00:00', NULL, NULL, '外国籍選手'),
    ('18442', '2026-06-02T09:05:00.282573+00:00', NULL, NULL, '外国籍選手'),
    ('18444', '2026-06-02T09:04:59.684542+00:00', NULL, NULL, '外国籍選手'),
    ('18452', '2026-06-02T09:04:59.838892+00:00', NULL, NULL, '日本人選手'),
    ('18459', '2026-06-02T09:04:58.037422+00:00', NULL, NULL, '外国籍選手'),
    ('18473', '2026-06-02T09:04:59.902481+00:00', NULL, NULL, '外国籍選手'),
    ('18479', '2026-06-02T09:04:59.263648+00:00', NULL, NULL, '外国籍選手'),
    ('18846', '2026-06-02T09:05:01.752545+00:00', NULL, NULL, '外国籍選手'),
    ('19955', '2026-06-02T09:05:02.784527+00:00', NULL, NULL, '外国籍選手'),
    ('19958', '2026-06-02T09:04:59.685952+00:00', NULL, NULL, '外国籍選手'),
    ('19995', '2026-06-02T09:04:59.305012+00:00', NULL, NULL, '外国籍選手'),
    ('19997', '2026-06-02T09:04:59.456049+00:00', NULL, NULL, '外国籍選手'),
    ('20020', '2026-06-02T09:05:02.333696+00:00', NULL, NULL, '外国籍選手'),
    ('20032', '2026-06-02T09:05:02.736966+00:00', NULL, NULL, '外国籍選手'),
    ('22396', '2026-06-02T09:05:02.705466+00:00', NULL, NULL, '外国籍選手'),
    ('22400', '2026-06-02T09:05:02.100261+00:00', NULL, NULL, '外国籍選手'),
    ('22404', '2026-06-02T09:05:09.800133+00:00', NULL, NULL, '外国籍選手'),
    ('22522', '2026-06-02T09:04:49.856377+00:00', NULL, NULL, '外国籍選手'),
    ('25136', '2026-06-02T09:05:08.028878+00:00', NULL, NULL, '外国籍選手'),
    ('26825', '2026-06-02T09:05:04.677288+00:00', NULL, NULL, '外国籍選手'),
    ('26826', '2026-06-02T09:05:06.602059+00:00', NULL, NULL, '外国籍選手'),
    ('26875', '2026-06-02T09:05:07.167192+00:00', NULL, NULL, '外国籍選手'),
    ('26892', '2026-06-02T09:05:05.042395+00:00', NULL, NULL, '外国籍選手'),
    ('26893', '2026-06-02T09:05:04.469699+00:00', NULL, NULL, '外国籍選手'),
    ('26897', '2026-06-02T09:05:05.222763+00:00', NULL, NULL, '外国籍選手'),
    ('26898', '2026-06-02T09:05:04.435344+00:00', NULL, NULL, '外国籍選手'),
    ('26910', '2026-06-02T09:05:03.115897+00:00', NULL, NULL, '外国籍選手'),
    ('26911', '2026-06-02T09:05:06.881111+00:00', NULL, NULL, '外国籍選手'),
    ('26915', '2026-06-02T09:05:04.836326+00:00', NULL, NULL, '外国籍選手'),
    ('26916', '2026-06-02T09:05:07.155633+00:00', NULL, NULL, '外国籍選手'),
    ('26928', '2026-06-02T09:05:15.458275+00:00', NULL, NULL, '外国籍選手'),
    ('26931', '2026-06-02T09:05:05.395712+00:00', NULL, NULL, '外国籍選手'),
    ('26938', '2026-06-02T09:05:05.19045+00:00', NULL, NULL, '外国籍選手'),
    ('27051', '2026-06-02T09:05:06.824845+00:00', NULL, NULL, '外国籍選手'),
    ('30393', '2026-06-02T09:05:06.290381+00:00', NULL, NULL, '外国籍選手'),
    ('30435', '2026-06-02T09:05:07.155645+00:00', NULL, NULL, '外国籍選手'),
    ('32952', '2026-06-02T09:05:15.880459+00:00', NULL, NULL, '外国籍選手'),
    ('32981', '2026-06-02T09:05:14.328671+00:00', NULL, NULL, '外国籍選手'),
    ('32983', '2026-06-02T09:05:14.034531+00:00', NULL, NULL, '日本人選手'),
    ('32990', '2026-06-02T09:05:11.335319+00:00', NULL, NULL, '外国籍選手'),
    ('32994', '2026-06-02T09:05:08.725081+00:00', NULL, NULL, '外国籍選手'),
    ('33030', '2026-06-02T09:05:15.802551+00:00', NULL, NULL, '外国籍選手'),
    ('33031', '2026-06-02T09:05:12.429906+00:00', NULL, NULL, '外国籍選手'),
    ('33037', '2026-06-02T09:05:16.850595+00:00', NULL, NULL, '外国籍選手'),
    ('33045', '2026-06-02T09:05:10.921021+00:00', NULL, NULL, '外国籍選手'),
    ('33093', '2026-06-02T09:05:12.702319+00:00', NULL, NULL, '外国籍選手'),
    ('33096', '2026-06-02T09:05:13.434153+00:00', NULL, NULL, '外国籍選手'),
    ('33098', '2026-06-02T09:05:09.919479+00:00', NULL, NULL, '外国籍選手'),
    ('43470', '2026-05-26T08:00:29.406515+00:00', 'ユース育成特別枠', '鹿児島県', '日本人選手'),
    ('5100000003', '2026-06-02T09:05:12.047328+00:00', NULL, NULL, '外国籍選手'),
    ('5100000007', '2026-06-02T09:04:59.263663+00:00', NULL, NULL, '外国籍選手'),
    ('5100000047', '2026-06-02T09:05:00.358557+00:00', NULL, NULL, '外国籍選手'),
    ('5100000060', '2026-06-02T09:04:51.356921+00:00', NULL, NULL, '外国籍選手'),
    ('5100000061', '2026-06-02T09:05:00.044484+00:00', NULL, NULL, '外国籍選手'),
    ('5100000065', '2026-06-02T09:04:45.473568+00:00', NULL, NULL, '外国籍選手'),
    ('5100000067', '2026-06-02T09:04:55.597691+00:00', NULL, NULL, '外国籍選手'),
    ('5100000068', '2026-06-02T09:04:45.686195+00:00', NULL, NULL, '外国籍選手'),
    ('5100000072', '2026-06-02T09:04:53.876386+00:00', NULL, NULL, '外国籍選手'),
    ('5100000086', '2026-06-02T09:04:54.604487+00:00', NULL, NULL, '外国籍選手'),
    ('51000098', '2026-06-02T09:04:57.499971+00:00', NULL, NULL, '日本人選手'),
    ('51000106', '2026-06-02T09:04:57.280337+00:00', NULL, NULL, '日本人選手'),
    ('51000126', '2026-06-02T09:05:00.817222+00:00', NULL, NULL, '外国籍選手'),
    ('51000131', '2026-06-02T09:05:04.538802+00:00', NULL, NULL, '外国籍選手'),
    ('51000427', '2026-06-02T09:05:41.566508+00:00', NULL, NULL, '外国籍選手'),
    ('8502', '2026-06-02T09:05:32.529279+00:00', NULL, NULL, '外国籍選手'),
    ('8664', '2026-06-02T09:05:02.333681+00:00', NULL, NULL, '外国籍選手'),
    ('8758', '2026-06-02T09:04:53.725518+00:00', NULL, NULL, '日本人選手'),
    ('8760', '2026-06-02T09:05:13.800502+00:00', NULL, NULL, '外国籍選手'),
    ('8762', '2026-06-02T09:05:29.60931+00:00', NULL, NULL, '外国籍選手'),
    ('8834', '2026-06-02T09:05:19.089166+00:00', NULL, NULL, '外国籍選手'),
    ('8836', '2026-06-02T09:04:47.593578+00:00', NULL, NULL, '日本人選手'),
    ('8844', '2026-06-02T09:04:50.447949+00:00', NULL, NULL, '外国籍選手'),
    ('9026', '2026-06-02T09:05:29.514564+00:00', NULL, NULL, '外国籍選手'),
    ('9027', '2026-06-02T09:05:12.758208+00:00', NULL, NULL, '日本人選手'),
    ('9028', '2026-06-02T09:04:54.509671+00:00', NULL, NULL, '外国籍選手'),
    ('9030', '2026-06-02T09:04:53.774941+00:00', NULL, NULL, '日本人選手'),
    ('9035', '2026-06-02T09:04:54.107194+00:00', NULL, NULL, '外国籍選手'),
    ('9038', '2026-06-02T09:05:28.94561+00:00', NULL, NULL, '外国籍選手'),
    ('9041', '2026-06-02T09:05:20.676831+00:00', NULL, NULL, '外国籍選手'),
    ('9042', '2026-06-02T09:05:24.722056+00:00', NULL, NULL, '外国籍選手'),
    ('9056', '2026-06-02T09:05:22.891542+00:00', NULL, NULL, '外国籍選手'),
    ('9057', '2026-06-02T09:05:19.027524+00:00', NULL, NULL, '外国籍選手'),
    ('9058', '2026-06-02T09:05:14.083025+00:00', NULL, NULL, '外国籍選手'),
    ('9059', '2026-06-02T09:05:13.801499+00:00', NULL, NULL, '外国籍選手'),
    ('9062', '2026-06-02T09:05:36.829332+00:00', NULL, NULL, '外国籍選手'),
    ('9081', '2026-06-02T09:04:59.746467+00:00', NULL, NULL, '外国籍選手'),
    ('9082', '2026-06-02T09:05:31.670576+00:00', NULL, NULL, '外国籍選手'),
    ('9089', '2026-06-02T09:04:49.864191+00:00', NULL, NULL, '外国籍選手'),
    ('9090', '2026-06-02T09:04:54.24644+00:00', NULL, NULL, '外国籍選手'),
    ('9266', '2026-06-02T09:04:47.198553+00:00', NULL, NULL, '外国籍選手'),
    ('9316', '2026-06-02T09:05:06.585648+00:00', NULL, NULL, '外国籍選手'),
    ('9331', '2026-06-02T09:04:49.763116+00:00', NULL, NULL, '外国籍選手'),
    ('9334', '2026-06-02T09:05:19.8761+00:00', NULL, NULL, '外国籍選手'),
    ('9354', '2026-06-02T09:05:36.781439+00:00', NULL, NULL, '外国籍選手'),
    ('9355', '2026-06-02T09:05:33.536757+00:00', NULL, NULL, '外国籍選手'),
    ('9356', '2026-06-02T09:05:35.113767+00:00', NULL, NULL, '外国籍選手'),
    ('9359', '2026-06-02T09:05:29.469624+00:00', NULL, NULL, '外国籍選手'),
    ('9360', '2026-06-02T09:05:29.236012+00:00', NULL, NULL, '外国籍選手'),
    ('9370', '2026-06-02T09:05:04.910315+00:00', NULL, NULL, '外国籍選手'),
    ('9372', '2026-06-02T09:05:03.115927+00:00', NULL, NULL, '外国籍選手'),
    ('9379', '2026-06-02T09:05:07.220813+00:00', NULL, NULL, '外国籍選手'),
    ('9381', '2026-06-02T09:04:54.566822+00:00', NULL, NULL, '外国籍選手'),
    ('9384', '2026-06-02T09:05:10.490996+00:00', NULL, NULL, '外国籍選手'),
    ('9385', '2026-06-02T09:04:57.305626+00:00', NULL, NULL, '外国籍選手'),
    ('9391', '2026-06-02T09:05:05.040662+00:00', NULL, NULL, '外国籍選手'),
    ('9393', '2026-06-02T09:05:04.802547+00:00', NULL, NULL, '外国籍選手'),
    ('9403', '2026-06-02T09:05:16.915227+00:00', NULL, NULL, '外国籍選手'),
    ('9404', '2026-06-02T09:05:11.117828+00:00', NULL, NULL, '外国籍選手'),
    ('9407', '2026-06-02T09:05:02.55844+00:00', NULL, NULL, '日本人選手'),
    ('9426', '2026-06-02T09:04:51.747579+00:00', NULL, NULL, '外国籍選手'),
    ('9448', '2026-06-02T09:05:09.703813+00:00', NULL, NULL, '外国籍選手'),
    ('9460', '2026-06-02T09:04:50.490085+00:00', NULL, NULL, '外国籍選手'),
    ('9461', '2026-06-02T09:04:54.452255+00:00', NULL, NULL, '外国籍選手'),
    ('9487', '2026-06-02T09:04:52.772678+00:00', NULL, NULL, '外国籍選手'),
    ('9488', '2026-06-02T09:05:10.906669+00:00', NULL, NULL, '外国籍選手'),
    ('9490', '2026-06-02T09:05:09.821517+00:00', NULL, NULL, '外国籍選手'),
    ('9494', '2026-06-02T09:05:08.866217+00:00', NULL, NULL, '外国籍選手'),
    ('9495', '2026-06-02T09:05:10.874433+00:00', NULL, NULL, '外国籍選手');

    CREATE TEMP TABLE issue_12_delete_ids (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue_12_delete_ids (player_id)
        SELECT player_id FROM public.data_patch_backup_20260811_issue_12_players_deleted;

    SELECT COUNT(*) INTO profile_ready_rows
      FROM public.players p
      JOIN issue_12_profile_patch d USING (player_id)
     WHERE p.updated_at IS NOT DISTINCT FROM d.expected_updated_at
       AND (d.league_value IS NULL OR p.league_registered_nationality IS NULL)
       AND (d.birthplace_value IS NULL OR p.birthplace IS NULL)
       AND (d.slot_value IS NULL OR p.player_slot_category IS NULL);
    IF profile_ready_rows <> 166 THEN
        RAISE EXCEPTION 'profile optimistic guard mismatch: expected=166 ready=%', profile_ready_rows;
    END IF;

    SELECT COUNT(*) INTO live_player_rows FROM public.players p JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO live_stat_rows FROM public.player_game_stats s JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO live_name_rows FROM public.player_name_history h JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO live_affiliation_rows FROM public.player_affiliations a JOIN issue_12_delete_ids d USING (player_id);
    IF live_player_rows <> 48 OR live_stat_rows <> 4060 OR live_name_rows <> 59 OR live_affiliation_rows <> 70 THEN
        RAISE EXCEPTION 'delete target count mismatch: players=% stats=% names=% affiliations=%',
            live_player_rows, live_stat_rows, live_name_rows, live_affiliation_rows;
    END IF;

    SELECT COUNT(*) INTO map_ref_rows
      FROM public.player_id_map m
      JOIN issue_12_delete_ids d
        ON m.player_id = d.player_id OR m.old_player_id = d.player_id;
    IF map_ref_rows <> 0 THEN
        RAISE EXCEPTION 'player_id_map references deletion targets: %', map_ref_rows;
    END IF;

    UPDATE public.players p
       SET league_registered_nationality = CASE WHEN d.league_value IS NOT NULL THEN d.league_value ELSE p.league_registered_nationality END,
           birthplace = CASE WHEN d.birthplace_value IS NOT NULL THEN d.birthplace_value ELSE p.birthplace END,
           player_slot_category = CASE WHEN d.slot_value IS NOT NULL THEN d.slot_value ELSE p.player_slot_category END,
           updated_at = NOW()
      FROM issue_12_profile_patch d
     WHERE p.player_id = d.player_id
       AND p.updated_at IS NOT DISTINCT FROM d.expected_updated_at
       AND (d.league_value IS NULL OR p.league_registered_nationality IS NULL)
       AND (d.birthplace_value IS NULL OR p.birthplace IS NULL)
       AND (d.slot_value IS NULL OR p.player_slot_category IS NULL);
    GET DIAGNOSTICS updated_profile_rows = ROW_COUNT;
    IF updated_profile_rows <> 166 THEN
        RAISE EXCEPTION 'profile update count mismatch: expected=166 actual=%', updated_profile_rows;
    END IF;

    DELETE FROM public.player_game_stats s USING issue_12_delete_ids d WHERE s.player_id = d.player_id;
    GET DIAGNOSTICS deleted_stat_rows = ROW_COUNT;
    DELETE FROM public.player_name_history h USING issue_12_delete_ids d WHERE h.player_id = d.player_id;
    GET DIAGNOSTICS deleted_name_rows = ROW_COUNT;
    DELETE FROM public.player_affiliations a USING issue_12_delete_ids d WHERE a.player_id = d.player_id;
    GET DIAGNOSTICS deleted_affiliation_rows = ROW_COUNT;
    DELETE FROM public.players p USING issue_12_delete_ids d WHERE p.player_id = d.player_id;
    GET DIAGNOSTICS deleted_player_rows = ROW_COUNT;

    IF deleted_stat_rows <> 4060 OR deleted_name_rows <> 59 OR deleted_affiliation_rows <> 70 OR deleted_player_rows <> 48 THEN
        RAISE EXCEPTION 'delete count mismatch: players=% stats=% names=% affiliations=%',
            deleted_player_rows, deleted_stat_rows, deleted_name_rows, deleted_affiliation_rows;
    END IF;

    SELECT COUNT(*) INTO remaining_profile_mismatches
      FROM public.players p
      JOIN issue_12_profile_patch d USING (player_id)
     WHERE (d.league_value IS NOT NULL AND p.league_registered_nationality IS DISTINCT FROM d.league_value)
        OR (d.birthplace_value IS NOT NULL AND p.birthplace IS DISTINCT FROM d.birthplace_value)
        OR (d.slot_value IS NOT NULL AND p.player_slot_category IS DISTINCT FROM d.slot_value);
    SELECT COUNT(*) INTO remaining_deleted_players FROM public.players p JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO remaining_deleted_stats FROM public.player_game_stats s JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO remaining_deleted_names FROM public.player_name_history h JOIN issue_12_delete_ids d USING (player_id);
    SELECT COUNT(*) INTO remaining_deleted_affiliations FROM public.player_affiliations a JOIN issue_12_delete_ids d USING (player_id);
    IF remaining_profile_mismatches <> 0 OR remaining_deleted_players <> 0 OR remaining_deleted_stats <> 0
       OR remaining_deleted_names <> 0 OR remaining_deleted_affiliations <> 0 THEN
        RAISE EXCEPTION 'postcheck mismatch: profile=% players=% stats=% names=% affiliations=%',
            remaining_profile_mismatches, remaining_deleted_players, remaining_deleted_stats,
            remaining_deleted_names, remaining_deleted_affiliations;
    END IF;
END;
$issue_12_apply$;

SELECT 'profile_patch_rows' AS check_name, COUNT(*) AS row_count
  FROM public.data_patch_backup_20260811_issue_12_player_profiles
UNION ALL
SELECT 'remaining_delete_players', COUNT(*)
  FROM public.players p
  JOIN public.data_patch_backup_20260811_issue_12_players_deleted b USING (player_id)
UNION ALL
SELECT 'remaining_delete_player_game_stats', COUNT(*)
  FROM public.player_game_stats s
  JOIN public.data_patch_backup_20260811_issue_12_players_deleted b USING (player_id);
