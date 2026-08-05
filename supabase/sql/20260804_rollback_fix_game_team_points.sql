-- Issue #11: game_team_statsの得点系23列を補正前へ戻す
-- 作成日: 2026-08-04
-- 対象: public.game_team_stats 全10,846行
-- 前提: 20260804_fix_game_team_points.sql が作成した
--       public.data_patch_backup_20260804_issue_11_game_team_stats が存在すること
-- 想定更新件数: 10,846
-- 再実行: バックアップとgame_team_statsが同一になった後は更新件数ガードで停止する。
--
-- 最初のDO文が復旧本体で、単一ステートメントとして原子的に実行される。
-- 末尾のSELECTは復旧後の確認表示専用であり、復旧処理には影響しない。
DO $issue_11_rollback$
DECLARE
    expected_rows CONSTANT INTEGER := 10846;
    backup_rows INTEGER;
    live_rows INTEGER;
    restorable_rows INTEGER;
    restored_rows INTEGER;
    mismatch_rows INTEGER;
BEGIN
    LOCK TABLE public.game_team_stats IN SHARE ROW EXCLUSIVE MODE;

    IF TO_REGCLASS(
        'public.data_patch_backup_20260804_issue_11_game_team_stats'
    ) IS NULL THEN
        RAISE EXCEPTION 'required backup table does not exist';
    END IF;

    SELECT COUNT(*) INTO backup_rows
    FROM public.data_patch_backup_20260804_issue_11_game_team_stats;
    IF backup_rows <> expected_rows THEN
        RAISE EXCEPTION
            'backup row count mismatch: expected=% actual=%',
            expected_rows,
            backup_rows;
    END IF;

    SELECT COUNT(*) INTO live_rows
    FROM public.game_team_stats;
    IF live_rows <> expected_rows THEN
        RAISE EXCEPTION
            'game_team_stats row count mismatch: expected=% actual=%',
            expected_rows,
            live_rows;
    END IF;

    SELECT COUNT(*) INTO restorable_rows
    FROM public.game_team_stats s
    JOIN public.data_patch_backup_20260804_issue_11_game_team_stats b
      USING (schedule_key, team_id)
    WHERE s.points IS DISTINCT FROM b.points
       OR s.ts_pct IS DISTINCT FROM b.ts_pct
       OR s.off_rtg IS DISTINCT FROM b.off_rtg
       OR s.def_rtg IS DISTINCT FROM b.def_rtg
       OR s.net_rtg IS DISTINCT FROM b.net_rtg
       OR s.pft_pct IS DISTINCT FROM b.pft_pct
       OR s.fbp_pct IS DISTINCT FROM b.fbp_pct
       OR s.scp_pct IS DISTINCT FROM b.scp_pct
       OR s.pitp_pct IS DISTINCT FROM b.pitp_pct
       OR s.pt2_points_share IS DISTINCT FROM b.pt2_points_share
       OR s.pt3_points_share IS DISTINCT FROM b.pt3_points_share
       OR s.ft_points_share IS DISTINCT FROM b.ft_points_share
       OR s.eff IS DISTINCT FROM b.eff
       OR s.close_win_3pts_or_less IS DISTINCT FROM b.close_win_3pts_or_less
       OR s.close_loss_3pts_or_less IS DISTINCT FROM b.close_loss_3pts_or_less
       OR s.opp_ts_pct IS DISTINCT FROM b.opp_ts_pct
       OR s.opp_pt2_points_share IS DISTINCT FROM b.opp_pt2_points_share
       OR s.opp_pt3_points_share IS DISTINCT FROM b.opp_pt3_points_share
       OR s.opp_ft_points_share IS DISTINCT FROM b.opp_ft_points_share
       OR s.opp_fbp_pct IS DISTINCT FROM b.opp_fbp_pct
       OR s.opp_scp_pct IS DISTINCT FROM b.opp_scp_pct
       OR s.opp_pitp_pct IS DISTINCT FROM b.opp_pitp_pct
       OR s.opp_pft_pct IS DISTINCT FROM b.opp_pft_pct
       OR s.updated_at IS DISTINCT FROM b.updated_at;
    IF restorable_rows <> expected_rows THEN
        RAISE EXCEPTION
            'restorable row count mismatch: expected=% actual=%',
            expected_rows,
            restorable_rows;
    END IF;

    UPDATE public.game_team_stats s
    SET
        points = b.points,
        ts_pct = b.ts_pct,
        off_rtg = b.off_rtg,
        def_rtg = b.def_rtg,
        net_rtg = b.net_rtg,
        pft_pct = b.pft_pct,
        fbp_pct = b.fbp_pct,
        scp_pct = b.scp_pct,
        pitp_pct = b.pitp_pct,
        pt2_points_share = b.pt2_points_share,
        pt3_points_share = b.pt3_points_share,
        ft_points_share = b.ft_points_share,
        eff = b.eff,
        close_win_3pts_or_less = b.close_win_3pts_or_less,
        close_loss_3pts_or_less = b.close_loss_3pts_or_less,
        opp_ts_pct = b.opp_ts_pct,
        opp_pt2_points_share = b.opp_pt2_points_share,
        opp_pt3_points_share = b.opp_pt3_points_share,
        opp_ft_points_share = b.opp_ft_points_share,
        opp_fbp_pct = b.opp_fbp_pct,
        opp_scp_pct = b.opp_scp_pct,
        opp_pitp_pct = b.opp_pitp_pct,
        opp_pft_pct = b.opp_pft_pct,
        updated_at = b.updated_at
    FROM public.data_patch_backup_20260804_issue_11_game_team_stats b
    WHERE s.schedule_key = b.schedule_key
      AND s.team_id = b.team_id;

    GET DIAGNOSTICS restored_rows = ROW_COUNT;
    IF restored_rows <> expected_rows THEN
        RAISE EXCEPTION
            'restored row count mismatch: expected=% actual=%',
            expected_rows,
            restored_rows;
    END IF;

    SELECT COUNT(*) INTO mismatch_rows
    FROM public.game_team_stats s
    JOIN public.data_patch_backup_20260804_issue_11_game_team_stats b
      USING (schedule_key, team_id)
    WHERE s.points IS DISTINCT FROM b.points
       OR s.ts_pct IS DISTINCT FROM b.ts_pct
       OR s.off_rtg IS DISTINCT FROM b.off_rtg
       OR s.def_rtg IS DISTINCT FROM b.def_rtg
       OR s.net_rtg IS DISTINCT FROM b.net_rtg
       OR s.pft_pct IS DISTINCT FROM b.pft_pct
       OR s.fbp_pct IS DISTINCT FROM b.fbp_pct
       OR s.scp_pct IS DISTINCT FROM b.scp_pct
       OR s.pitp_pct IS DISTINCT FROM b.pitp_pct
       OR s.pt2_points_share IS DISTINCT FROM b.pt2_points_share
       OR s.pt3_points_share IS DISTINCT FROM b.pt3_points_share
       OR s.ft_points_share IS DISTINCT FROM b.ft_points_share
       OR s.eff IS DISTINCT FROM b.eff
       OR s.close_win_3pts_or_less IS DISTINCT FROM b.close_win_3pts_or_less
       OR s.close_loss_3pts_or_less IS DISTINCT FROM b.close_loss_3pts_or_less
       OR s.opp_ts_pct IS DISTINCT FROM b.opp_ts_pct
       OR s.opp_pt2_points_share IS DISTINCT FROM b.opp_pt2_points_share
       OR s.opp_pt3_points_share IS DISTINCT FROM b.opp_pt3_points_share
       OR s.opp_ft_points_share IS DISTINCT FROM b.opp_ft_points_share
       OR s.opp_fbp_pct IS DISTINCT FROM b.opp_fbp_pct
       OR s.opp_scp_pct IS DISTINCT FROM b.opp_scp_pct
       OR s.opp_pitp_pct IS DISTINCT FROM b.opp_pitp_pct
       OR s.opp_pft_pct IS DISTINCT FROM b.opp_pft_pct
       OR s.updated_at IS DISTINCT FROM b.updated_at;
    IF mismatch_rows <> 0 THEN
        RAISE EXCEPTION
            'rollback postcheck mismatch rows: expected=0 actual=%',
            mismatch_rows;
    END IF;
END;
$issue_11_rollback$;

SELECT
    COUNT(*) AS game_team_stats_rows,
    COUNT(*) FILTER (
        WHERE s.points IS DISTINCT FROM CASE
            WHEN s.is_home THEN g.home_team_score_total
            ELSE g.away_team_score_total
        END
    ) AS restored_points_score_mismatch_rows
FROM public.game_team_stats s
JOIN public.games g USING (schedule_key);

-- Issue #11の確認完了後、バックアップが不要になった場合のみ手動で実行する:
-- DROP TABLE public.data_patch_backup_20260804_issue_11_game_team_stats;
