-- Issue #11: game_team_statsの得点系23列を補正
-- 作成日: 2026-08-04
-- 対象: public.game_team_stats 全10,846行
-- 関連Issue: https://github.com/tj-999-comp/B_Stats_Site/issues/11
-- 得点正本: public.games.home_team_score_total / away_team_score_total
-- 想定更新件数: 10,846
-- 再実行: 不可。成功後はバックアップテーブルの存在と事前状態ガードで停止する。
--
-- TeamPTRを得点として保存していたため、pointsと、それに依存して永続化された
-- レーティング・得点比率・相手指標・接戦フラグを同時に再計算する。
-- PFTの元値は未保存だが、現行pft_pct * 誤pointsから整数として復元し、
-- pft_rtgから復元した値とも一致することを更新前に検証する。
--
-- 最初のDO文がバックアップ・更新・検証を単一ステートメントで原子的に実行する。
-- DBeaverまたはSupabase SQL Editorではファイル全体を実行し、
-- 途中のUPDATEだけを抜き出さないこと。末尾のSELECTは確認表示専用。
DO $issue_11_patch$
DECLARE
    expected_rows CONSTANT INTEGER := 10846;
    live_rows INTEGER;
    paired_rows INTEGER;
    invalid_base_rows INTEGER;
    score_shot_mismatch_rows INTEGER;
    bad_points_rows INTEGER;
    pft_recovery_mismatch_rows INTEGER;
    patch_rows INTEGER;
    backup_rows INTEGER;
    updated_rows INTEGER;
    postcheck_rows INTEGER;
BEGIN
    LOCK TABLE public.games IN SHARE MODE;
    LOCK TABLE public.game_team_stats IN SHARE ROW EXCLUSIVE MODE;

    SELECT COUNT(*) INTO live_rows
    FROM public.game_team_stats;
    IF live_rows <> expected_rows THEN
        RAISE EXCEPTION
            'game_team_stats row count mismatch: expected=% actual=%',
            expected_rows,
            live_rows;
    END IF;

    SELECT COUNT(*) INTO paired_rows
    FROM public.game_team_stats s
    JOIN public.games g
      ON g.schedule_key = s.schedule_key
    JOIN public.game_team_stats opp
      ON opp.schedule_key = s.schedule_key
     AND opp.team_id = s.opponent_team_id
    WHERE (
        s.is_home
        AND s.team_id = g.home_team_id
        AND s.opponent_team_id = g.away_team_id
        AND NOT opp.is_home
    ) OR (
        NOT s.is_home
        AND s.team_id = g.away_team_id
        AND s.opponent_team_id = g.home_team_id
        AND opp.is_home
    );
    IF paired_rows <> expected_rows THEN
        RAISE EXCEPTION
            'game/opponent pairing mismatch: expected=% actual=%',
            expected_rows,
            paired_rows;
    END IF;

    SELECT COUNT(*) INTO invalid_base_rows
    FROM public.game_team_stats
    WHERE points IS NULL
       OR points <= 0
       OR fgm IS NULL
       OR fga IS NULL
       OR fg2m IS NULL
       OR fg3m IS NULL
       OR ftm IS NULL
       OR fta IS NULL
       OR total_rebounds IS NULL
       OR assists IS NULL
       OR steals IS NULL
       OR blocks IS NULL
       OR turnovers IS NULL
       OR fast_break_points IS NULL
       OR second_chance_points IS NULL
       OR points_in_paint IS NULL
       OR possession IS NULL
       OR pft_pct IS NULL
       OR pft_rtg IS NULL
       OR opp_pft_pct IS NULL;
    IF invalid_base_rows <> 0 THEN
        RAISE EXCEPTION
            'invalid base rows: expected=0 actual=%',
            invalid_base_rows;
    END IF;

    SELECT COUNT(*) INTO score_shot_mismatch_rows
    FROM public.game_team_stats s
    JOIN public.games g USING (schedule_key)
    WHERE (
        CASE
            WHEN s.is_home THEN g.home_team_score_total
            ELSE g.away_team_score_total
        END
    ) IS DISTINCT FROM (2 * s.fg2m + 3 * s.fg3m + s.ftm);
    IF score_shot_mismatch_rows <> 0 THEN
        RAISE EXCEPTION
            'score/shot-formula mismatch rows: expected=0 actual=%',
            score_shot_mismatch_rows;
    END IF;

    SELECT COUNT(*) INTO bad_points_rows
    FROM public.game_team_stats s
    JOIN public.games g USING (schedule_key)
    WHERE s.points IS DISTINCT FROM (
        CASE
            WHEN s.is_home THEN g.home_team_score_total
            ELSE g.away_team_score_total
        END
    );
    IF bad_points_rows <> expected_rows THEN
        RAISE EXCEPTION
            'unexpected pre-patch points state: expected_bad=% actual_bad=%',
            expected_rows,
            bad_points_rows;
    END IF;

    SELECT COUNT(*) INTO pft_recovery_mismatch_rows
    FROM public.game_team_stats s
    JOIN public.game_team_stats opp
      ON opp.schedule_key = s.schedule_key
     AND opp.team_id = s.opponent_team_id
    WHERE ROUND(s.pft_pct * s.points)::INTEGER
              IS DISTINCT FROM ROUND(s.pft_rtg * GREATEST(1, opp.turnovers))::INTEGER
       OR ROUND(s.opp_pft_pct * opp.points)::INTEGER
              IS DISTINCT FROM ROUND(opp.pft_pct * opp.points)::INTEGER;
    IF pft_recovery_mismatch_rows <> 0 THEN
        RAISE EXCEPTION
            'PFT recovery mismatch rows: expected=0 actual=%',
            pft_recovery_mismatch_rows;
    END IF;

    IF TO_REGCLASS(
        'public.data_patch_backup_20260804_issue_11_game_team_stats'
    ) IS NOT NULL THEN
        RAISE EXCEPTION
            'backup table already exists; patch may already have been applied';
    END IF;

    CREATE TEMP TABLE issue_11_game_team_patch (
        schedule_key BIGINT NOT NULL,
        team_id TEXT NOT NULL,
        points INTEGER NOT NULL,
        ts_pct NUMERIC(8, 4),
        off_rtg NUMERIC(10, 4),
        def_rtg NUMERIC(10, 4),
        net_rtg NUMERIC(10, 4),
        pft_pct NUMERIC(8, 4),
        fbp_pct NUMERIC(8, 4),
        scp_pct NUMERIC(8, 4),
        pitp_pct NUMERIC(8, 4),
        pt2_points_share NUMERIC(8, 4),
        pt3_points_share NUMERIC(8, 4),
        ft_points_share NUMERIC(8, 4),
        eff NUMERIC(10, 4),
        close_win_3pts_or_less INTEGER,
        close_loss_3pts_or_less INTEGER,
        opp_ts_pct NUMERIC(8, 4),
        opp_pt2_points_share NUMERIC(8, 4),
        opp_pt3_points_share NUMERIC(8, 4),
        opp_ft_points_share NUMERIC(8, 4),
        opp_fbp_pct NUMERIC(8, 4),
        opp_scp_pct NUMERIC(8, 4),
        opp_pitp_pct NUMERIC(8, 4),
        opp_pft_pct NUMERIC(8, 4),
        PRIMARY KEY (schedule_key, team_id)
    ) ON COMMIT DROP;

    INSERT INTO issue_11_game_team_patch (
        schedule_key,
        team_id,
        points,
        ts_pct,
        off_rtg,
        def_rtg,
        net_rtg,
        pft_pct,
        fbp_pct,
        scp_pct,
        pitp_pct,
        pt2_points_share,
        pt3_points_share,
        ft_points_share,
        eff,
        close_win_3pts_or_less,
        close_loss_3pts_or_less,
        opp_ts_pct,
        opp_pt2_points_share,
        opp_pt3_points_share,
        opp_ft_points_share,
        opp_fbp_pct,
        opp_scp_pct,
        opp_pitp_pct,
        opp_pft_pct
    )
    WITH source AS (
        SELECT
            s.*,
            opp.fga AS opp_fga,
            opp.fg2m AS opp_fg2m,
            opp.fg3m AS opp_fg3m,
            opp.ftm AS opp_ftm,
            opp.fta AS opp_fta,
            opp.fast_break_points AS opp_fast_break_points,
            opp.second_chance_points AS opp_second_chance_points,
            opp.points_in_paint AS opp_points_in_paint,
            CASE
                WHEN s.is_home THEN g.home_team_score_total
                ELSE g.away_team_score_total
            END AS corrected_points,
            CASE
                WHEN s.is_home THEN g.away_team_score_total
                ELSE g.home_team_score_total
            END AS corrected_opp_points,
            ROUND(s.pft_pct * s.points)::INTEGER AS points_from_turnover,
            ROUND(opp.pft_pct * opp.points)::INTEGER AS opp_points_from_turnover
        FROM public.game_team_stats s
        JOIN public.games g
          ON g.schedule_key = s.schedule_key
        JOIN public.game_team_stats opp
          ON opp.schedule_key = s.schedule_key
         AND opp.team_id = s.opponent_team_id
    )
    SELECT
        schedule_key,
        team_id,
        corrected_points,
        corrected_points::NUMERIC
            / NULLIF(2 * (fga::NUMERIC + 0.44 * fta), 0),
        100 * corrected_points::NUMERIC / NULLIF(possession, 0),
        100 * corrected_opp_points::NUMERIC / NULLIF(possession, 0),
        100 * (corrected_points - corrected_opp_points)::NUMERIC
            / NULLIF(possession, 0),
        points_from_turnover::NUMERIC / NULLIF(corrected_points, 0),
        fast_break_points::NUMERIC / NULLIF(corrected_points, 0),
        second_chance_points::NUMERIC / NULLIF(corrected_points, 0),
        points_in_paint::NUMERIC / NULLIF(corrected_points, 0),
        (2 * fg2m)::NUMERIC / NULLIF(corrected_points, 0),
        (3 * fg3m)::NUMERIC / NULLIF(corrected_points, 0),
        ftm::NUMERIC / NULLIF(corrected_points, 0),
        corrected_points
            + total_rebounds
            + assists
            + steals
            + blocks
            - (fga - fgm)
            - (fta - ftm)
            - turnovers,
        CASE
            WHEN corrected_points - corrected_opp_points BETWEEN 1 AND 3 THEN 1
            ELSE 0
        END,
        CASE
            WHEN corrected_points - corrected_opp_points BETWEEN -3 AND -1 THEN 1
            ELSE 0
        END,
        corrected_opp_points::NUMERIC
            / NULLIF(2 * (opp_fga::NUMERIC + 0.44 * opp_fta), 0),
        (2 * opp_fg2m)::NUMERIC / NULLIF(corrected_opp_points, 0),
        (3 * opp_fg3m)::NUMERIC / NULLIF(corrected_opp_points, 0),
        opp_ftm::NUMERIC / NULLIF(corrected_opp_points, 0),
        opp_fast_break_points::NUMERIC / NULLIF(corrected_opp_points, 0),
        opp_second_chance_points::NUMERIC / NULLIF(corrected_opp_points, 0),
        opp_points_in_paint::NUMERIC / NULLIF(corrected_opp_points, 0),
        opp_points_from_turnover::NUMERIC / NULLIF(corrected_opp_points, 0)
    FROM source;

    SELECT COUNT(*) INTO patch_rows
    FROM issue_11_game_team_patch;
    IF patch_rows <> expected_rows THEN
        RAISE EXCEPTION
            'patch row count mismatch: expected=% actual=%',
            expected_rows,
            patch_rows;
    END IF;

    CREATE TABLE public.data_patch_backup_20260804_issue_11_game_team_stats (
        schedule_key BIGINT NOT NULL,
        team_id TEXT NOT NULL,
        points INTEGER,
        ts_pct NUMERIC(8, 4),
        off_rtg NUMERIC(10, 4),
        def_rtg NUMERIC(10, 4),
        net_rtg NUMERIC(10, 4),
        pft_pct NUMERIC(8, 4),
        fbp_pct NUMERIC(8, 4),
        scp_pct NUMERIC(8, 4),
        pitp_pct NUMERIC(8, 4),
        pt2_points_share NUMERIC(8, 4),
        pt3_points_share NUMERIC(8, 4),
        ft_points_share NUMERIC(8, 4),
        eff NUMERIC(10, 4),
        close_win_3pts_or_less INTEGER,
        close_loss_3pts_or_less INTEGER,
        opp_ts_pct NUMERIC(8, 4),
        opp_pt2_points_share NUMERIC(8, 4),
        opp_pt3_points_share NUMERIC(8, 4),
        opp_ft_points_share NUMERIC(8, 4),
        opp_fbp_pct NUMERIC(8, 4),
        opp_scp_pct NUMERIC(8, 4),
        opp_pitp_pct NUMERIC(8, 4),
        opp_pft_pct NUMERIC(8, 4),
        updated_at TIMESTAMPTZ NOT NULL,
        backed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (schedule_key, team_id)
    );
    ALTER TABLE public.data_patch_backup_20260804_issue_11_game_team_stats
        ENABLE ROW LEVEL SECURITY;
    REVOKE ALL ON TABLE public.data_patch_backup_20260804_issue_11_game_team_stats
        FROM anon, authenticated;

    INSERT INTO public.data_patch_backup_20260804_issue_11_game_team_stats (
        schedule_key,
        team_id,
        points,
        ts_pct,
        off_rtg,
        def_rtg,
        net_rtg,
        pft_pct,
        fbp_pct,
        scp_pct,
        pitp_pct,
        pt2_points_share,
        pt3_points_share,
        ft_points_share,
        eff,
        close_win_3pts_or_less,
        close_loss_3pts_or_less,
        opp_ts_pct,
        opp_pt2_points_share,
        opp_pt3_points_share,
        opp_ft_points_share,
        opp_fbp_pct,
        opp_scp_pct,
        opp_pitp_pct,
        opp_pft_pct,
        updated_at
    )
    SELECT
        schedule_key,
        team_id,
        points,
        ts_pct,
        off_rtg,
        def_rtg,
        net_rtg,
        pft_pct,
        fbp_pct,
        scp_pct,
        pitp_pct,
        pt2_points_share,
        pt3_points_share,
        ft_points_share,
        eff,
        close_win_3pts_or_less,
        close_loss_3pts_or_less,
        opp_ts_pct,
        opp_pt2_points_share,
        opp_pt3_points_share,
        opp_ft_points_share,
        opp_fbp_pct,
        opp_scp_pct,
        opp_pitp_pct,
        opp_pft_pct,
        updated_at
    FROM public.game_team_stats;

    SELECT COUNT(*) INTO backup_rows
    FROM public.data_patch_backup_20260804_issue_11_game_team_stats;
    IF backup_rows <> expected_rows THEN
        RAISE EXCEPTION
            'backup row count mismatch: expected=% actual=%',
            expected_rows,
            backup_rows;
    END IF;

    UPDATE public.game_team_stats s
    SET
        points = p.points,
        ts_pct = p.ts_pct,
        off_rtg = p.off_rtg,
        def_rtg = p.def_rtg,
        net_rtg = p.net_rtg,
        pft_pct = p.pft_pct,
        fbp_pct = p.fbp_pct,
        scp_pct = p.scp_pct,
        pitp_pct = p.pitp_pct,
        pt2_points_share = p.pt2_points_share,
        pt3_points_share = p.pt3_points_share,
        ft_points_share = p.ft_points_share,
        eff = p.eff,
        close_win_3pts_or_less = p.close_win_3pts_or_less,
        close_loss_3pts_or_less = p.close_loss_3pts_or_less,
        opp_ts_pct = p.opp_ts_pct,
        opp_pt2_points_share = p.opp_pt2_points_share,
        opp_pt3_points_share = p.opp_pt3_points_share,
        opp_ft_points_share = p.opp_ft_points_share,
        opp_fbp_pct = p.opp_fbp_pct,
        opp_scp_pct = p.opp_scp_pct,
        opp_pitp_pct = p.opp_pitp_pct,
        opp_pft_pct = p.opp_pft_pct,
        updated_at = NOW()
    FROM issue_11_game_team_patch p
    WHERE s.schedule_key = p.schedule_key
      AND s.team_id = p.team_id;

    GET DIAGNOSTICS updated_rows = ROW_COUNT;
    IF updated_rows <> expected_rows THEN
        RAISE EXCEPTION
            'updated row count mismatch: expected=% actual=%',
            expected_rows,
            updated_rows;
    END IF;

    SELECT COUNT(*) INTO postcheck_rows
    FROM public.game_team_stats s
    JOIN issue_11_game_team_patch p USING (schedule_key, team_id)
    WHERE s.points IS DISTINCT FROM p.points
       OR s.ts_pct IS DISTINCT FROM p.ts_pct
       OR s.off_rtg IS DISTINCT FROM p.off_rtg
       OR s.def_rtg IS DISTINCT FROM p.def_rtg
       OR s.net_rtg IS DISTINCT FROM p.net_rtg
       OR s.pft_pct IS DISTINCT FROM p.pft_pct
       OR s.fbp_pct IS DISTINCT FROM p.fbp_pct
       OR s.scp_pct IS DISTINCT FROM p.scp_pct
       OR s.pitp_pct IS DISTINCT FROM p.pitp_pct
       OR s.pt2_points_share IS DISTINCT FROM p.pt2_points_share
       OR s.pt3_points_share IS DISTINCT FROM p.pt3_points_share
       OR s.ft_points_share IS DISTINCT FROM p.ft_points_share
       OR s.eff IS DISTINCT FROM p.eff
       OR s.close_win_3pts_or_less IS DISTINCT FROM p.close_win_3pts_or_less
       OR s.close_loss_3pts_or_less IS DISTINCT FROM p.close_loss_3pts_or_less
       OR s.opp_ts_pct IS DISTINCT FROM p.opp_ts_pct
       OR s.opp_pt2_points_share IS DISTINCT FROM p.opp_pt2_points_share
       OR s.opp_pt3_points_share IS DISTINCT FROM p.opp_pt3_points_share
       OR s.opp_ft_points_share IS DISTINCT FROM p.opp_ft_points_share
       OR s.opp_fbp_pct IS DISTINCT FROM p.opp_fbp_pct
       OR s.opp_scp_pct IS DISTINCT FROM p.opp_scp_pct
       OR s.opp_pitp_pct IS DISTINCT FROM p.opp_pitp_pct
       OR s.opp_pft_pct IS DISTINCT FROM p.opp_pft_pct;
    IF postcheck_rows <> 0 THEN
        RAISE EXCEPTION
            'postcheck mismatch rows: expected=0 actual=%',
            postcheck_rows;
    END IF;
END;
$issue_11_patch$;

SELECT
    COUNT(*) AS game_team_stats_rows,
    COUNT(*) FILTER (
        WHERE s.points IS DISTINCT FROM CASE
            WHEN s.is_home THEN g.home_team_score_total
            ELSE g.away_team_score_total
        END
    ) AS points_score_mismatch_rows,
    COUNT(*) FILTER (
        WHERE s.points IS DISTINCT FROM (2 * s.fg2m + 3 * s.fg3m + s.ftm)
    ) AS points_shot_formula_mismatch_rows
FROM public.game_team_stats s
JOIN public.games g USING (schedule_key);

-- Issue #11の確認完了後、バックアップが不要になった場合のみ手動で実行する:
-- DROP TABLE public.data_patch_backup_20260804_issue_11_game_team_stats;
