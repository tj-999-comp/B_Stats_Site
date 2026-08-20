# 作業記録 019: Issue #16 live DB・再構築SQL・テーブル定義の整合
作成日: 2026-08-20

## 概要

GitHub Issue [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16)について、live DBの`players`列、canonical rebuild SQL、分割SQL、`docs/table_definition.md`の差異を確認した。

完了条件は、再構築後の`players`スキーマと期待するliveスキーマの一致、nationality関連列の責務の一意化、SQLとテーブル定義の差異解消、差異検出手順の再実行可能化である。

## 適用した役割

### 実際に担当したRole

- `DB/SQL`: live DBの列定義を読み取り専用で確認し、再構築SQLとの契約を照合
- `Documentation`: 現行プロフィール列の責務と、再構築後の差異検出手順を文書化
- `GitHub`: Issueの最新状態を確認し、作業記録・PR・完了コメントの対象を整理

## 主要な判断

- live `players`には`nationality`が存在せず、同列は廃止済みの旧列と判断した。
- `player_slot_category`は選手区分、`league_registered_nationality`はリーグ登録国籍、`birthplace`は出身地として責務を分離する。
- canonical SQLと分割SQLは`nationality`を作成しておらず、現行liveの期待列と一致しているため、live DBへのDDL変更は不要とした。
- 今後の新規再構築や別環境の差異を検出できるよう、期待列・想定外列・廃止済み`nationality`を確認する読み取りSQLを再構築手順へ追加した。

## 最終結果

### live DB確認

2026-08-20にSupabase REST OpenAPIを読み取り、`players`の列を確認した。

- 列数: 12
- `nationality`: 存在しない
- 現行プロフィール列: `player_slot_category`、`league_registered_nationality`、`birthplace`
- その他の列: `player_id`、`player_name_j`、`player_name_e`、`last_seen_team_id`、`last_seen_jersey_number`、`old_player_id`、`entity_type`、`created_at`、`updated_at`

`players`全件監査では、live 1,101行・ユニークID 1,101件を読み取った。監査は読み取り専用で、DBの更新は発生していない。

### 実装・文書変更

- `supabase/rebuild/README.md`
  - `players`プロフィール列の現行契約を追加
  - 期待列との差分、想定外列、廃止済み`nationality`を検出するSQLを追加
  - 再構築完了判定に列契約の確認を追加
- `docs/table_definition.md`
  - 2026-08-20のlive`players`列再確認結果を追記
- `docs/changelog.md`
  - Issue #16の判断と変更内容を追記

## 検証

- live DBを読み取り専用で確認した。
- `supabase/rebuild/01_base_schema.sql`、`05_batch_game_and_players_columns.sql`、`00_rebuild_all.sql`の列契約を確認した。
- `nationality`がrebuild SQLに作成対象として存在しないことを確認した。
- `git diff --check`を実行し、成功した。
- 作業記録MarkdownからHTMLを生成し、filename・Markdown・HTMLの検証を実行する。

## 完了判定

Issue #16の完了条件を満たした。現行live DBと再構築SQLの間に、今回の対象である`nationality`関連のDB変更は不要である。差異が発生した場合に再実行できる確認SQLを`supabase/rebuild/README.md`へ残した。

実装変更は課題専用ブランチ`agent/issue-16-schema-drift`でcommit・pushし、Draft PRを作成する。Issueはユーザーの明示により、PR未mergeの理由とPR URLを完了コメントへ残したうえでクローズする。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは9件だった。

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

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P2 | [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13) [DB] player_slot_category の値を正規化する | 未完了 | #25完了後が適切 |
| 2 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 3 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 4 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 5 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 6 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 7 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 8 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 9 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
