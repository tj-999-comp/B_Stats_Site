# 作業記録 026: 新規作業記録の手動公開要求E2E
作成日: 2026-08-24

## 概要

GitHub Issue [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31)に対応し、`B_Stats_Site`で新しく作成した作業記録1件を、固定commitと対象basenameを指定する手動公開要求workflowから`sandbox-pages`へ送る。

完了条件は、既存最大番号の次を採番し、Markdown・metadata・同名HTMLを揃え、B側のvalidatorとブラウザ確認を通したcommitを公開要求の入力に固定すること、A側の受入workflowとPages公開結果を確認すること、Aのファイルを直接変更しないことである。

## 適用した役割

### 実際に担当したRole

- `E2E validation`: B側の生成・検証結果、固定commit、対象basename、A側workflowの実行結果を照合
- `Release operation`: `workflow_dispatch`による公開要求と公開URLの確認
- `Documentation`: 採番、入力、実行順、未確認事項を作業記録へ整理

## 主要な判断

- 既存ファイルとGit履歴で確認できる最大番号は`025`だったため、欠番の再利用をせず`work_record_026`を採用する。
- 公開対象は`work-records/md/work_record_026.md`、`work-records/metadata/work_record_026.yml`、`work-records/work_record_026.html`の同名3ファイルとする。
- metadataの`project_id`は登録済みの`B_Stats_Site`、`publish`は公開要求対象を示す`true`とする。
- B側で作成したcommitのSHAを`source_commit_sha`へ固定し、`target_basename=work_record_026`として手動workflowを起動する。公開先`sandbox-pages`はcheckout・編集・commit・pushの対象にしない。
- A側の受入結果とPagesの公開URLは、dispatch後のGitHub Actions実行結果で確認する。A側の作業ツリーは変更しない。

## 作成物

- `work-records/md/work_record_026.md`
- `work-records/metadata/work_record_026.yml`
- `work-records/work_record_026.html`

## 実行内容

1. `origin/main`を基準にIssue #31専用ブランチを作成する。
2. 過去最大番号`025`の次としてMarkdownとmetadataを作成する。
3. converterで同名HTMLを生成し、filename、metadata、source safety、HTML再生成を検証する。
4. 1280pxと320pxのChromium表示で横overflow、console error、page error、failed requestを確認する。
5. レビュー済みcommitをBへpushし、その40文字SHAと`work_record_026`を手動公開要求へ渡す。
6. A側の受入workflow、provenance、Pages公開URLを確認し、結果をIssue #31へ記録する。

## 検証

実行結果は、作業記録の作成・変換後に追記する。公開要求はB側の検証がすべて成功したcommitだけを対象にする。

## 最終結果

- 作業ブランチ: `agent/issue-31-manual-publish-e2e`
- 対象basename: `work_record_026`
- A側の公開結果: 公開要求実行後に確認する
- Aのファイル直接変更: 実施しない

## 未完了事項と次アクション

- B側のレビュー、push、手動公開要求、A側の受入・Pages反映結果を確認する。
- Issue #31はA側の公開URLとprovenanceを確認してから完了コメントを記録する。

## GitHub Issue状況（2026-08-24時点の現在値）

確認日: 2026-08-24（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは7件だった。

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
| 5 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 6 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
| 7 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
