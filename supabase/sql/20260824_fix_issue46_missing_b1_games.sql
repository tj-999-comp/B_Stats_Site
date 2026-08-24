-- Issue #46: 欠落B1試合40件のUpsert
-- 作成日: 20260824
-- 実行順: backup → verify（PRE_FIX）→ 本SQL → verify（POST_FIX）
-- 注意: live DBを変更する。接続先、backup結果、verify（PRE_FIX）を確認してから実行する。
-- play_by_playは対象外。

BEGIN;

DO $issue_46_fix$
DECLARE
    n BIGINT;
    expected_players BIGINT;
BEGIN
    IF TO_REGCLASS('public.data_patch_issue46_teams') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_games') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_game_team_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_players') IS NULL
       OR TO_REGCLASS('public.data_patch_issue46_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_teams') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_games') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_game_team_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_players') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_game_stats') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_id_map') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_team_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_name_history') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_player_affiliations') IS NULL
       OR TO_REGCLASS('public.data_patch_backup_20260824_issue46_meta') IS NULL THEN
        RAISE EXCEPTION 'Issue #46 input or backup table is missing';
    END IF;

    IF (SELECT COUNT(*) FROM public.data_patch_issue46_teams) <> 27
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_games) <> 40
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_game_team_stats) <> 78
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_players) <> 687
       OR (SELECT COUNT(*) FROM public.data_patch_issue46_player_game_stats) <> 917 THEN
        RAISE EXCEPTION 'Issue #46 input row-count guard failed';
    END IF;

    WITH mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, i.player_id))
           COALESCE(m.player_id, i.player_id) AS player_id,
           i.player_name_j,
           i.player_name_e,
           i.last_seen_team_id,
           i.last_seen_jersey_number
      FROM public.data_patch_issue46_players i
      LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m
        ON m.old_player_id = i.player_id
     ORDER BY COALESCE(m.player_id, i.player_id), i.batch_order DESC
)
    SELECT COUNT(*) INTO expected_players FROM mapped_players;
    IF EXISTS (
        SELECT 1
          FROM public.data_patch_issue46_player_game_stats i
          LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
         GROUP BY i.schedule_key, COALESCE(m.player_id, i.player_id)
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Issue #46 player_game_stats primary-key conflict after player_id_map';
    END IF;

    SELECT COUNT(*) INTO n
      FROM public.teams live
      JOIN public.data_patch_backup_20260824_issue46_teams backup ON live.team_id = backup.team_id
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'teams changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_teams backup
     WHERE NOT EXISTS (
           SELECT 1 FROM public.teams live WHERE live.team_id = backup.team_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'teams rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.teams live
     WHERE live.team_id IN (SELECT team_id FROM public.data_patch_issue46_teams)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_teams backup WHERE backup.team_id = live.team_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'teams contains rows not present in backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.games live
      JOIN public.data_patch_backup_20260824_issue46_games backup ON live.schedule_key = backup.schedule_key
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'games changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_games backup
     WHERE NOT EXISTS (
           SELECT 1 FROM public.games live WHERE live.schedule_key = backup.schedule_key
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'games rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.games live
     WHERE live.schedule_key IN (SELECT schedule_key FROM public.data_patch_issue46_games)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_games backup WHERE backup.schedule_key = live.schedule_key
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'games contains rows not present in backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.game_team_stats live
      JOIN public.data_patch_backup_20260824_issue46_game_team_stats backup ON live.schedule_key = backup.schedule_key AND live.team_id = backup.team_id
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'game_team_stats changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_game_team_stats backup
     WHERE NOT EXISTS (
           SELECT 1 FROM public.game_team_stats live WHERE live.schedule_key = backup.schedule_key AND live.team_id = backup.team_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'game_team_stats rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.game_team_stats live
     WHERE live.schedule_key IN (SELECT schedule_key FROM public.data_patch_issue46_game_team_stats)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_game_team_stats backup WHERE backup.schedule_key = live.schedule_key AND backup.team_id = live.team_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'game_team_stats contains rows not present in backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.player_game_stats live
      JOIN public.data_patch_backup_20260824_issue46_player_game_stats backup ON live.schedule_key = backup.schedule_key AND live.player_id = backup.player_id
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_game_stats changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_player_game_stats backup
     WHERE NOT EXISTS (
           SELECT 1 FROM public.player_game_stats live WHERE live.schedule_key = backup.schedule_key AND live.player_id = backup.player_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_game_stats rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.player_game_stats live
     WHERE live.schedule_key IN (SELECT schedule_key FROM public.data_patch_issue46_player_game_stats)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_player_game_stats backup WHERE backup.schedule_key = live.schedule_key AND backup.player_id = live.player_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_game_stats contains rows not present in backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.team_name_history live
      JOIN public.data_patch_backup_20260824_issue46_team_name_history backup ON live.history_id = backup.history_id
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'team_name_history changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_team_name_history backup
     WHERE NOT EXISTS (
         SELECT 1 FROM public.team_name_history live WHERE live.history_id = backup.history_id
     );
    IF n <> 0 THEN
        RAISE EXCEPTION 'team_name_history rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.team_name_history live
     WHERE live.team_id IN (SELECT team_id FROM public.data_patch_issue46_teams)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_team_name_history backup WHERE backup.history_id = live.history_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'team_name_history contains rows not present in backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.player_name_history live
      JOIN public.data_patch_backup_20260824_issue46_player_name_history backup ON live.history_id = backup.history_id
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_name_history changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_player_name_history backup
     WHERE NOT EXISTS (
         SELECT 1 FROM public.player_name_history live WHERE live.history_id = backup.history_id
     );
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_name_history rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.player_name_history live
     WHERE live.player_id IN (SELECT DISTINCT COALESCE(m.player_id, i.player_id) FROM public.data_patch_issue46_players i LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_player_name_history backup WHERE backup.history_id = live.history_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_name_history contains rows not present in backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.player_affiliations live
      JOIN public.data_patch_backup_20260824_issue46_player_affiliations backup ON live.affiliation_id = backup.affiliation_id
     WHERE to_jsonb(live) IS DISTINCT FROM to_jsonb(backup);
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_affiliations changed after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.data_patch_backup_20260824_issue46_player_affiliations backup
     WHERE NOT EXISTS (
         SELECT 1 FROM public.player_affiliations live WHERE live.affiliation_id = backup.affiliation_id
     );
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_affiliations rows disappeared after backup: % rows', n;
    END IF;
    SELECT COUNT(*) INTO n
      FROM public.player_affiliations live
     WHERE live.player_id IN (SELECT DISTINCT COALESCE(m.player_id, i.player_id) FROM public.data_patch_issue46_players i LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id)
       AND NOT EXISTS (
           SELECT 1 FROM public.data_patch_backup_20260824_issue46_player_affiliations backup WHERE backup.affiliation_id = live.affiliation_id
       );
    IF n <> 0 THEN
        RAISE EXCEPTION 'player_affiliations contains rows not present in backup: % rows', n;
    END IF;

    INSERT INTO public.teams (team_id, team_name_j, team_name_e, team_short_name_j, team_short_name_e)
    SELECT team_id, team_name_j, team_name_e, team_short_name_j, team_short_name_e FROM public.data_patch_issue46_teams
    ON CONFLICT (team_id) DO UPDATE SET
        team_name_j = EXCLUDED.team_name_j,
        team_name_e = EXCLUDED.team_name_e,
        team_short_name_j = EXCLUDED.team_short_name_j,
        team_short_name_e = EXCLUDED.team_short_name_e,
        updated_at = NOW();

    INSERT INTO public.games (schedule_key, season, code, convention_key, convention_name_j, convention_name_e, year, setu, game_type, max_period, game_current_period, game_datetime_unix, game_datetime, game_date, stadium_cd, stadium_name_j, stadium_name_e, attendance, game_ended_flg, record_fixed_flg, boxscore_exists_flg, play_by_play_exists_flg, home_team_id, away_team_id, home_team_score_q1, home_team_score_q2, home_team_score_q3, home_team_score_q4, home_team_score_q5, home_team_score_total, away_team_score_q1, away_team_score_q2, away_team_score_q3, away_team_score_q4, away_team_score_q5, away_team_score_total, referee_id, referee_name_j, sub_referee_id_1, sub_referee_name_j_1, sub_referee_id_2, sub_referee_name_j_2, source_tab)
    SELECT schedule_key, season, code, convention_key, convention_name_j, convention_name_e, year, setu, game_type, max_period, game_current_period, game_datetime_unix, game_datetime, game_date, stadium_cd, stadium_name_j, stadium_name_e, attendance, game_ended_flg, record_fixed_flg, boxscore_exists_flg, play_by_play_exists_flg, home_team_id, away_team_id, home_team_score_q1, home_team_score_q2, home_team_score_q3, home_team_score_q4, home_team_score_q5, home_team_score_total, away_team_score_q1, away_team_score_q2, away_team_score_q3, away_team_score_q4, away_team_score_q5, away_team_score_total, referee_id, referee_name_j, sub_referee_id_1, sub_referee_name_j_1, sub_referee_id_2, sub_referee_name_j_2, source_tab FROM public.data_patch_issue46_games
    ON CONFLICT (schedule_key) DO UPDATE SET
        season = EXCLUDED.season,
        code = EXCLUDED.code,
        convention_key = EXCLUDED.convention_key,
        convention_name_j = EXCLUDED.convention_name_j,
        convention_name_e = EXCLUDED.convention_name_e,
        year = EXCLUDED.year,
        setu = EXCLUDED.setu,
        game_type = EXCLUDED.game_type,
        max_period = EXCLUDED.max_period,
        game_current_period = EXCLUDED.game_current_period,
        game_datetime_unix = EXCLUDED.game_datetime_unix,
        game_datetime = EXCLUDED.game_datetime,
        game_date = EXCLUDED.game_date,
        stadium_cd = EXCLUDED.stadium_cd,
        stadium_name_j = EXCLUDED.stadium_name_j,
        stadium_name_e = EXCLUDED.stadium_name_e,
        attendance = EXCLUDED.attendance,
        game_ended_flg = EXCLUDED.game_ended_flg,
        record_fixed_flg = EXCLUDED.record_fixed_flg,
        boxscore_exists_flg = EXCLUDED.boxscore_exists_flg,
        play_by_play_exists_flg = EXCLUDED.play_by_play_exists_flg,
        home_team_id = EXCLUDED.home_team_id,
        away_team_id = EXCLUDED.away_team_id,
        home_team_score_q1 = EXCLUDED.home_team_score_q1,
        home_team_score_q2 = EXCLUDED.home_team_score_q2,
        home_team_score_q3 = EXCLUDED.home_team_score_q3,
        home_team_score_q4 = EXCLUDED.home_team_score_q4,
        home_team_score_q5 = EXCLUDED.home_team_score_q5,
        home_team_score_total = EXCLUDED.home_team_score_total,
        away_team_score_q1 = EXCLUDED.away_team_score_q1,
        away_team_score_q2 = EXCLUDED.away_team_score_q2,
        away_team_score_q3 = EXCLUDED.away_team_score_q3,
        away_team_score_q4 = EXCLUDED.away_team_score_q4,
        away_team_score_q5 = EXCLUDED.away_team_score_q5,
        away_team_score_total = EXCLUDED.away_team_score_total,
        referee_id = EXCLUDED.referee_id,
        referee_name_j = EXCLUDED.referee_name_j,
        sub_referee_id_1 = EXCLUDED.sub_referee_id_1,
        sub_referee_name_j_1 = EXCLUDED.sub_referee_name_j_1,
        sub_referee_id_2 = EXCLUDED.sub_referee_id_2,
        sub_referee_name_j_2 = EXCLUDED.sub_referee_name_j_2,
        source_tab = EXCLUDED.source_tab,
        updated_at = NOW();

    WITH mapped_players AS (
    SELECT DISTINCT ON (COALESCE(m.player_id, i.player_id))
           COALESCE(m.player_id, i.player_id) AS player_id,
           i.player_name_j,
           i.player_name_e,
           i.last_seen_team_id,
           i.last_seen_jersey_number
      FROM public.data_patch_issue46_players i
      LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m
        ON m.old_player_id = i.player_id
     ORDER BY COALESCE(m.player_id, i.player_id), i.batch_order DESC
)
    INSERT INTO public.players (player_id, player_name_j, player_name_e, last_seen_team_id, last_seen_jersey_number)
    SELECT player_id, player_name_j, player_name_e, last_seen_team_id, last_seen_jersey_number
      FROM mapped_players
    ON CONFLICT (player_id) DO UPDATE SET
        player_name_j = EXCLUDED.player_name_j,
        player_name_e = EXCLUDED.player_name_e,
        last_seen_team_id = EXCLUDED.last_seen_team_id,
        last_seen_jersey_number = EXCLUDED.last_seen_jersey_number,
        updated_at = NOW();

    GET DIAGNOSTICS n = ROW_COUNT;
    IF n <> expected_players THEN
        RAISE EXCEPTION 'Issue #46 players upsert row-count mismatch: % <> %', n, expected_players;
    END IF;
    INSERT INTO public.game_team_stats (schedule_key, team_id, opponent_team_id, is_home, points, fgm, fga, fg_pct, fg2m, fg2a, fg2_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct, off_rebounds, def_rebounds, total_rebounds, assists, steals, blocks, blocks_received, turnovers, fouls, fouls_drawn, fast_break_points, second_chance_points, points_in_paint, possession, pace, off_rtg, def_rtg, net_rtg, ast_rtg, tov_rtg, pft_rtg, scp_rtg, efg_pct, ts_pct, ast_pct, tov_pct, ast_tov_ratio, play_pct, ft_freq, ft_rate, orb_pct, drb_pct, pft_pct, fbp_pct, scp_pct, pitp_pct, pt2_attempt_pct, pt3_attempt_pct, pt2_points_share, pt3_points_share, ft_points_share, shot_chances, eff, close_win_3pts_or_less, close_loss_3pts_or_less, opp_possession, opp_efg_pct, opp_ts_pct, opp_fg2_pct, opp_fg3_pct, opp_pt2_attempt_pct, opp_pt3_attempt_pct, opp_pt2_points_share, opp_pt3_points_share, opp_ft_points_share, opp_ast_pct, opp_ast_tov_ratio, opp_ast_rtg, opp_tov_pct, opp_orb_pct, opp_drb_pct, opp_shot_chances, opp_fbp_pct, opp_scp_pct, opp_scp_rtg, opp_pitp_pct, opp_pft_pct, opp_pft_rtg)
    SELECT schedule_key, team_id, opponent_team_id, is_home, points, fgm, fga, fg_pct, fg2m, fg2a, fg2_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct, off_rebounds, def_rebounds, total_rebounds, assists, steals, blocks, blocks_received, turnovers, fouls, fouls_drawn, fast_break_points, second_chance_points, points_in_paint, possession, pace, off_rtg, def_rtg, net_rtg, ast_rtg, tov_rtg, pft_rtg, scp_rtg, efg_pct, ts_pct, ast_pct, tov_pct, ast_tov_ratio, play_pct, ft_freq, ft_rate, orb_pct, drb_pct, pft_pct, fbp_pct, scp_pct, pitp_pct, pt2_attempt_pct, pt3_attempt_pct, pt2_points_share, pt3_points_share, ft_points_share, shot_chances, eff, close_win_3pts_or_less, close_loss_3pts_or_less, opp_possession, opp_efg_pct, opp_ts_pct, opp_fg2_pct, opp_fg3_pct, opp_pt2_attempt_pct, opp_pt3_attempt_pct, opp_pt2_points_share, opp_pt3_points_share, opp_ft_points_share, opp_ast_pct, opp_ast_tov_ratio, opp_ast_rtg, opp_tov_pct, opp_orb_pct, opp_drb_pct, opp_shot_chances, opp_fbp_pct, opp_scp_pct, opp_scp_rtg, opp_pitp_pct, opp_pft_pct, opp_pft_rtg FROM public.data_patch_issue46_game_team_stats ORDER BY schedule_key, team_id
    ON CONFLICT (schedule_key, team_id) DO UPDATE SET
        opponent_team_id = EXCLUDED.opponent_team_id,
        is_home = EXCLUDED.is_home,
        points = EXCLUDED.points,
        fgm = EXCLUDED.fgm,
        fga = EXCLUDED.fga,
        fg_pct = EXCLUDED.fg_pct,
        fg2m = EXCLUDED.fg2m,
        fg2a = EXCLUDED.fg2a,
        fg2_pct = EXCLUDED.fg2_pct,
        fg3m = EXCLUDED.fg3m,
        fg3a = EXCLUDED.fg3a,
        fg3_pct = EXCLUDED.fg3_pct,
        ftm = EXCLUDED.ftm,
        fta = EXCLUDED.fta,
        ft_pct = EXCLUDED.ft_pct,
        off_rebounds = EXCLUDED.off_rebounds,
        def_rebounds = EXCLUDED.def_rebounds,
        total_rebounds = EXCLUDED.total_rebounds,
        assists = EXCLUDED.assists,
        steals = EXCLUDED.steals,
        blocks = EXCLUDED.blocks,
        blocks_received = EXCLUDED.blocks_received,
        turnovers = EXCLUDED.turnovers,
        fouls = EXCLUDED.fouls,
        fouls_drawn = EXCLUDED.fouls_drawn,
        fast_break_points = EXCLUDED.fast_break_points,
        second_chance_points = EXCLUDED.second_chance_points,
        points_in_paint = EXCLUDED.points_in_paint,
        possession = EXCLUDED.possession,
        pace = EXCLUDED.pace,
        off_rtg = EXCLUDED.off_rtg,
        def_rtg = EXCLUDED.def_rtg,
        net_rtg = EXCLUDED.net_rtg,
        ast_rtg = EXCLUDED.ast_rtg,
        tov_rtg = EXCLUDED.tov_rtg,
        pft_rtg = EXCLUDED.pft_rtg,
        scp_rtg = EXCLUDED.scp_rtg,
        efg_pct = EXCLUDED.efg_pct,
        ts_pct = EXCLUDED.ts_pct,
        ast_pct = EXCLUDED.ast_pct,
        tov_pct = EXCLUDED.tov_pct,
        ast_tov_ratio = EXCLUDED.ast_tov_ratio,
        play_pct = EXCLUDED.play_pct,
        ft_freq = EXCLUDED.ft_freq,
        ft_rate = EXCLUDED.ft_rate,
        orb_pct = EXCLUDED.orb_pct,
        drb_pct = EXCLUDED.drb_pct,
        pft_pct = EXCLUDED.pft_pct,
        fbp_pct = EXCLUDED.fbp_pct,
        scp_pct = EXCLUDED.scp_pct,
        pitp_pct = EXCLUDED.pitp_pct,
        pt2_attempt_pct = EXCLUDED.pt2_attempt_pct,
        pt3_attempt_pct = EXCLUDED.pt3_attempt_pct,
        pt2_points_share = EXCLUDED.pt2_points_share,
        pt3_points_share = EXCLUDED.pt3_points_share,
        ft_points_share = EXCLUDED.ft_points_share,
        shot_chances = EXCLUDED.shot_chances,
        eff = EXCLUDED.eff,
        close_win_3pts_or_less = EXCLUDED.close_win_3pts_or_less,
        close_loss_3pts_or_less = EXCLUDED.close_loss_3pts_or_less,
        opp_possession = EXCLUDED.opp_possession,
        opp_efg_pct = EXCLUDED.opp_efg_pct,
        opp_ts_pct = EXCLUDED.opp_ts_pct,
        opp_fg2_pct = EXCLUDED.opp_fg2_pct,
        opp_fg3_pct = EXCLUDED.opp_fg3_pct,
        opp_pt2_attempt_pct = EXCLUDED.opp_pt2_attempt_pct,
        opp_pt3_attempt_pct = EXCLUDED.opp_pt3_attempt_pct,
        opp_pt2_points_share = EXCLUDED.opp_pt2_points_share,
        opp_pt3_points_share = EXCLUDED.opp_pt3_points_share,
        opp_ft_points_share = EXCLUDED.opp_ft_points_share,
        opp_ast_pct = EXCLUDED.opp_ast_pct,
        opp_ast_tov_ratio = EXCLUDED.opp_ast_tov_ratio,
        opp_ast_rtg = EXCLUDED.opp_ast_rtg,
        opp_tov_pct = EXCLUDED.opp_tov_pct,
        opp_orb_pct = EXCLUDED.opp_orb_pct,
        opp_drb_pct = EXCLUDED.opp_drb_pct,
        opp_shot_chances = EXCLUDED.opp_shot_chances,
        opp_fbp_pct = EXCLUDED.opp_fbp_pct,
        opp_scp_pct = EXCLUDED.opp_scp_pct,
        opp_scp_rtg = EXCLUDED.opp_scp_rtg,
        opp_pitp_pct = EXCLUDED.opp_pitp_pct,
        opp_pft_pct = EXCLUDED.opp_pft_pct,
        opp_pft_rtg = EXCLUDED.opp_pft_rtg,
        updated_at = NOW();

    INSERT INTO public.player_game_stats (schedule_key, player_id, team_id, jersey_number, is_starter, is_playing, play_time, points, fgm, fga, fg_pct, fg2m, fg2a, fg2_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct, off_rebounds, def_rebounds, total_rebounds, assists, turnovers, steals, blocks, blocks_received, fouls, fouls_drawn, fast_break_points, points_in_paint, second_chance_points, efficiency, plus_minus, ast_to_ratio, efg_pct, ts_pct, usg_pct)
    SELECT i.schedule_key, COALESCE(m.player_id, i.player_id) AS player_id, i.team_id, i.jersey_number, i.is_starter, i.is_playing, i.play_time, i.points, i.fgm, i.fga, i.fg_pct, i.fg2m, i.fg2a, i.fg2_pct, i.fg3m, i.fg3a, i.fg3_pct, i.ftm, i.fta, i.ft_pct, i.off_rebounds, i.def_rebounds, i.total_rebounds, i.assists, i.turnovers, i.steals, i.blocks, i.blocks_received, i.fouls, i.fouls_drawn, i.fast_break_points, i.points_in_paint, i.second_chance_points, i.efficiency, i.plus_minus, i.ast_to_ratio, i.efg_pct, i.ts_pct, i.usg_pct FROM public.data_patch_issue46_player_game_stats i LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id ORDER BY (SELECT g.game_datetime_unix FROM public.games g WHERE g.schedule_key = i.schedule_key) NULLS LAST, i.schedule_key, COALESCE(m.player_id, i.player_id)
    ON CONFLICT (schedule_key, player_id) DO UPDATE SET
        jersey_number = EXCLUDED.jersey_number,
        is_starter = EXCLUDED.is_starter,
        is_playing = EXCLUDED.is_playing,
        play_time = EXCLUDED.play_time,
        points = EXCLUDED.points,
        fgm = EXCLUDED.fgm,
        fga = EXCLUDED.fga,
        fg_pct = EXCLUDED.fg_pct,
        fg2m = EXCLUDED.fg2m,
        fg2a = EXCLUDED.fg2a,
        fg2_pct = EXCLUDED.fg2_pct,
        fg3m = EXCLUDED.fg3m,
        fg3a = EXCLUDED.fg3a,
        fg3_pct = EXCLUDED.fg3_pct,
        ftm = EXCLUDED.ftm,
        fta = EXCLUDED.fta,
        ft_pct = EXCLUDED.ft_pct,
        off_rebounds = EXCLUDED.off_rebounds,
        def_rebounds = EXCLUDED.def_rebounds,
        total_rebounds = EXCLUDED.total_rebounds,
        assists = EXCLUDED.assists,
        turnovers = EXCLUDED.turnovers,
        steals = EXCLUDED.steals,
        blocks = EXCLUDED.blocks,
        blocks_received = EXCLUDED.blocks_received,
        fouls = EXCLUDED.fouls,
        fouls_drawn = EXCLUDED.fouls_drawn,
        fast_break_points = EXCLUDED.fast_break_points,
        points_in_paint = EXCLUDED.points_in_paint,
        second_chance_points = EXCLUDED.second_chance_points,
        efficiency = EXCLUDED.efficiency,
        plus_minus = EXCLUDED.plus_minus,
        ast_to_ratio = EXCLUDED.ast_to_ratio,
        efg_pct = EXCLUDED.efg_pct,
        ts_pct = EXCLUDED.ts_pct,
        usg_pct = EXCLUDED.usg_pct,
        updated_at = NOW();

END;
$issue_46_fix$;

SELECT 'games' AS item, COUNT(*) AS row_count
  FROM public.games g JOIN public.data_patch_issue46_games i USING (schedule_key)
UNION ALL SELECT 'game_team_stats', COUNT(*)
  FROM public.game_team_stats s JOIN public.data_patch_issue46_game_team_stats i
    USING (schedule_key, team_id)
UNION ALL SELECT 'player_game_stats', COUNT(*)
  FROM public.player_game_stats s
  JOIN public.data_patch_issue46_player_game_stats i
    ON s.schedule_key = i.schedule_key
  LEFT JOIN public.data_patch_backup_20260824_issue46_player_id_map m ON m.old_player_id = i.player_id
 WHERE s.player_id = COALESCE(m.player_id, i.player_id);

COMMIT;
