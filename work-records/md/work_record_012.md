# 作業記録 012: Issue #25 player_id統合・プロフィール補完
作成日: 2026-08-20

## 目的

GitHub Issue #25について、Issue #24後のLive DBを再監査し、重複player_idの統合と統合後プロフィール欠損の補完を行う。

## 対象と判断

- 45848〜45865周辺を中心に、同一人物候補18組を調査した。
- 同一人物と判断した18組について、新しい正規IDを優先して統合した。
- 統合後に選手・スタッフ相当を再分類し、補完対象281選手を作成した。
- 公式取得値に加え、確認済みの国籍から出生地を補完した。
- team_id=786の選手は韓国、指定された5選手は帰化選手、残りの手動対象は日本人選手として補完した。
- `player_slot_category` は `日本人選手`、`外国籍選手`、`帰化選手` の3表記へ統一した。既存の非空値は、指定対象を除き保持した。

## 実行結果

- 統合前の選手数1119人から、統合後1101人になった。
- ID統合後の確認で、旧IDのplayers、player_game_stats、名前履歴、所属履歴はすべて0件になった。
- 正規ID側は選手18人、試合成績2392行、名前履歴20行、所属履歴42行になった。
- 正規IDの試合成績に `(schedule_key, player_id)` の重複はなかった。
- プロフィール補完SQLを281人対象で実行した。
- 実行後verify結果は `ISSUE25_PROFILE 281 281 0 281 281` だった。適用後の想定外差分は0件、選手区分の標準表記は281件だった。

## 成果物と実行順

ID統合:

- `supabase/patches/20260819_issue25_player_id_candidates.csv`
- `supabase/sql/20260819_backup_issue25_player_id_merge.sql`
- `supabase/sql/20260819_verify_issue25_player_id_merge.sql`
- `supabase/sql/20260819_fix_issue25_player_id_merge.sql`
- `supabase/sql/20260819_rollback_fix_issue25_player_id_merge.sql`

プロフィール補完:

- `supabase/patches/20260819_issue25_missing_player_profiles.csv`
- `supabase/patches/20260819_issue25_missing_player_profiles_proposed.csv`
- `supabase/patches/20260819_issue25_missing_player_profiles_unresolved.csv`
- `supabase/patches/20260820_issue25_unresolved_player_slot_category.csv`
- `supabase/sql/20260820_backup_issue25_player_profiles.sql`
- `supabase/sql/20260820_verify_issue25_player_profiles.sql`
- `supabase/sql/20260820_fix_issue25_player_profiles.sql`
- `supabase/sql/20260820_rollback_fix_issue25_player_profiles.sql`

SQLの実行順は、ID統合・プロフィール補完ともに `backup → verify（前）→ fix → verify（後）` とした。プロフィール補完のバックアップ表とパッチ表は、ロールバック確認が完了するまで保持する。

## 補完しなかった欠損

補完対象について、国籍・出生地の残存未補完はない。公式値が空欄だった出生地には、確認済みの`league_registered_nationality`を国として採用した。スタッフ相当47人、ダミー1人はプロフィール補完対象から除外した。

## 正本JSONとの整合方針

今回の反映対象はLive DBの`players`であり、`scraper/data/players.json`を自動上書きしていない。プロフィール補完の判断値はCSVに記録し、SQLは既存の非空な国籍・出生地を上書きしない。DB反映後の確認結果はverify SQLの出力で記録した。

## 完了判定

Issue #25の完了条件であるID統合、関連行の重複・欠落確認、目視確認済みプロフィール補完、未補完理由の記録、CSV・SQL・検証結果の保存を完了した。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは15件だった。

### 親子関係

```text
#7（未完了・親Issue）
└── #8（完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（未完了・子Issue）
└── #23（未完了・子Issue）
#24（完了・親Issue）
└── #25（完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P1 | [#22](https://github.com/tj-999-comp/B_Stats_Site/issues/22) [DB] スタッフ相当判定フラグを追加してプロフィール欠損一覧から除外する | 未完了 | #12の子Issue。#25と関連 |
| 2 | P1 | [#23](https://github.com/tj-999-comp/B_Stats_Site/issues/23) [DB] 45848〜45865周辺の分割player_idを調査・統合する | 未完了 | #12の子Issue。#25と関連 |
| 3 | P2 | [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13) [DB] player_slot_category の値を正規化する | 未完了 | #25完了後が適切 |
| 4 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 5 | P2 | [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16) [DB] live DB・再構築SQL・テーブル定義のスキーマ差異を解消する | 未完了 | 独立 |
| 6 | P2 | [#18](https://github.com/tj-999-comp/B_Stats_Site/issues/18) [DB] 空の player_id_map と旧ID名寄せ経路を検証する | 未完了 | #23と関連 |
| 7 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 8 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 9 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 10 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 11 | P3 | [#28](https://github.com/tj-999-comp/B_Stats_Site/issues/28) [Work records] 親ディレクトリREADMEリンクをproject内リンクへ修正する | 未完了 | 独立。優先度未設定 |
| 12 | P3 | [#29](https://github.com/tj-999-comp/B_Stats_Site/issues/29) [Work records] 001〜010のmetadataと生成元validator・CIを追加する | 未完了 | 独立。優先度未設定 |
| 13 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 14 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 15 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
