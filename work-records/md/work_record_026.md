# 作業記録 026: 新規作業記録の手動公開要求E2E
作成日: 2026-08-24

## 概要

GitHub Issue [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31)に対応し、`B_Stats_Site`で新しく作成した作業記録1件を、固定commitと対象basenameを指定する手動公開要求workflowから`sandbox-pages`へ送る。

完了条件は、既存最大番号の次を採番し、Markdown・metadata・同名HTMLを揃え、B側のvalidatorとブラウザ確認を通したcommitを公開要求の入力に固定すること、A側の受入workflowとPages公開結果を確認すること、Aのファイルを直接変更しないことである。初回のA側applyは未追跡`__pycache__`で停止したが、A側workflow修正後に同じ固定入力で再実行し、provenance更新とPages公開まで確認した。

## 適用した役割

### 実際に担当したRole

- `E2E validation`: B側の生成・検証結果、固定commit、対象basename、A側workflowの実行結果を照合
- `Release operation`: `workflow_dispatch`による公開要求とA側受入workflowの実行結果を確認
- `Documentation`: 採番、入力、実行順、失敗原因、次セッションの再実行条件を作業記録へ整理

## 主要な判断

- 既存ファイルとGit履歴で確認できる最大番号は`025`だったため、欠番の再利用をせず`work_record_026`を採用する。
- 公開対象は`work-records/md/work_record_026.md`、`work-records/metadata/work_record_026.yml`、`work-records/work_record_026.html`の同名3ファイルとする。
- metadataの`project_id`は登録済みの`B_Stats_Site`、`publish`は公開要求対象を示す`true`とする。
- B側のmerge commit `8210edbcd271089d6942ce44371a90261bcfc0a0`を`source_commit_sha`へ固定し、`target_basename=work_record_026`として手動workflowを起動した。公開先`sandbox-pages`はcheckout・編集・commit・pushの対象にしない。
- A側のdry-run受入が成功した後、初回applyで停止した。失敗原因はA側workflowのPython実行で生成された未追跡`__pycache__/*.pyc`が、apply前の`Repository A worktree must be clean`チェックに残ったことである。
- A側の修正commit `b9c7a4d27ed4597a55de6f6a6e2400b30b64ef5e`でapply時の`PYTHONDONTWRITEBYTECODE=1`を設定し、A側のファイルを直接編集せずに再実行した。
- 公開先への適用・provenance更新・Pages公開は、`sandbox-pages`のworkflowが行った。B側からA側のファイルを直接変更していない。

## 作成物

- `work-records/md/work_record_026.md`
- `work-records/metadata/work_record_026.yml`
- `work-records/work_record_026.html`

## 実行内容

1. `origin/main`を基準にIssue #31専用ブランチを作成した。
2. 過去最大番号`025`の次としてMarkdownとmetadataを作成した。
3. converterで同名HTMLを生成し、filename、metadata、source safety、HTML再生成を検証した。
4. 1280px、900px、640px、320pxのChromium表示で横overflow、console error、page error、failed requestを確認した。
5. commit `b476f4688a1463e51bd98aeb4b4139af211fbd21`を作成し、PR #51をmergeした。main上のmerge commit `8210edbcd271089d6942ce44371a90261bcfc0a0`を固定してB側publish要求を起動した。
6. B側workflow attempt 2とA側workflowを確認した。初回A側applyは未追跡`__pycache__`で停止した。
7. A側修正後、同じ`source_commit_sha=8210edbcd271089d6942ce44371a90261bcfc0a0`と`target_basename=work_record_026`で再実行した。A側dry-run・apply、Pages build/deploy、公開物を確認した。

## 検証

### B側の事前検証

- filename、metadata、source safety、fixture、HTML regeneration check: 成功
- `work_record_026`のpublish request validation: 成功
- `git diff --check`: 成功
- Chromium 1280/900/640/320px: 横overflow 0、console error 0、page error 0、failed request 0

### 実行結果

- B側workflow run [32712590804](https://github.com/tj-999-comp/B_Stats_Site/actions/runs/32712590804)のattempt 2: 固定SHA checkout、全validator、A側dispatchが成功
- 初回A側workflow run [32714174339](https://github.com/tj-999-comp/sandbox-pages/actions/runs/32714174339): dry-runは成功、applyは`__pycache__`で停止
- 修正後A側workflow run [32715367822](https://github.com/tj-999-comp/sandbox-pages/actions/runs/32715367822): dry-run・applyが成功し、固定commit `c88a5cc77fb46a15546554d3bbcf539f3f8862b`を生成
- A側Pages build/deploy run [32715402294](https://github.com/tj-999-comp/sandbox-pages/actions/runs/32715402294): build・deployとも成功
- 公開先のprovenanceに`source.commit_sha=8210edbcd271089d6942ce44371a90261bcfc0a0`、対象`work_record_026`、公開URLを確認
- 親の受入runは最終conclusionが`failure`だが、dry-run/applyと呼び出し先Pages deployは成功し、失敗ログは出力されなかった。公開成果物とPages状態は独立に確認済み

## 最終結果

- 作業ブランチ: `agent/issue-31-manual-publish-e2e`（初回）、`agent/issue-31-work-record-followup`（本追記）
- 対象basename: `work_record_026`
- B側publish要求: 成功
- A側dry-run受入: 成功
- A側Pages公開結果: 完了。`https://tj-999-comp.github.io/sandbox-pages/projects/B_Stats_Site/work_record_026.html`
- A側provenance: 完了。公開対象、source commit、metadata、HTMLの記録を確認
- Aのファイル直接変更: 実施しない

## 未完了事項と次アクション

初回失敗からの再実行、公開先commit・provenance更新、Pages build/deploy、公開URL確認まで完了した。残る作業は、この最終結果を記録した変更をB側へ反映し、Issue #31へ完了コメントを残すことである。

## 最終追記（2026-08-25）

`sandbox-pages`の現在mainとGitHub Actionsを再確認した。A側workflowの修正commit後の受入runでは、`work_record_026`が`c88a5cc77fb46a15546554d3bbcf539f3f8862b`として反映され、provenanceに固定source commitと公開対象が保存されている。Pagesの公開状態は`built`で、対象HTMLを公開URLから確認できる。これによりIssue #31のE2E完了条件を満たした。

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
