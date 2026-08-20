# 作業記録 016: Issue #23 分割player_idの調査・統合
作成日: 2026-08-20

## 概要

Issue #23の対象である`player_id` 45848〜45865について、同一人物候補を正規IDへ統合し、正本JSONに残っていた正規IDの重複行を整理した。

## 対象と判断

- 対象は旧ID 18件（45848〜45865）と、それぞれの統合先候補18件。
- `player_name_j`、`player_name_e`、所属チーム、背番号、試合出場履歴を照合した。
- 18件すべてを同一人物と判断し、`510000...`系の正規IDを残す方針とした。
- 旧IDは独立した`player_id`として残さず、`old_player_id`と`player_id_map`で対応関係を保持する。
- 正本JSONでは、同じ正規IDが2行存在する14人について、`old_player_id`が設定されている統合後の行を残し、古い所属・更新情報を持つ行を削除した。

## 統合対応表

対応表は`supabase/patches/20260819_issue25_player_id_candidates.csv`に保存した。対象18件のうち、正本JSONで重複していた14件は次のとおりである。

| 旧ID | 正規ID | 選手名 | 削除した重複行の特徴 |
|---:|---:|---|---|
| 45848 | 5100000069 | レイ・パークスジュニア | 所属729、`old_player_id`なし |
| 45849 | 51000259 | カイ・ソット | 所属721、`old_player_id`なし |
| 45851 | 5100000062 | キーファー・ラベナ | 所属698、`old_player_id`なし |
| 45852 | 51000102 | ドワイト・ラモス | 所属702、`old_player_id`なし |
| 45853 | 51000185 | グレゴリー・スローター | 所属53000064、`old_player_id`なし |
| 45855 | 51000260 | カール・タマヨ | 所属701、`old_player_id`なし |
| 45857 | 51000314 | イ デソン | 所属728、`old_player_id`なし |
| 45859 | 51000187 | マシュー・ライト | 所属699、`old_player_id`なし |
| 45860 | 51000308 | ロン･ジェイ･アバリエントス | 所属716、背番号0、`old_player_id`なし |
| 45861 | 5100000041 | 王 偉嘉 | 所属693、背番号1、`old_player_id`なし |
| 45862 | 5100000012 | 荒谷 裕秀 | 所属703、`old_player_id`なし |
| 45863 | 51000137 | 上田 隼輔 | 所属696、`old_player_id`なし |
| 45864 | 51000113 | 飯尾 文哉 | 所属700、`old_player_id`なし |
| 45865 | 5100000024 | キング 開 | 所属694、`old_player_id`なし |

チュアンシン・リュウ、チャン ミンクク、シェンゼ・リー、劉 駿霆の4人は、正本JSON内に重複行がなかった。

## DB統合の成果物と結果

DB統合はIssue #25の作業で実施した。対象テーブルは`players`、`player_game_stats`、`player_name_history`、`player_affiliations`、`player_id_map`である。

- 旧ID側の`players`行、試合成績、名前履歴、所属履歴を正規IDへ整理した。
- 旧IDから正規IDへの対応を`player_id_map`へ登録した。
- 旧IDの残存は0件、正規ID側は18件となった。
- 正規ID側の試合成績は2,392行で、`(schedule_key, player_id)`の重複はなかった。
- 変更前の対象行をバックアップし、verifyとロールバックSQLを用意した。

成果物:

- `supabase/sql/20260819_backup_issue25_player_id_merge.sql`
- `supabase/sql/20260819_verify_issue25_player_id_merge.sql`
- `supabase/sql/20260819_fix_issue25_player_id_merge.sql`
- `supabase/sql/20260819_rollback_fix_issue25_player_id_merge.sql`

## 正本JSONの整理結果

対象JSONは`scraper/data/players.json`である。JSONをDBへ再投入したり、プロフィール値を新たに補完したりせず、対象の重複行だけを削除した。

- 変更前: 713行
- 変更後: 699行
- 削除: 14行
- 対象18正規ID: すべて1行ずつ
- 対象旧ID 45848〜45865の独立行: なし
- 対象外の重複ID: 6件を残した（Issue #23の対象外）
- 対象外データの変更: なし

旧IDとの対応関係は、正規行の`old_player_id`とDBの`player_id_map`に保持する。正本JSONには旧IDを独立選手として再投入しない。

## 検証

- `players.json`をPythonで読み込み、JSON構文を確認した。
- 対象18正規IDの重複が0件であることを確認した。
- 対象18正規IDの欠落が0件であることを確認した。
- 対象外IDの行内容が変更されていないことを確認した。
- `git diff --check`が成功した。
- live DBの統合後検証結果はIssue #25の作業記録とverify SQLに記録されている。

## 完了判定

Issue #23の完了条件を満たした。対象18件の正規ID、統合根拠、関連テーブルのバックアップ・ロールバック、試合成績の重複確認、正本JSONのID収束結果を記録した。追加のDB変更は不要である。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは12件だった。

### 親子関係

```text
#7（未完了・親Issue）
└── #8（完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（完了・子Issue）
└── #23（未完了・子Issue）
#24（完了・親Issue）
└── #25（完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P1 | [#23](https://github.com/tj-999-comp/B_Stats_Site/issues/23) [DB] 45848〜45865周辺の分割player_idを調査・統合する | 未完了 | #12の子Issue。#25と関連 |
| 2 | P2 | [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13) [DB] player_slot_category の値を正規化する | 未完了 | #25完了後が適切 |
| 3 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 4 | P2 | [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16) [DB] live DB・再構築SQL・テーブル定義のスキーマ差異を解消する | 未完了 | 独立 |
| 5 | P2 | [#18](https://github.com/tj-999-comp/B_Stats_Site/issues/18) [DB] 空の player_id_map と旧ID名寄せ経路を検証する | 未完了 | #23と関連 |
| 6 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 7 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 8 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 9 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 10 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 11 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 12 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
