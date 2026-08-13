-- Issue #10: 2021-22シーズン303試合の日時補正を元に戻す
-- 作成日: 2026-08-04
-- 対象: public.games のみ
-- 前提: 20260804_fix_2021_22_game_datetimes.sql が作成した
--       public.data_patch_backup_20260804_issue_10_games が存在すること
-- 想定更新件数: 303
-- 再実行: バックアップとgamesが同一になった後は更新件数ガードで停止する。
-- 最初のDO文が復旧本体で、単一ステートメントとして原子的に実行される。
-- 末尾のSELECTは復旧後の確認表示専用であり、復旧処理には影響しない。
DO $issue_10_rollback$
DECLARE
    backup_rows INTEGER;
    restorable_rows INTEGER;
    restored_rows INTEGER;
    mismatch_rows INTEGER;
BEGIN
    IF TO_REGCLASS('public.data_patch_backup_20260804_issue_10_games') IS NULL THEN
        RAISE EXCEPTION 'required backup table does not exist';
    END IF;
    SELECT COUNT(*) INTO backup_rows
    FROM public.data_patch_backup_20260804_issue_10_games;
    IF backup_rows <> 303 THEN
        RAISE EXCEPTION 'backup row count mismatch: expected=303 actual=%', backup_rows;
    END IF;
    SELECT COUNT(*) INTO restorable_rows
    FROM public.games g
    JOIN public.data_patch_backup_20260804_issue_10_games b USING (schedule_key)
    WHERE g.season = '2021-22'
      AND g.year = 2021
      AND (TO_TIMESTAMP(g.game_datetime_unix) AT TIME ZONE 'Asia/Tokyo')::DATE
              BETWEEN DATE '2022-01-01' AND DATE '2022-04-30';
    IF restorable_rows <> 303 THEN
        RAISE EXCEPTION
            'current corrected rows mismatch: expected=303 actual=%',
            restorable_rows;
    END IF;
    UPDATE public.games g
    SET
        season = b.season,
        year = b.year,
        game_datetime_unix = b.game_datetime_unix,
        game_datetime = b.game_datetime,
        game_date = b.game_date,
        source_tab = b.source_tab,
        updated_at = b.updated_at
    FROM public.data_patch_backup_20260804_issue_10_games b
    WHERE g.schedule_key = b.schedule_key
      AND (
          g.season IS DISTINCT FROM b.season
          OR g.year IS DISTINCT FROM b.year
          OR g.game_datetime_unix IS DISTINCT FROM b.game_datetime_unix
          OR g.game_datetime IS DISTINCT FROM b.game_datetime
          OR g.game_date IS DISTINCT FROM b.game_date
          OR g.source_tab IS DISTINCT FROM b.source_tab
          OR g.updated_at IS DISTINCT FROM b.updated_at
      );
    GET DIAGNOSTICS restored_rows = ROW_COUNT;
    IF restored_rows <> 303 THEN
        RAISE EXCEPTION 'restored row count mismatch: expected=303 actual=%', restored_rows;
    END IF;
    SELECT COUNT(*) INTO mismatch_rows
    FROM public.games g
    JOIN public.data_patch_backup_20260804_issue_10_games b USING (schedule_key)
    WHERE g.season IS DISTINCT FROM b.season
       OR g.year IS DISTINCT FROM b.year
       OR g.game_datetime_unix IS DISTINCT FROM b.game_datetime_unix
       OR g.game_datetime IS DISTINCT FROM b.game_datetime
       OR g.game_date IS DISTINCT FROM b.game_date
       OR g.source_tab IS DISTINCT FROM b.source_tab
       OR g.updated_at IS DISTINCT FROM b.updated_at;
    IF mismatch_rows <> 0 THEN
        RAISE EXCEPTION 'rollback postcheck mismatch rows: expected=0 actual=%', mismatch_rows;
    END IF;
END;
$issue_10_rollback$;
SELECT
    season,
    year,
    MIN(game_date) AS min_game_date,
    MAX(game_date) AS max_game_date,
    COUNT(*) AS game_count
FROM public.games
WHERE season = '2021-22'
GROUP BY season, year
ORDER BY year;
-- Issue #10の確認完了後、バックアップが不要になった場合のみ手動で実行する:
-- DROP TABLE public.data_patch_backup_20260804_issue_10_games;
