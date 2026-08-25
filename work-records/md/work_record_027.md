# 作業記録 027: B_Stats_Site mainへのpush確認テスト
作成日: 2026-08-25

## 概要

- 対象: `tj-999-comp/B_Stats_Site` の作業記録027。
- 目的: 作業記録のMarkdown、metadata、対応HTMLを揃え、`B_Stats_Site` の `main` へpushできることを確認する。
- 完了条件: 3ファイルの対応、既存validatorとHTML再生成チェックの合格、`main` へのpush、GitHub上の先端commit確認。

## 主要な判断

- 既存の最大番号が026だったため、次の番号として027を採用する。
- GitHub Issueに紐づく実装課題ではなく、リポジトリのpush経路確認を目的とするテスト記録として作成する。
- 公開対象の作業記録としてmetadataの`publish`を`true`にする。

## 作成物

- `work-records/md/work_record_027.md`
- `work-records/metadata/work_record_027.yml`
- `work-records/work_record_027.html`

## 検証

- MarkdownからHTMLを再生成し、対応HTMLとの差分がないことを確認した。
- 作業記録のファイル名、metadata、HTML対応、source safetyを検証した。
- `git diff --check`を実行した。
- commit後、`B_Stats_Site` の`main`へpushし、GitHub上の先端commitを確認した。

## 最終結果

- 作業記録027のMarkdown、metadata、HTMLを作成した。
- `B_Stats_Site` の`main`へのpush確認テストを完了した。
- 未解決事項: なし。

## GitHub Issue状況（2026-08-25時点の現在値）

確認日: 2026-08-25（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは6件だった。

### 親子関係

```text
#7（未完了・親Issue）
├── #8（完了・子Issue）
├── #45（完了・子Issue）
└── #46（完了・子Issue）
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
| 5 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
| 6 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
