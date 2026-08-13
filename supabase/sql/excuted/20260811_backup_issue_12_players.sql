-- Issue #12: playersプロフィール補完・スタッフ行整理
-- 作成日: 2026-08-11
-- 目的: 適用対象の実データを永続バックアップへ保存する。
-- 対象: public.players、public.player_game_stats、public.player_name_history、public.player_affiliations
-- 想定件数: profile対象166、削除対象players48 / player_game_stats4060 / name_history59 / affiliations70
-- 実行順: このSQLを最初に実行し、件数確認後に 20260811_fix_issue_12_players.sql を実行する。
-- 注意: このSQL自体はliveデータを削除・更新しないが、バックアップテーブルを作成する。

DO $issue_12_backup$
DECLARE
    profile_rows INTEGER;
    deleted_player_rows INTEGER;
    game_stat_rows INTEGER;
    name_history_rows INTEGER;
    affiliation_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_profiles') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_players_deleted') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_game_stats') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_name_history') IS NOT NULL
       OR TO_REGCLASS('public.data_patch_backup_20260811_issue_12_player_affiliations') IS NOT NULL THEN
        RAISE EXCEPTION 'Issue #12 backup table already exists; inspect before re-running';
    END IF;

    CREATE TEMP TABLE issue_12_profile_ids (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue_12_profile_ids (player_id) VALUES
    ('10265'),
    ('10817'),
    ('10819'),
    ('10823'),
    ('10875'),
    ('10886'),
    ('10887'),
    ('10897'),
    ('12457'),
    ('12459'),
    ('12507'),
    ('12508'),
    ('12523'),
    ('12578'),
    ('12579'),
    ('12580'),
    ('12581'),
    ('12583'),
    ('12584'),
    ('12585'),
    ('12586'),
    ('12594'),
    ('12595'),
    ('12596'),
    ('12630'),
    ('12636'),
    ('12637'),
    ('12640'),
    ('12648'),
    ('12660'),
    ('12663'),
    ('15805'),
    ('15809'),
    ('15812'),
    ('15814'),
    ('15845'),
    ('15847'),
    ('15848'),
    ('15849'),
    ('15852'),
    ('18168'),
    ('18169'),
    ('18173'),
    ('18397'),
    ('18426'),
    ('18427'),
    ('18431'),
    ('18432'),
    ('18436'),
    ('18442'),
    ('18444'),
    ('18452'),
    ('18459'),
    ('18473'),
    ('18479'),
    ('18846'),
    ('19955'),
    ('19958'),
    ('19995'),
    ('19997'),
    ('20020'),
    ('20032'),
    ('22396'),
    ('22400'),
    ('22404'),
    ('22522'),
    ('25136'),
    ('26825'),
    ('26826'),
    ('26875'),
    ('26892'),
    ('26893'),
    ('26897'),
    ('26898'),
    ('26910'),
    ('26911'),
    ('26915'),
    ('26916'),
    ('26928'),
    ('26931'),
    ('26938'),
    ('27051'),
    ('30393'),
    ('30435'),
    ('32952'),
    ('32981'),
    ('32983'),
    ('32990'),
    ('32994'),
    ('33030'),
    ('33031'),
    ('33037'),
    ('33045'),
    ('33093'),
    ('33096'),
    ('33098'),
    ('43470'),
    ('5100000003'),
    ('5100000007'),
    ('5100000047'),
    ('5100000060'),
    ('5100000061'),
    ('5100000065'),
    ('5100000067'),
    ('5100000068'),
    ('5100000072'),
    ('5100000086'),
    ('51000098'),
    ('51000106'),
    ('51000126'),
    ('51000131'),
    ('51000427'),
    ('8502'),
    ('8664'),
    ('8758'),
    ('8760'),
    ('8762'),
    ('8834'),
    ('8836'),
    ('8844'),
    ('9026'),
    ('9027'),
    ('9028'),
    ('9030'),
    ('9035'),
    ('9038'),
    ('9041'),
    ('9042'),
    ('9056'),
    ('9057'),
    ('9058'),
    ('9059'),
    ('9062'),
    ('9081'),
    ('9082'),
    ('9089'),
    ('9090'),
    ('9266'),
    ('9316'),
    ('9331'),
    ('9334'),
    ('9354'),
    ('9355'),
    ('9356'),
    ('9359'),
    ('9360'),
    ('9370'),
    ('9372'),
    ('9379'),
    ('9381'),
    ('9384'),
    ('9385'),
    ('9391'),
    ('9393'),
    ('9403'),
    ('9404'),
    ('9407'),
    ('9426'),
    ('9448'),
    ('9460'),
    ('9461'),
    ('9487'),
    ('9488'),
    ('9490'),
    ('9494'),
    ('9495');

    CREATE TEMP TABLE issue_12_delete_ids (player_id TEXT PRIMARY KEY) ON COMMIT DROP;
    INSERT INTO issue_12_delete_ids (player_id) VALUES
    ('8660'),
    ('8661'),
    ('8691'),
    ('8692'),
    ('8693'),
    ('8694'),
    ('8695'),
    ('8745'),
    ('8746'),
    ('8747'),
    ('8748'),
    ('8749'),
    ('8751'),
    ('8753'),
    ('9276'),
    ('9335'),
    ('9417'),
    ('9419'),
    ('9421'),
    ('9422'),
    ('9429'),
    ('10267'),
    ('12282'),
    ('12510'),
    ('12511'),
    ('12512'),
    ('12513'),
    ('12514'),
    ('12515'),
    ('12517'),
    ('12518'),
    ('12520'),
    ('12655'),
    ('12661'),
    ('18147'),
    ('18423'),
    ('18453'),
    ('18471'),
    ('18474'),
    ('18842'),
    ('22483'),
    ('22495'),
    ('25147'),
    ('27047'),
    ('30467'),
    ('45872'),
    ('45873'),
    ('999999999');

    CREATE TABLE public.data_patch_backup_20260811_issue_12_player_profiles AS
        SELECT p.* FROM public.players p WHERE FALSE;
    CREATE TABLE public.data_patch_backup_20260811_issue_12_players_deleted AS
        SELECT p.* FROM public.players p WHERE FALSE;
    CREATE TABLE public.data_patch_backup_20260811_issue_12_player_game_stats AS
        SELECT s.* FROM public.player_game_stats s WHERE FALSE;
    CREATE TABLE public.data_patch_backup_20260811_issue_12_player_name_history AS
        SELECT h.* FROM public.player_name_history h WHERE FALSE;
    CREATE TABLE public.data_patch_backup_20260811_issue_12_player_affiliations AS
        SELECT a.* FROM public.player_affiliations a WHERE FALSE;

    INSERT INTO public.data_patch_backup_20260811_issue_12_player_profiles
        SELECT p.* FROM public.players p JOIN issue_12_profile_ids i USING (player_id);
    INSERT INTO public.data_patch_backup_20260811_issue_12_players_deleted
        SELECT p.* FROM public.players p JOIN issue_12_delete_ids i USING (player_id);
    INSERT INTO public.data_patch_backup_20260811_issue_12_player_game_stats
        SELECT s.* FROM public.player_game_stats s JOIN issue_12_delete_ids i USING (player_id);
    INSERT INTO public.data_patch_backup_20260811_issue_12_player_name_history
        SELECT h.* FROM public.player_name_history h JOIN issue_12_delete_ids i USING (player_id);
    INSERT INTO public.data_patch_backup_20260811_issue_12_player_affiliations
        SELECT a.* FROM public.player_affiliations a JOIN issue_12_delete_ids i USING (player_id);

    SELECT COUNT(*) INTO profile_rows FROM public.data_patch_backup_20260811_issue_12_player_profiles;
    SELECT COUNT(*) INTO deleted_player_rows FROM public.data_patch_backup_20260811_issue_12_players_deleted;
    SELECT COUNT(*) INTO game_stat_rows FROM public.data_patch_backup_20260811_issue_12_player_game_stats;
    SELECT COUNT(*) INTO name_history_rows FROM public.data_patch_backup_20260811_issue_12_player_name_history;
    SELECT COUNT(*) INTO affiliation_rows FROM public.data_patch_backup_20260811_issue_12_player_affiliations;

    IF profile_rows <> 166 OR deleted_player_rows <> 48 OR game_stat_rows <> 4060
       OR name_history_rows <> 59 OR affiliation_rows <> 70 THEN
        RAISE EXCEPTION 'backup row count mismatch: profiles=% deleted_players=% stats=% name_history=% affiliations=%',
            profile_rows, deleted_player_rows, game_stat_rows, name_history_rows, affiliation_rows;
    END IF;

    REVOKE ALL ON TABLE public.data_patch_backup_20260811_issue_12_player_profiles FROM anon, authenticated;
    REVOKE ALL ON TABLE public.data_patch_backup_20260811_issue_12_players_deleted FROM anon, authenticated;
    REVOKE ALL ON TABLE public.data_patch_backup_20260811_issue_12_player_game_stats FROM anon, authenticated;
    REVOKE ALL ON TABLE public.data_patch_backup_20260811_issue_12_player_name_history FROM anon, authenticated;
    REVOKE ALL ON TABLE public.data_patch_backup_20260811_issue_12_player_affiliations FROM anon, authenticated;
END;
$issue_12_backup$;

SELECT 'player_profiles' AS backup_scope, COUNT(*) AS row_count
  FROM public.data_patch_backup_20260811_issue_12_player_profiles
UNION ALL
SELECT 'players_deleted', COUNT(*) FROM public.data_patch_backup_20260811_issue_12_players_deleted
UNION ALL
SELECT 'player_game_stats', COUNT(*) FROM public.data_patch_backup_20260811_issue_12_player_game_stats
UNION ALL
SELECT 'player_name_history', COUNT(*) FROM public.data_patch_backup_20260811_issue_12_player_name_history
UNION ALL
SELECT 'player_affiliations', COUNT(*) FROM public.data_patch_backup_20260811_issue_12_player_affiliations
ORDER BY backup_scope;
