# 作業記録 022: 欠落B1試合の子Issue分割と補完候補の確定
作成日: 2026-08-24

## 概要

GitHub Issue [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7)の試合レコード精査で、ローカルデータに存在しない可能性があるB1試合を、スクレイピングとUpsertの2段階へ分割した。

公式クラブページのチーム・シーズン別試合数とローカルJSONの件数を比較し、候補リストとの重複を除いた結果、補完候補は40試合、チーム側候補は78件となった。集計CSV上の残存不足数は0件である。ただし、実際の試合詳細取得とSupabaseへの反映は、この作業記録の時点では実施していない。

## 適用した役割

### 実際に担当したRole

- `Issue planning`: 親Issue #7の残作業をスクレイピングとUpsertの子Issueへ分割
- `Data audit`: 公式件数、ローカル件数、補完候補件数の対応を確認
- `Documentation`: 子Issueの完了条件と依存関係、作業記録を整理

## 主要な判断

- 試合詳細の取得とDB反映を同じIssueに混在させず、#45で取得・検証、#46で変換・Upsertを行う。
- #46は#45の取得成功分を入力とし、schedule_key、シーズン、対戦チーム、件数を確認してから着手する。
- Supabaseのlive DB変更はこの作業記録では実施しない。Upsert時はbackup、verify前、fix、rollback、verify後の順序と、対象・接続先・件数の確認を必要条件とする。
- 既存のB1対象を維持し、B2・B3の試合を今回の補完対象へ混在させない。
- `main`への直接Pushはリポジトリ標準に従って行わず、専用ブランチとDraft PRで受け渡す。

## 最終結果

### 作成した子Issue

- 親Issue [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7)
  - 子Issue [#45](https://github.com/tj-999-comp/B_Stats_Site/issues/45): 特定済みの欠落B1試合をスクレイピングする
  - 子Issue [#46](https://github.com/tj-999-comp/B_Stats_Site/issues/46): 特定済みの欠落B1試合をUpsertする
- 既存の子Issue [#8](https://github.com/tj-999-comp/B_Stats_Site/issues/8)は完了済み。
- #46の着手条件は#45の取得・検証完了である。

### 変更ファイル

- `scraper/data/game_supplement_candidates.csv`
  - 既存候補へ今回の7試合候補を追加
  - 片側チームだけを数える候補は`counted_team_ids`で明示
- `scraper/data/club_season_game_counts.csv`
  - 補完候補数と残存不足数を更新
  - `remaining_team_game_count`の合計は0
- `scripts/dev/scrape_club_season_game_counts.py`
  - 候補のチーム側指定と残存不足数の集計に対応

### 確認結果

| 項目 | 件数 |
|---|---:|
| 補完候補のユニーク試合 | 40 |
| 補完候補のチーム側件数 | 78 |
| 残存チーム側不足数 | 0 |
| 候補で充足した差異行 | 57 |

### Git・PR

- 作業ブランチ: `agent/issue-7-missing-game-child-issues`
- コミット: `76f573b` `docs: record missing B1 game child issues`
- Draft PR: [#47](https://github.com/tj-999-comp/B_Stats_Site/pull/47)
- `main`への直接Pushは行わず、Draft PRで確認可能な状態にした。

## 検証

- `scripts/dev/validate_work_record_filenames.py`を実行し、作業記録の番号・配置を確認した。
- `scripts/dev/validate_work_record_source.py --check-fixtures`を実行し、作業記録の構成を確認した。
- `sync_github_issue_status --check`を実行し、#022のIssue状況がGitHub上のオープンIssue 10件と一致することを確認した。
- スクレイパーのPython構文確認、`git diff --check`を実行した。
- 集計CSVは212行、候補リストは40試合、チーム側候補は78件、残存不足数は0件であることを確認した。
- PRのCIで既存の`work_record_018.html`がMarkdownからの再生成結果と不一致と判定されたため、公式変換結果へ更新して再検証する。

## 未完了事項と次アクション

- #45で公式スケジュールからschedule_keyを確定し、既存JSONとの重複を除いて試合詳細を取得する。
- #46で取得成功分をdry-run変換し、必要なDB変更一式をreview-agentで確認したうえで、ユーザーがlive DBへ適用する。
- Upsert後にチーム・シーズン別件数を再集計し、`club_season_game_counts.csv`と一致することを確認する。

## GitHub Issue状況（2026-08-24時点の現在値）

確認日: 2026-08-24（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは10件だった。

### 親子関係

```text
#7（未完了・親Issue）
├── #8（完了・子Issue）
├── #45（未完了・子Issue）
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
| 9 | P3 | [#45](https://github.com/tj-999-comp/B_Stats_Site/issues/45) [Scraping] 特定済みの欠落B1試合をスクレイピングする | 未完了 | #7の子Issue。#7完了後 |
| 10 | P3 | [#46](https://github.com/tj-999-comp/B_Stats_Site/issues/46) [DB] 特定済みの欠落B1試合をUpsertする | 未完了 | #7の子Issue。#7完了後 |
