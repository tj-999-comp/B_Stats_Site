# 作業記録 020: Issue #14 attendance欠損14試合の調査
作成日: 2026-08-20

## 概要

GitHub Issue [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14)について、`games.attendance` がNULLの14試合を調査した。

完了条件は、14試合すべてのNULL理由または正しい観客数を確定し、補完可能な行を反映し、0とNULLの意味を文書化することである。

## 適用した役割

### 実際に担当したRole

- `Data audit`: 正本JSONと取得ログを対象キー単位で照合
- `Official source verification`: B.LEAGUE公式試合詳細ページと公式発表を確認
- `Documentation`: `games.attendance` の0/NULL判定基準と調査結果を記録

## 主要な判断

- `0`は、公式に当該試合が無観客と確認できる場合だけ使う。
- 公式に観客数が掲載されていない場合は、推測で0にせずNULLを維持する。
- イベント全体、開催日全体、アリーナ延べ人数は個別試合のattendanceへ流用しない。
- 対象14件は、試合データの取得漏れ・中止ではなく、公式の個別試合観客数未掲載と判定した。

## 最終結果

### 対象14件

`docs/attendance_policy.md` に、対象キー、試合日、対戦、正本JSON、公式詳細URL、人数の扱いを一覧化した。

14件すべてで次を確認した。

- 正本JSONに試合データが存在し、`error`はない。
- `source_tab`は`4`である。
- 正本JSONの`Game.Attendance`は`null`である。
- 公式詳細ページの`Game.Attendance`も`null`で、人数表示欄は空である。
- `scraper/logs/game_detail_fetch_log.json`の失敗一覧に対象キーはない。
- 得点と試合終了フラグが存在し、試合自体は成立している。

2023年水戸大会の3,146名、2024年沖縄大会のDAY2 6,379名・DAY3 7,357名は、公式発表上もイベントまたは開催日単位の人数であるため、対象ゲームへ割り当てなかった。

### 変更ファイル

- `docs/attendance_policy.md`
  - `games.attendance` の値の意味を定義
  - 14試合の調査結果と公式根拠を記録
- `work-records/md/work_record_020.md`
  - Issue #14の作業記録
- `work-records/work_record_020.html`
  - Markdownから生成する作業記録HTML

### DB・正本JSONへの適用

補完可能な個別試合の人数は確認できなかったため、DB更新、正本JSON変更、SQL作成は行わない。14件の`NULL`は公式未掲載を表す値として維持する。

## 検証

- 14件の正本JSONを対象キーで走査し、`game`存在、`error`、`source_tab`、`Attendance`を確認した。
- `game_detail_fetch_log.json`の全61 runについて、対象キーが失敗一覧にないことを確認した。
- 公式試合詳細ページ14件を読み取り専用で取得し、`Game.Attendance`がNULLであることを確認した。
- 公式発表で確認できたイベント単位の人数を個別試合へ流用しないことを確認した。
- DB変更操作は実行していない。
- `git diff --check`、作業記録ファイル名検証、MarkdownからHTML生成後のHTML検証を実施する。

## 完了判定

Issue #14の14件はすべて、取得漏れではなく公式個別試合人数未掲載として理由を確定した。0とNULLの意味を文書化し、補完可能な行がないためDBと正本JSONへの変更は不要と判断した。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは8件だった。

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
| 1 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 2 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 3 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 4 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 5 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 6 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 7 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 8 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
