# 作業記録 017: Issue #18 player_id_mapと旧ID名寄せ経路の検証
作成日: 2026-08-20

## 概要

GitHub Issue [#18](https://github.com/tj-999-comp/B_Stats_Site/issues/18)について、2026-08-04のlive DB監査で0行だった`player_id_map`の状態を再確認し、旧ID名寄せのデータフロー、Issue #23・#25で実施したID統合、再投入時の分裂防止を検証した。

完了条件は、旧ID名寄せの正しいデータフローを説明できること、旧ID側の未統合・成績衝突がないこと、`player_id_map`が空だった理由を確定すること、再投入時の安全な検証手順が残ることである。

## 適用した役割

### 実際に担当したRole

- `DB/SQL`: live DBの読み取り検証と既存の統合結果の確認
- `Python`: `player_id_map`取得処理の失敗時挙動の修正
- `Documentation`: 再投入・dry-run・live確認手順の文書化

## 主要な判断

- 2026-08-04時点の`player_id_map` 0行は、旧ID名寄せが不要という仕様ではなく、Issue #23・#25の統合前の状態だったと判断した。
- Issue #25の統合により、45848〜45865の18件は正規IDへ収束し、live DBの`player_id_map`に対応関係を保持する方針を採用した。
- `player_id_map`取得時のDB接続・権限・テーブルエラーを空マップとして扱うと、旧IDが未変換のまま再投入されるため、取得失敗は処理停止とする。
- `--dry-run`はDBから`player_id_map`を取得しない既存仕様を維持し、本番投入時の名寄せ検証はlive DBの読み取り確認と投入後の重複確認で行う。

## 最終結果

### live DB確認

- `player_id_map`は18行だった。
- 45848〜45865の18件すべてに正規IDの対応があった。
- 旧IDの`players`行は0件だった。
- 正規ID側の選手行は18件で、全件に対応する`old_player_id`が設定されていた。
- 旧IDを持つ試合成績は0件だった。
- 既存の正規ID側との試合成績衝突は0件だった。

### 実装・文書変更

- `scripts/db/db.py`の`fetch_player_id_map()`から広範な例外握りつぶしを削除した。
- マッピング行の旧ID・正規ID欠損と、同一旧IDの異なる対応先をエラーにした。
- `docs/flow.md`へ通常投入時の取得失敗時挙動、dry-runの制約、live確認SQLを追記した。

変更ファイル:

- `scripts/db/db.py`
- `docs/flow.md`
- `AGENTS.md`
- `README.md`
- `docs/PORTFOLIO_STANDARD.md`
- `work-records/md/work_record_017.md`
- `work-records/metadata/work_record_017.yml`
- `work-records/work_record_017.html`

## 検証

- live DBを読み取り専用で確認した。
- `player_id_map`の18件、旧ID選手行0件、正規ID18件を確認した。
- 旧ID側の試合成績0件、試合成績衝突0件を確認した。
- `fetch_player_id_map()`の空マップ、正常な1件、不正行、競合行に対する簡易動作チェックを実行した。
- `py_compile`を実行した。
- `git diff --check`を実行した。
- 作業記録のMarkdown・HTML・metadataをvalidatorで確認する。

## 完了判定

Issue #18の完了条件を満たした。live DBの統合状態、旧ID名寄せの経路、取得失敗時の停止挙動、再投入前に実施する確認手順を記録した。

実装変更は課題専用ブランチ`agent/issue-18-player-id-map-validation`でcommit・pushし、commit `4c57dc3`としてDraft PR [#39](https://github.com/tj-999-comp/B_Stats_Site/pull/39)を作成した。Issueはユーザーの明示により、PR未mergeのためその理由とPR URLを完了コメントへ残したうえでクローズする。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは11件だった。

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
| 3 | P2 | [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16) [DB] live DB・再構築SQL・テーブル定義のスキーマ差異を解消する | 未完了 | 独立 |
| 4 | P2 | [#18](https://github.com/tj-999-comp/B_Stats_Site/issues/18) [DB] 空の player_id_map と旧ID名寄せ経路を検証する | 未完了 | #23と関連 |
| 5 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 6 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 7 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 8 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 9 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 10 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 11 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
