-- Issue #21: rollback player profile patch
-- Date: 2026-08-13
-- Related issues: #12, #21
-- Backup: public.data_patch_backup_20260813_issue_21_player_profiles
-- Run only when the post-apply state is verified and the backup table is intact.
-- Re-run guard: current target rows must match the expected post-apply state.

BEGIN;

CREATE TEMP TABLE issue_21_profile_patch (
    player_id TEXT PRIMARY KEY,
    player_name_j TEXT,
    player_name_e TEXT,
    last_seen_jersey_number TEXT,
    last_seen_team_id TEXT,
    league_registered_nationality TEXT,
    birthplace TEXT
) ON COMMIT DROP;

INSERT INTO issue_21_profile_patch (
    player_id,
    player_name_j,
    player_name_e,
    last_seen_jersey_number,
    last_seen_team_id,
    league_registered_nationality,
    birthplace
) VALUES
    ('8469', '菅澤 紀行', 'Noriyuki Sugasawa', '10', '699', '日本', NULL),
    ('8520', '杉本 慶', 'Kei Sugimoto', '11', NULL, '日本', '滋賀県'),
    ('8594', '長谷川 智也', 'Tomoya Hasegawa', '8', NULL, '日本', '新潟県'),
    ('8596', '桜木 ジェイアール', 'JR Sakuragi', '32', '728', '日本', NULL),
    ('8651', 'アンソニー・マクヘンリー', 'Anthony Mchenry', NULL, '3013', 'アメリカ合衆国', 'アメリカ合衆国'),
    ('8689', '木下 博之', 'Hiroyuki Kinoshita', '17', '700', '日本', NULL),
    ('8835', 'ジェフ・ギブス', 'Jeff Gibbs', '4', '726', 'アメリカ合衆国', NULL),
    ('9382', 'ジェロウム・ティルマン', 'Jerome Tillman', '33', '693', 'アメリカ合衆国', NULL),
    ('9392', 'ダニエル・ミラー', 'Daniel Miller', '5', '702', 'アメリカ合衆国', NULL),
    ('9431', 'ジョシュア・クロフォード', 'Joshua Crawford', '22', '695', 'アメリカ合衆国', NULL),
    ('9474', 'PARK JAE HAN', 'PARK JAE HAN', '0', '786', NULL, NULL),
    ('9476', 'HAN HUI WON', 'HAN HUI WON', '4', '786', NULL, NULL),
    ('9477', 'KIM JONG KEUN', 'KIM JONG KEUN', '7', '786', NULL, NULL),
    ('9478', 'KIM MIN WOOK', 'KIM MIN WOOK', '9', '786', NULL, NULL),
    ('9479', 'JEON SEONG HYEN', 'JEON SEONG HYEN', '23', '786', NULL, NULL),
    ('9480', 'KEIFER J SYKES', 'KEIFER J SYKES', '28', '786', NULL, NULL),
    ('9481', 'KIM CHEOL UK', 'KIM CHEOL UK', '32', '786', NULL, NULL),
    ('9482', 'DAVID JOSEPH SIMON', 'DAVID JOSEPH SIMON', '55', '786', NULL, NULL),
    ('9483', 'LEE JUNG HYUN', 'LEE JUNG HYUN', '3', '786', NULL, NULL),
    ('9484', 'MOON SEONG GON', 'MOON SEONG GON', '10', '786', NULL, NULL),
    ('9485', 'YANG HEE JONG', 'YANG HEE JONG', '11', '786', NULL, NULL),
    ('9486', 'OH SE KEUN', 'OH SE KEUN', '41', '786', NULL, NULL),
    ('10256', 'ドゥレイロン・バーンズ', 'Draelon Burns', '2', '716', 'アメリカ合衆国', NULL),
    ('12642', 'アンジェロ・チョル', 'Angelo Chol', '7', '693', 'アメリカ合衆国', NULL),
    ('18429', '大崎 裕太', 'Yuta Osaki', '16', NULL, '日本', '茨城県'),
    ('20033', 'セドリック・シモンズ', 'Cedric Simmons', '22', '728', 'アメリカ合衆国', NULL),
    ('25149', 'イシュマエル・レーン', 'Ishmael Lane', '4', '729', 'アメリカ合衆国', NULL),
    ('26909', 'クリス・オトゥーレ', 'Chris Otule', '42', '728', 'アメリカ合衆国', NULL),
    ('33042', 'デクアン・ジョーンズ', 'DeQuan Jones', '18', '698', 'アメリカ合衆国', NULL),
    ('40153', 'ダニエル・ギデンズ', 'Daniel Giddens', '41', '697', 'アメリカ合衆国', NULL),
    ('45848', 'レイ・パークスジュニア', 'Ray Parks Jr.', '1', '3013', NULL, NULL),
    ('45849', 'カイ・ソット', 'Kai Sotto', '11', '3013', NULL, NULL),
    ('45850', 'チュアンシン・リュウ', 'Liu Chuanxing', '12', '3013', NULL, NULL),
    ('45851', 'キーファー・ラベナ', 'Kiefer Ravena', '15', '3013', NULL, NULL),
    ('45852', 'ドワイト・ラモス', 'Dwight Ramos', '2', '3013', NULL, NULL),
    ('45853', 'グレゴリー・スローター', 'Gregory Slaughter', '20', '3013', NULL, NULL),
    ('45854', 'チャン ミンクク', 'Min kug Chang', '3', '3013', NULL, NULL),
    ('45855', 'カール・タマヨ', 'Carl Tamayo', '33', '3013', NULL, NULL),
    ('45856', 'シェンゼ・リー', 'Li Shengzhe', '34', '3013', NULL, NULL),
    ('45857', 'イ デソン', 'Daesung Lee', '43', '3013', NULL, NULL),
    ('45858', '劉 駿霆', 'Chun-Ting Liu', '6', '3013', '日本', NULL),
    ('45859', 'マシュー・ライト', 'Matthew Wright', '7', '3013', NULL, NULL),
    ('45860', 'ロン･ジェイ･アバリエントス', 'Rhon Jhay Abarrientos', '77', '3013', NULL, NULL),
    ('45861', '王 偉嘉', 'Weijia Wang', '8', '3013', '日本', NULL),
    ('45862', '荒谷 裕秀', 'Hirohide Araya', '11', '3012', '日本', NULL),
    ('45863', '上田 隼輔', 'Shunsuke Ueda', '20', '3012', '日本', NULL),
    ('45864', '飯尾 文哉', 'Fumiya Iio', '22', '3012', '日本', NULL),
    ('45865', 'キング 開', 'Kai King', '23', '3012', NULL, NULL),
    ('45866', '角田 太輝', 'Taiki Sumida', '25', '3012', '日本', NULL),
    ('45867', '湧川 颯斗', 'Hayato Wakugawa', '34', '3012', '日本', NULL),
    ('45868', '佐土原 遼', 'Ryo Sadohara', '8', '3012', '日本', NULL),
    ('45869', '八村 阿蓮', 'Allen Hachimura', '88', '3012', '日本', NULL),
    ('45870', '渡邉 飛勇', 'Hugh Watanabe', '9', '701', '日本', NULL),
    ('45871', '川真田 紘也', 'Koya Kawamata', '99', '3012', '日本', NULL),
    ('52433', 'ジョーダン・ナタイ', 'Jordan Ngatai', '20', '702', 'ニュージーランド', NULL),
    ('51000114', '寺澤 大夢', 'Hiromu Terasawa', '10', '692', '日本', NULL),
    ('51000161', 'ジェイコブ・ワイリー', 'Jacob Wiley', '0', '698', 'アメリカ合衆国', NULL),
    ('51000192', 'トレイ・ポーター', 'Trey Porter', '22', NULL, 'アメリカ合衆国', 'アメリカ合衆国'),
    ('51000218', 'アンドリュー・ファーガソン', 'Andrew Ferguson', '34', '720', 'オーストラリア', NULL),
    ('51000219', 'ウィリアム・モズリー', 'William Mosley', '42', '716', 'アメリカ合衆国', NULL),
    ('51000225', '平岡 勇人', 'Yuto Hiraoka', '31', '694', '日本', NULL),
    ('51000226', 'エペ・ウドゥ', 'Ekpe Udoh', '77', '699', 'アメリカ合衆国', NULL),
    ('51000229', 'キャメロン・クラットウィグ', 'Cameron Krutwig', '15', '712', 'アメリカ合衆国', NULL),
    ('51000241', 'シズ・オルストン', 'Shizz Alston', '10', '728', 'アメリカ合衆国', NULL),
    ('51000261', 'パク ジェヒョン', 'Jaehyun Park', '11', '695', '大韓民国', NULL),
    ('51000262', 'サムソン・フローリング', 'Samson Froling', '13', '702', 'オーストラリア', NULL),
    ('51000321', 'デレク・パードン', 'Dererk Pardon', '7', NULL, 'アメリカ合衆国', 'アメリカ合衆国'),
    ('51000334', 'ジョニー・オブライアント', 'Johnny O''Bryant', '84', '712', 'アメリカ合衆国', NULL),
    ('51000340', '井手 歩由夢', 'Ayumu Ide', '12', '1638', '日本', NULL),
    ('51000352', '渡邉 伶音', 'Leon Watanabe', '42', NULL, '日本', '千葉県'),
    ('51000359', '黒川 虎徹', 'Kotetsu Kurokawa', '3', NULL, '日本', '長崎県'),
    ('51000369', '橋谷 真季', 'Manaki Hashiya', '23', '712', '日本', NULL),
    ('51000533', 'デイボン・リード', 'Davon Reed', '9', '745', 'アメリカ合衆国', NULL),
    ('51000578', 'マリアル・シャヨク', 'Marial Shayok', '1', NULL, 'カナダ', 'カナダ'),
    ('55000009', '根本 晃', 'Ko Nemoto', '12', '53000073', '日本', NULL),
    ('55000015', '山田 悠斗', 'Yuto Yamada', '5', '53000072', '日本', NULL),
    ('55000067', '五明 一真', 'Kazuma Gomyo', '13', '53000063', '日本', NULL),
    ('55000076', '須藤 春輝', 'Haruki Sudo', '0', '701', '日本', NULL),
    ('55000077', '宜保 隼弥', 'shunya Gibo', '11', '53000072', '日本', NULL),
    ('55000174', '松下 湊人', 'Minato Matsushita', '13', '53000073', '日本', NULL),
    ('55000219', '南 拓摩', 'Takuma Minami', '13', '53000062', '日本', NULL),
    ('55000308', '菅野　楓太', 'Futa Sugano', '14', '53000062', '日本', NULL),
    ('55000363', '李 子浩', 'Kohiro Lee', '9', '53000062', '日本', NULL),
    ('55000423', '中西 真那斗', 'Manato Nakanishi', '6', '53000072', '日本', NULL),
    ('55000424', '佐藤 遼乙', 'Haruto Sato', '12', '53000063', '日本', NULL),
    ('55000450', '藤井 暖', 'Non Fujii', '12', '53000062', '日本', NULL),
    ('55000453', '小倉 貴志', 'Takashi Ogura', '11', '53000073', '日本', NULL),
    ('55000463', '中田 直斗', 'Naoto Nakata', '14', '53000073', '日本', NULL),
    ('55000510', '木戸 龍斗', 'Ryuto Kido', '4', '53000063', '日本', NULL),
    ('55000565', '稲葉 耕佑', 'Kosuke Inaba', '5', '53000063', '日本', NULL),
    ('55000566', '藤原 拓海', 'Takumi Fujiwara', '6', '53000063', '日本', NULL),
    ('55000569', '木山 大輔', 'Daisuke Kiyama', '10', '53000063', '日本', NULL),
    ('55000570', '山本 奨', 'Masashi Yamamoto', '14', '53000063', '日本', NULL),
    ('55000571', '松尾 和', 'Yamato Matsuo', '15', '53000063', '日本', NULL),
    ('55000572', '藤井 大', 'Yamato Fujii', '4', '53000062', '日本', NULL),
    ('55000574', '山﨑 成隆', 'Naritaka Yamazaki', '6', '53000062', NULL, NULL),
    ('55000576', '倉光 晴', 'Haru Kuramitsu', '10', '53000062', '日本', NULL),
    ('55000752', '服部 怜恩', 'Reon Hattori', '5', '53000073', '日本', NULL),
    ('55000811', '西田 瑛久', 'Eku Nishida', '13', '53000072', '日本', NULL),
    ('55000818', '井伊 拓海', 'Takuni Ii', '10', '53000072', '日本', NULL),
    ('55000826', '大越 海藍', 'Kai Ogoshi', '15', '53000073', '日本', NULL),
    ('55000845', '林 空翔', 'Takato Hayashi', '8', '53000073', '日本', NULL),
    ('55000868', '梅原 咲弥', 'Sakuya Umehara', '39', '712', '日本', NULL),
    ('55000960', '原田 ジョルジオ', 'Giorgio Harada', '12', '53000072', NULL, NULL),
    ('55000961', '栗原 琉空', 'Riku Kurihara', '9', '53000073', '日本', NULL),
    ('55000963', '長嶺 充来', 'Mirai Nagamine', '12', '53000073', '日本', NULL),
    ('55000964', '石原 蔵之助', 'Kuranosuke Ishihara', '14', '53000073', '日本', NULL),
    ('55000973', '高橋 秀成', 'Shusei Takahashi', '7', '53000073', '日本', NULL),
    ('55000974', '小松 亮太', 'Ryota Komatsu', '10', '53000073', '日本', NULL),
    ('55000975', '三上 寛太', 'Kanta Mikami', '13', '53000073', '日本', NULL),
    ('55000976', 'エルマスリ アダム', 'Adam Elmasri', '14', '53000073', NULL, NULL),
    ('55000977', '宮里 俊佑', 'Syunsuke Miyazato', '7', '53000072', '日本', NULL),
    ('55000978', '福地 勇太', 'Yudai Fukuchi', '8', '53000072', '日本', NULL),
    ('55000979', '川邉 蒼侑', 'Ayuki Kawabe', '12', '53000072', '日本', NULL),
    ('55000980', '中川 恵太', 'Keita Nakagawa', '13', '53000072', '日本', NULL),
    ('55000981', 'プラット 聖也', 'Sena Platt', '14', '53000072', NULL, NULL),
    ('5100000064', '青木 龍史', 'Ryuji Aoki', '1', '700', '日本', NULL);

DO $issue_21_rollback$
DECLARE
    backup_rows INTEGER;
    existing_rows INTEGER;
    post_mismatches INTEGER;
    expected_changed_rows INTEGER;
    current_changed_rows INTEGER;
    restored_rows INTEGER;
    rollback_mismatches INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260813_issue_21_player_profiles') IS NULL THEN
        RAISE EXCEPTION 'Issue #21 backup table is required';
    END IF;

    SELECT COUNT(*) INTO backup_rows
      FROM public.data_patch_backup_20260813_issue_21_player_profiles;
    IF backup_rows <> 117 THEN
        RAISE EXCEPTION 'backup row count mismatch: expected=117 actual=%', backup_rows;
    END IF;

    SELECT COUNT(*) INTO existing_rows
      FROM public.players p
      JOIN public.data_patch_backup_20260813_issue_21_player_profiles b USING (player_id);
    IF existing_rows <> 117 THEN
        RAISE EXCEPTION 'rollback target row count mismatch: expected=117 actual=%', existing_rows;
    END IF;

    SELECT COUNT(*) INTO post_mismatches
      FROM public.players p
      JOIN public.data_patch_backup_20260813_issue_21_player_profiles b USING (player_id)
      JOIN issue_21_profile_patch patch USING (player_id)
     WHERE p.player_name_j IS DISTINCT FROM
               CASE WHEN patch.player_name_j IS NOT NULL
                          AND NULLIF(b.player_name_j, '') IS NULL
                    THEN patch.player_name_j ELSE b.player_name_j END
        OR p.player_name_e IS DISTINCT FROM
               CASE WHEN patch.player_name_e IS NOT NULL
                          AND NULLIF(b.player_name_e, '') IS NULL
                    THEN patch.player_name_e ELSE b.player_name_e END
        OR p.last_seen_jersey_number IS DISTINCT FROM
               CASE WHEN patch.last_seen_jersey_number IS NOT NULL
                          AND NULLIF(b.last_seen_jersey_number, '') IS NULL
                    THEN patch.last_seen_jersey_number ELSE b.last_seen_jersey_number END
        OR p.last_seen_team_id IS DISTINCT FROM
               CASE WHEN patch.last_seen_team_id IS NOT NULL
                          AND NULLIF(b.last_seen_team_id, '') IS NULL
                    THEN patch.last_seen_team_id ELSE b.last_seen_team_id END
        OR p.league_registered_nationality IS DISTINCT FROM
               CASE WHEN patch.league_registered_nationality IS NOT NULL
                          AND NULLIF(b.league_registered_nationality, '') IS NULL
                    THEN patch.league_registered_nationality ELSE b.league_registered_nationality END
        OR p.birthplace IS DISTINCT FROM
               CASE WHEN patch.birthplace IS NOT NULL
                          AND NULLIF(b.birthplace, '') IS NULL
                    THEN patch.birthplace ELSE b.birthplace END
        OR p.player_slot_category IS DISTINCT FROM b.player_slot_category
        OR p.old_player_id IS DISTINCT FROM b.old_player_id
        OR p.created_at IS DISTINCT FROM b.created_at;
    IF post_mismatches <> 0 THEN
        RAISE EXCEPTION 'rollback target is not the expected post-apply state: % rows',
            post_mismatches;
    END IF;

    SELECT COUNT(*) INTO expected_changed_rows
      FROM public.data_patch_backup_20260813_issue_21_player_profiles b
      JOIN issue_21_profile_patch patch USING (player_id)
     WHERE (
       (patch.player_name_j IS NOT NULL
        AND NULLIF(b.player_name_j, '') IS NULL)
    OR (patch.player_name_e IS NOT NULL
        AND NULLIF(b.player_name_e, '') IS NULL)
    OR (patch.last_seen_jersey_number IS NOT NULL
        AND NULLIF(b.last_seen_jersey_number, '') IS NULL)
    OR (patch.last_seen_team_id IS NOT NULL
        AND NULLIF(b.last_seen_team_id, '') IS NULL)
    OR (patch.league_registered_nationality IS NOT NULL
        AND NULLIF(b.league_registered_nationality, '') IS NULL)
    OR (patch.birthplace IS NOT NULL
        AND NULLIF(b.birthplace, '') IS NULL)
);
    SELECT COUNT(*) INTO current_changed_rows
      FROM public.players p
      JOIN public.data_patch_backup_20260813_issue_21_player_profiles b USING (player_id)
     WHERE p.player_name_j IS DISTINCT FROM b.player_name_j
        OR p.player_name_e IS DISTINCT FROM b.player_name_e
        OR p.last_seen_jersey_number IS DISTINCT FROM b.last_seen_jersey_number
        OR p.last_seen_team_id IS DISTINCT FROM b.last_seen_team_id
        OR p.league_registered_nationality IS DISTINCT FROM b.league_registered_nationality
        OR p.birthplace IS DISTINCT FROM b.birthplace;
    IF expected_changed_rows > 0 AND current_changed_rows = 0 THEN
        RAISE EXCEPTION 'Issue #21 fix does not appear to be applied';
    END IF;

    UPDATE public.players p
       SET player_name_j = b.player_name_j,
           player_name_e = b.player_name_e,
           player_slot_category = b.player_slot_category,
           league_registered_nationality = b.league_registered_nationality,
           birthplace = b.birthplace,
           last_seen_team_id = b.last_seen_team_id,
           last_seen_jersey_number = b.last_seen_jersey_number,
           old_player_id = b.old_player_id,
           created_at = b.created_at,
           updated_at = b.updated_at
      FROM public.data_patch_backup_20260813_issue_21_player_profiles b
     WHERE p.player_id = b.player_id;

    GET DIAGNOSTICS restored_rows = ROW_COUNT;
    IF restored_rows <> 117 THEN
        RAISE EXCEPTION 'rollback restore count mismatch: expected=117 actual=%',
            restored_rows;
    END IF;

    SELECT COUNT(*) INTO rollback_mismatches
      FROM public.players p
      JOIN public.data_patch_backup_20260813_issue_21_player_profiles b USING (player_id)
     WHERE p.player_name_j IS DISTINCT FROM b.player_name_j
        OR p.player_name_e IS DISTINCT FROM b.player_name_e
        OR p.player_slot_category IS DISTINCT FROM b.player_slot_category
        OR p.league_registered_nationality IS DISTINCT FROM b.league_registered_nationality
        OR p.birthplace IS DISTINCT FROM b.birthplace
        OR p.last_seen_team_id IS DISTINCT FROM b.last_seen_team_id
        OR p.last_seen_jersey_number IS DISTINCT FROM b.last_seen_jersey_number
        OR p.old_player_id IS DISTINCT FROM b.old_player_id
        OR p.created_at IS DISTINCT FROM b.created_at
        OR p.updated_at IS DISTINCT FROM b.updated_at;
    IF rollback_mismatches <> 0 THEN
        RAISE EXCEPTION 'rollback postcheck mismatch: % rows', rollback_mismatches;
    END IF;
END;
$issue_21_rollback$;

SELECT 'restored_player_profiles' AS check_name, COUNT(*) AS row_count
  FROM public.players p
  JOIN public.data_patch_backup_20260813_issue_21_player_profiles b USING (player_id);

COMMIT;
