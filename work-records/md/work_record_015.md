# 作業記録 015: Issue #22 スタッフ相当判定とプロフィール監査除外
作成日: 2026-08-20

## 概要

Issue #22に対応し、`players` の選手・スタッフ相当分類を `entity_type` として保存できるようにした。分類結果をプロフィール欠損監査へ連携し、スタッフ相当とダミーを補完対象から除外できることをlive DBで確認した。

## 目的

`PeriodCategory == 18` に混在するスタッフ相当行が、選手プロフィール欠損一覧へ再び含まれないようにする。ダミーID、スタッフ相当、追跡済み試合に未出現のIDは別分類として扱い、判定根拠を再生成できる状態を残す。

## 実施事項

- `players.entity_type` を追加し、`player`、`staff`、`placeholder`、`unresolved` の4分類を許可した。
- `supabase/rebuild/00_rebuild_all.sql`、`01_base_schema.sql`、`05_batch_game_and_players_columns.sql` を同期した。
- `scripts/dev/classify_player_entities.py` に `entities[].entity_type` を追加した。
- `scripts/dev/fill_missing_player_profile_fields.py` で `staff` と `placeholder` を除外し、`unresolved` は保持するようにした。
- `scripts/dev/apply_player_entity_types.py` を追加し、既定は監査、`--apply` 指定時だけDBへ反映するようにした。
- `scripts/dev/upsert_players_json.py` で `entity_type` を保持できるようにした。
- `docs/flow.md` と `supabase/rebuild/README.md` に実行順、検証方法、ベンチテクニカルの扱いを追記した。

## live DBの反映結果

分類レポートと統合確認SQLにより、`players` 1,101件を次のとおり確認した。

| entity_type | 件数 |
|---|---:|
| `player` | 1,049 |
| `staff` | 47 |
| `placeholder` | 1 |
| `unresolved` | 4 |

NULL、不正な分類値、重複 `player_id`、孤立した `player_game_stats` は0件だった。スタッフ相当47件、ダミー1件、未解決4件を選手1,049件と区別できている。

## ベンチテクニカルの扱い

ベンチテクニカルは選手マスタの `entity_type` へ混ぜない。公式記録上の責任者と実際の行為者が異なり得るため、将来扱う場合は試合イベントとして、チーム、テクニカル種別、公式記録上の責任者、行為者を分離して保存する。

## 検証

- live `players` スナップショット取得が成功した。
- 82個のゲームJSONから `PeriodCategory == 18` の149,375行を走査した。
- 選手相当145,315行、スタッフ相当4,060行を確認した。
- Python 3.11で関連スクリプトの構文確認が成功した。
- `git diff --check` が成功した。
- SQL変更をreview-agentで再レビューし、指摘なしだった。
- `entity_type` 列、`NOT NULL`、CHECK制約、分類件数、参照整合性を統合SQLで確認した。
- GitHub Issue #22へ結果をコメントし、2026-08-20にクローズした。

## 完了判定

Issue #22の完了条件を満たした。全 `players` IDについて分類を再生成でき、Issue #12で確認したスタッフ相当47 ID、ダミーID、未解決IDを区別して保持できる。欠損プロフィール監査ではスタッフ相当とダミーを自動除外できる。

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
