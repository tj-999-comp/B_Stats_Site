# 作業記録 018: Issue #13 player_slot_category の正規化準備
作成日: 2026-08-20

## 概要

GitHub Issue [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13)について、`players.player_slot_category`の表記ゆれを解消し、新規投入時にも正規値だけを保存できるようにするための実装とDB適用SQLを準備した。

Issueで確認されていた正規値は`日本人選手`、`外国籍選手`、`帰化選手`とし、NULL/空欄は未確認・未判定として保持する。`日本`は`日本人選手`へ、`帰化選手枠`は`帰化選手`へ変換する。

完了条件に関係するDBの実更新はユーザーが行う運用であり、本作業ではlive DBへの`upsert`、`update`、`delete`を実行していない。Issue 13向けの4種のSQLと投入経路の変更を提案可能な状態にした。

## 適用した役割

### 実際に担当したRole

- `DB/SQL`: 正規値、NULLの意味、CHECK制約、バックアップ・確認・修正・ロールバックSQLの設計
- `Python`: 選手投入経路での`player_slot_category`正規化と未知値の検知
- `Documentation`: 運用ルール、投入フロー、SQL一覧、作業記録の更新

## 主要な判断

- DBへ保存する正規値は`日本人選手`、`外国籍選手`、`帰化選手`の3値とする。
- NULL/空欄は情報未確認・未判定を表すため、正規値へ無理に補完しない。
- 既知の表記ゆれ2種類だけを変換し、未知の非空値は`ValueError`で停止して見逃さない。
- 正規化処理は`upsert_players`へ集約し、選手JSON投入、試合JSONからの選手投入、プロフィール補完の共通経路で適用する。
- DB変更の実行主体はユーザーとする。ClaudeはDB変更SQLを作成・提案するが、Supabaseへの適用、CLI/API/Python経由の自動実行を行わない。
- DB変更SQLは、同じIssue・対象について`backup`、`verify`、`fix`、`rollback`の4種を必ず用意する。

## 最終結果

### 実装変更

- `scripts/db/db.py`
  - `player_slot_category`の正規化関数を追加。
  - NULL/空欄をNULLへ統一。
  - `日本`、`帰化選手枠`を正規値へ変換。
  - 未知の非空値を拒否。
- `supabase/rebuild/00_rebuild_all.sql`
- `supabase/rebuild/05_batch_game_and_players_columns.sql`
  - 既存表記ゆれの事前変換と、3値またはNULLに限定するCHECK制約を追加。
- `docs/flow.md`
  - 正規値とNULLの意味、新規投入時の検知方針を記載。
- `AGENTS.md`
  - DB変更はユーザーが実行し、Claudeは実行しないルールを明文化。

### ユーザーが実行するDB適用SQL

次の順序で、ユーザーが対象接続先を確認して実行する。Claudeはこれらを実行しない。

1. [`20260820_backup_issue13_player_slot_category.sql`](../../supabase/sql/20260820_backup_issue13_player_slot_category.sql)
2. [`20260820_verify_issue13_player_slot_category.sql`](../../supabase/sql/20260820_verify_issue13_player_slot_category.sql)（実行前）
3. [`20260820_fix_issue13_player_slot_category.sql`](../../supabase/sql/20260820_fix_issue13_player_slot_category.sql)
4. [`20260820_verify_issue13_player_slot_category.sql`](../../supabase/sql/20260820_verify_issue13_player_slot_category.sql)（実行後）
5. 問題がある場合のみ[`20260820_rollback_fix_issue13_player_slot_category.sql`](../../supabase/sql/20260820_rollback_fix_issue13_player_slot_category.sql)を実行し、その後に`verify`を再実行する。

バックアップ対象は、実行時点で`日本`または`帰化選手枠`を持つ行である。バックアップSQLは対象件数を固定し、修正SQLはバックアップ件数と更新件数を照合する。検証SQLは正規化状態とCHECK制約の存在を確認する。

## 検証

- Python 3.11で`scripts`と`Colab`の構文確認を実行した。
- 正規化関数について、NULL、空欄、既知の別名、正規値、未知値拒否を確認した。
- `upsert_players`が別名を正規値へ変換することを確認した。
- `git diff --check`を実行した。
- SQL変更に対するreview-agentの読み取り専用レビューを実行し、指摘を修正した。最終レビューは`No findings.`だった。
- live DBへのSQL適用、DB件数の実更新確認は未実施。ユーザー実行後にIssue 13のDB側完了条件を確認する。

## 完了判定

正規値、NULLの意味、新規投入時の検知、既存データ用の4種SQL、ロールバック方針、運用上の実行主体を記録した。実装とSQL提案の準備は完了しているが、live DBの実更新はユーザー実行待ちであるため、Issue 13自体は未完了のまま維持する。

作業ブランチは`agent/issue-13-player-slot-category-normalization`とする。commit・push・Draft PRの情報は作成後に本記録へ追記する。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで`tj-999-comp/B_Stats_Site`のIssue 13、Issue 13のコメント、全オープンIssue、親Issueのsub-issuesを取得した。Issue 13はopenで、コメントは0件だった。Pull Requestは一覧から除外した。

### 親子関係

```text
#7（未完了・親Issue）
└── #8（完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（完了・子Issue）
└── #23（完了・子Issue）
#24（完了・親Issue）
└── #25（完了・子Issue）
```

Issue 13は親子関係の登録がない。Issue 25の完了後に着手する関係として、優先順位一覧へ記載する。

### 優先順位順の未完了一覧

優先度と関係・着手条件は`scripts/dev/github_issue_status_policy.json`の運用設定を使用し、設定のないIssueは既定値P3とした。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P2 | [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13) [DB] player_slot_category の値を正規化する | 未完了 | #25完了後が適切 |
| 2 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 3 | P2 | [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16) [DB] live DB・再構築SQL・テーブル定義のスキーマ差異を解消する | 未完了 | 独立 |
| 4 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 5 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 6 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 7 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 8 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 9 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 10 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
