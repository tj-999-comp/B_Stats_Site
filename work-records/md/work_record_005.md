# 作業記録 005: 2021-22シーズン303試合の日時・year補正
作成日: 2026-08-04

## 対象

- GitHub Issue: [#10 2021-22シーズンに誤配属された可能性がある303試合を修正する](https://github.com/tj-999-comp/B_Stats_Site/issues/10)
- 対象テーブル: `public.games`
- 対象条件: `season = '2021-22' AND year = 2020`
- 対象件数: 303件

## 原因と対応方針

対象行は `year` だけでなく、`game_datetime`、`game_datetime_unix`、`game_date` も実際の開催年より約1年早い値だった。既存値の日付だけを機械的に加算せず、B.LEAGUE公式サイトから2022年1月〜4月分を再取得し、そのJSONを補正値の正本とした。

## 実施事項

1. `season = 2021-22` の2022年1月〜4月を月単位で再取得した。
2. 再取得した月次JSON 4ファイルについて、合計303試合、`schedule_key` 303件重複なし、取得失敗0件であることを確認した。
3. 旧JSONと比較し、303件の `schedule_key`、対戦カード、スコア、home/away boxscore、試合概要が一致することを確認した。日時だけが2022年の正しい値へ変わることを確認した。
4. 4ファイルすべてを `scripts.db.upsert_games --dry-run` で変換し、エラーがないことを確認した。
5. 追跡済み月次JSONを再取得結果へ更新した。
6. `public.games` のみを対象とするデータパッチとロールバックSQLを作成した。
7. DBeaver／トランザクションプーラー経由でも一時テーブルのセッション切替に依存しないよう、バックアップ、事前条件確認、303件更新、事後確認を単一の `DO` 文へまとめた。
8. 使い捨てローカルPostgreSQLで、適用、永続バックアップ303件、ロールバック、再実行防止ガードを確認した。
9. live DBへデータパッチを適用し、シーズン別件数を再集計した。

## 関連ファイル

- `scraper/data/season_2021-2022/games_2021-22_2022-01-01_2022-01-31.json`
- `scraper/data/season_2021-2022/games_2021-22_2022-02-01_2022-02-28.json`
- `scraper/data/season_2021-2022/games_2021-22_2022-03-01_2022-03-31.json`
- `scraper/data/season_2021-2022/games_2021-22_2022-04-01_2022-04-30.json`
- `supabase/sql/20260804_fix_2021_22_game_datetimes.sql`
- `supabase/sql/20260804_rollback_fix_2021_22_game_datetimes.sql`

更新SQLは適用前の303行を `public.data_patch_backup_20260804_issue_10_games` に保存してから、次の項目を補正する。

- `year`: `2020` から `2021`
- `game_datetime_unix`: 再取得JSONの値
- `game_datetime`: 再取得日時からJSTで再生成
- `game_date`: 再取得日時からJSTで再生成
- `source_tab`: 再取得JSONの値
- `updated_at`: 適用時刻

## live DB適用後の確認結果

```text
2019  2019-20  367
2020  2020-21  590
2021  2021-22  618
2022  2022-23  731
```

補正前に存在した `year = 2020 AND season = '2021-22'` の303件はなくなり、既存の `year = 2021 AND season = '2021-22'` 315件と統合されて618件になった。

## 完了判定

- 2021-22の対象試合日は2022年1月〜4月へ補正済み。
- `season = '2021-22' AND year = 2020` は0件。
- 対象303件の `schedule_key` に重複・欠落なし。
- 再取得、JSON比較、dry-run、ローカルDB適用・復旧、live DB再集計の手順と結果を記録済み。

以上によりIssue #10を完了とする。
