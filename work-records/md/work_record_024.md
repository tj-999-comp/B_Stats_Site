# 作業記録 024: Issue #46 欠落B1試合40件のDB Upsert
作成日: 2026-08-24

## 概要

GitHub Issue [#46](https://github.com/tj-999-comp/B_Stats_Site/issues/46)を対象に、Issue [#45](https://github.com/tj-999-comp/B_Stats_Site/issues/45)で取得・統合した欠落B1試合40件をSupabaseへ反映するための入力固定、dry-run、backup・verify・fix・rollback SQLを整備した。live DBへの変更はユーザーが実行し、こちらは適用後の読み取り専用確認を行った。

Issue #46の最新状態を作業記録作成前に確認した時点では、状態はOPEN（REOPENED）、親Issueは#7、依存Issueは#45だった。完了条件は、入力JSON・schedule_key・件数の照合、snake_case変換のdry-run、4本のSQLと実行手順の整備、ユーザーによるlive DB適用、適用後の不足件数確認である。

## 適用した役割

### 実際に担当したRole

- `Data validation`: 40試合の入力選定、変換件数、得点整合性、適用後のキー・値・重複を確認
- `SQL design`: backup、verify、fix、rollbackの4本構成と実行順を設計
- `Data patch preparation`: 入力固定表、既存行バックアップ、`player_id_map`固定、履歴・所属バックアップを生成
- `Documentation`: 再実行手順、検証結果、未実施事項を作業記録へ整理

## 主要な判断

- 40試合を7シーズン単位に分け、`scripts/dev/dry_run_issue46_games.py`で一括dry-runできるようにした。
- `ScheduleKey=1810`は公式ヘッダーにチームIDが無いため、A東京を706、千葉を704としてヘッダー記載順に補完した。Box Scoreやplay_by_playは対象外である。
- SQLは`backup → verify（PRE_FIX）→ fix → verify（POST_FIX）`の順とし、問題時だけ`rollback → verify（ROLLED_BACK）`を実行する。
- `player_id_map`はbackup時点のスナップショットを固定し、fix・verify・rollbackで同じ写像を使う。
- `player_game_stats`は試合日時順に投入し、選手所属履歴の時系列を保つ。入力固定表のNUMERIC精度は現行スキーマに合わせた。
- `verify`は読み取り専用とし、play_by_playは変更しない。

## 最終結果

### 変換・SQL入力結果

| 項目 | 結果 |
|---|---:|
| 対象games | 40件 |
| 対象teams | 27件 |
| 対象game_team_stats | 78件 |
| raw players入力 | 687件 |
| 対象player_game_stats | 917件 |
| 対象シーズン | 7シーズン |
| play_by_play | 0件 |

作成したSQLは次の4本である。

- `supabase/sql/20260824_backup_issue46_missing_b1_games.sql`
- `supabase/sql/20260824_verify_issue46_missing_b1_games.sql`
- `supabase/sql/20260824_fix_issue46_missing_b1_games.sql`
- `supabase/sql/20260824_rollback_fix_issue46_missing_b1_games.sql`

補助ファイルは次のとおりである。

- `supabase/patches/20260824_issue46_missing_b1_games_manifest.csv`
- `scripts/dev/dry_run_issue46_games.py`
- `scripts/dev/generate_issue46_sql.py`

### dry-run結果

7シーズンすべてでdry-runを実行し、次の結果になった。

- `games=40`
- `game_team_stats=78`
- `player_game_stats=917`
- 得点・ショット整合性の不一致0件
- 変換後の欠落・想定外・重複行0件
- `play_by_play=0`

### live DB適用後の読み取り専用確認

ユーザーによるSQL適用後、Supabase PostgRESTから対象テーブルをSELECTし、次を確認した。

- games 40件、teams 27件、game_team_stats 78件、player_game_stats 917件
- 対象schedule_key、game_team_stats主キー、player_game_stats主キーが入力と完全一致
- 欠落・重複なし
- 全対象列の実値照合で意味上の不一致なし
- `ScheduleKey=1810`はhome 706、away 704、67-49、2018-01-01で入力と一致

照合時に`games.setu`の整数／TEXT表現差が32件確認されたが、実値はすべて一致していた。再実行時の誤検知を避けるため、SQL生成器の入力表型をTEXTへ修正し、verify・rollbackの比較でもTEXTへ正規化した。

## 検証

- `.venv311/bin/python -m scripts.dev.dry_run_issue46_games`
- `.venv311/bin/python -m scripts.dev.generate_issue46_sql`
- `.venv311/bin/python -m py_compile scripts/dev/dry_run_issue46_games.py scripts/dev/generate_issue46_sql.py`
- `git diff --check`
- 4本のSQLについて、backup表の作成・参照、verifyの読み取り専用性、主キー、履歴テーブル、`player_id_map`の整合性をreview-agentで確認
- 最終レビュー結果: PASS、P1/P2指摘なし
- live DBへの確認はSELECTのみ。DB変更、rollback、play_by_play更新は実施していない
- 作業記録全体のvalidatorを通すため、既存記録018・020の不足metadataを補完し、記録018のHTMLで検出されたリポジトリ外向きリンクをコード表記へ整理した

## Git・PR

- 作業ブランチ: `agent/issue-46-upsert-missing-b1-games`
- コミット: [`c40c7dd`](https://github.com/tj-999-comp/B_Stats_Site/commit/c40c7dd) `feat: prepare issue 46 missing game upsert patch`、[`ebb0973`](https://github.com/tj-999-comp/B_Stats_Site/commit/ebb0973) `docs: finalize issue 46 work record`
- Draft PR: [#49](https://github.com/tj-999-comp/B_Stats_Site/pull/49) `[DB] 欠落B1試合40件のUpsert SQLを整備`
- mainへの直接Pushは行っていない

## 未完了事項と次アクション

- 作業記録、metadata、HTML、SQL一式のcommit・push・Draft PR作成まで完了した。
- Issue #46へ完了コメントとPR URLを記録する。
- IssueのクローズはPR merge後に行う。

## GitHub Issue状況（2026-08-24時点の現在値）

確認日: 2026-08-24（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは9件だった。

### 親子関係

```text
#7（未完了・親Issue）
├── #8（完了・子Issue）
├── #45（完了・子Issue）
└── #46（未完了・子Issue）
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
| 1 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 2 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 3 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 4 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 5 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 6 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 7 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
| 8 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
| 9 | P3 | [#46](https://github.com/tj-999-comp/B_Stats_Site/issues/46) [DB] 特定済みの欠落B1試合をUpsertする | 未完了 | #7の子Issue。#7完了後 |
