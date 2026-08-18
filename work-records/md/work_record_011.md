# 作業記録 011: Issue #24 試合データ取得・Live DB投入
作成日: 2026-08-18

## 目的

GitHub Issue #24の対象である、2026-05-31（JST）までの未投入試合データを取得し、Live DBへ投入する。

## 対象と入力

- 2025-05-18の未取得試合: `schedule_key=503896`
- 2025-26シーズン: 2025年10月〜2026年5月の月次JSON 8ファイル
- 保存先: `scraper/data/season_2025-2026/`
- `play_by_play` は取得・投入しない。

## 実行結果

- `schedule_key=503896` を再取得し、2024-25年5月JSONへ反映した。
- 2025-26シーズンの10月、11月、12月、2026年1月、2月、3月、4月、5月を月順に取得した。
- ユーザー環境のPython 3.11仮想環境で、古い月から順にLive DBへUPSERTした。
- GitHub Issue #24へ実施結果をコメントした。

## 実行上の問題と対応

Codexの既定サンドボックスでは外部ネットワークが無効だったため、B.LEAGUEのスケジュールAPIでDNS解決に失敗した。スクレイパーはこの失敗を空のスケジュールとして扱い、`game_count=0` のJSONを保存していた。

空JSONをUPSERTしても更新件数が0件になることを確認した後、ユーザーのネットワーク接続可能なローカル環境で再取得し、その結果をLive DBへ投入した。

## 残件

- Live DB上で、試合・チーム・選手試合成績・チーム試合成績の件数、抜け漏れ、重複、参照整合性を確認する。
- Issue #24の確認結果を踏まえ、子Issue #25（player_id重複整理・プロフィール欠損補完）へ引き継ぐ。

## 関連ファイル

- `scraper/data/season_2024-2025/games_2024-25_2025-05-01_2025-05-31.json`
- `scraper/data/season_2025-2026/`
- `scraper/logs/game_detail_fetch_log.json`
- `scraper/logs/schedule_fetch_log.json`
- `scripts/dev/sync_github_issue_status.py`
- `scripts/dev/github_issue_status_policy.json`
- `.github/workflows/validate-work-record-filenames.yml`

## GitHub Issue状況（2026-08-18時点の現在値）

確認日: 2026-08-18（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは17件だった。

### 親子関係

```text
#7（未完了・親Issue）
└── #8（完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（未完了・子Issue）
└── #23（未完了・子Issue）
#24（未完了・親Issue）
└── #25（未完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P0 | [#24](https://github.com/tj-999-comp/B_Stats_Site/issues/24) [DB] 2026年5月末までの未投入試合データをスクレイピング・投入する | 未完了 | 親Issue。#25をブロック |
| 2 | P1 | [#22](https://github.com/tj-999-comp/B_Stats_Site/issues/22) [DB] スタッフ相当判定フラグを追加してプロフィール欠損一覧から除外する | 未完了 | #12の子Issue。#25と関連 |
| 3 | P1 | [#23](https://github.com/tj-999-comp/B_Stats_Site/issues/23) [DB] 45848〜45865周辺の分割player_idを調査・統合する | 未完了 | #12の子Issue。#25と関連 |
| 4 | P1 | [#25](https://github.com/tj-999-comp/B_Stats_Site/issues/25) [DB] 試合データ投入後のplayer_id重複整理とプロフィール欠損補完 | 未完了 | #24の子Issue。#24完了後 |
| 5 | P2 | [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13) [DB] player_slot_category の値を正規化する | 未完了 | #25完了後が適切 |
| 6 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 7 | P2 | [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16) [DB] live DB・再構築SQL・テーブル定義のスキーマ差異を解消する | 未完了 | 独立 |
| 8 | P2 | [#18](https://github.com/tj-999-comp/B_Stats_Site/issues/18) [DB] 空の player_id_map と旧ID名寄せ経路を検証する | 未完了 | #23と関連 |
| 9 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 10 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 11 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 12 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 13 | P3 | [#28](https://github.com/tj-999-comp/B_Stats_Site/issues/28) [Work records] 親ディレクトリREADMEリンクをproject内リンクへ修正する | 未完了 | 独立。優先度未設定 |
| 14 | P3 | [#29](https://github.com/tj-999-comp/B_Stats_Site/issues/29) [Work records] 001〜010のmetadataと生成元validator・CIを追加する | 未完了 | 独立。優先度未設定 |
| 15 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 16 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 17 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
