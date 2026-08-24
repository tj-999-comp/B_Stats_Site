# 作業記録 024: 固定commitの手動公開要求workflowとdispatch権限
作成日: 2026-08-24

## 概要

GitHub Issue [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30)に対応し、`B_Stats_Site`から公開リポジトリ`sandbox-pages`へ、安全に手動公開要求を送るGitHub Actions workflowを追加した。

公開要求は`workflow_dispatch`だけで開始し、利用者が指定した40文字のcommit SHAをcheckoutして検証する。生成元のfilename、metadata、HTML再生成、安全性validatorを通過し、対象metadataが`publish: true`である場合だけ、`project_id`、`source_commit_sha`、`target_basename`の3入力を公開先workflowへ送る。

## 適用した役割

### 実際に担当したRole

- `Workflow design`: 固定SHA検証と公開先dispatchの権限境界を設計
- `Security review`: Fine-grained PATの限定権限、Secret非出力、公開先非変更を確認
- `Validation`: 選択対象のmetadataと既存validator・converter checkをworkflowへ接続
- `Documentation`: Secretの期限、rotation、失効手順と手動実行方法を記録

## 主要な判断

- workflowは`workflow_dispatch`だけとし、`push` triggerは追加しない。main更新時の自動公開は後続Issue #32の対象とする。
- `actions/checkout`は入力SHAを`ref`へ渡し、checkout後に`HEAD`と同一であることを再確認する。ブランチ名や最新mainへ解決し直さない。
- 公開先のcheckout、編集、commit、pushは行わず、`gh api`で`sandbox-pages`の`accept-source.yml`をdispatchするだけにする。
- `SANDBOX_PAGES_DISPATCH_TOKEN`はdispatch jobにだけ渡し、Fine-grained PATの対象repositoryを`sandbox-pages`だけ、権限をActionsのRead and writeだけに限定する。Contents writeは付与しない。
- `publish: true`、固定`project_id`、同名Markdown・metadata・HTMLを送信直前に確認する。選択対象以外のファイル内容やtokenをartifactへ保存しない。

## 実装

### 変更内容

- `.github/workflows/request-publish.yml`
  - 固定SHAと対象basenameを入力する手動workflowを追加
  - checkout SHA、既存validator、converter check、selected metadataを検証
  - 検証成功後に`sandbox-pages`の`accept-source.yml`へ3入力だけをdispatch
- `scripts/dev/validate_publish_request.py`
  - basename、対象3ファイル、`project_id`、`publish: true`を検査する標準ライブラリCLIを追加
- `docs/workflows.md`, `docs/deployment.md`
  - 手動公開要求、Secretの権限、期限・rotation・失効手順を追記
- `work-records/metadata/work_record_018.yml`, `work-records/metadata/work_record_020.yml`
  - 既存番号付き作業記録の欠落metadataを補完し、source validatorの全体検証対象を揃えた
- `work-records/md/work_record_018.md`
  - 公開先でリポジトリ外参照になるSQL相対リンクをコード表記へ変更した

### 公開要求の境界

```text
workflow_dispatch
  -> fixed SHA checkout
  -> filename / converter / source safety / publish metadata validation
  -> sandbox-pages accept-source.yml dispatch
       inputs: project_id, source_commit_sha, target_basename
```

公開先側の受入、provenance、Pages反映は`sandbox-pages`が担当し、このrepositoryのworkflowは公開先の状態を変更しない。

## 検証

- `python scripts/dev/validate_publish_request.py --target-basename work_record_023`
- `python scripts/dev/validate_work_record_filenames.py`
- `python -m scripts.dev.convert_work_records_to_html --check`
- `python scripts/dev/validate_work_record_source.py`
- `python scripts/dev/validate_work_record_source.py --check-fixtures`
- `git diff --check`
- workflow YAMLのtrigger、permissions、Secret参照、dispatch入力を静的確認

実際の公開要求dispatchとPATの設定は、秘密情報と外部workflowの状態を伴うためこの作業では実行しない。手動E2EはIssue #31で扱う。

## 最終結果

- 作業ブランチ: `agent/issue-30-manual-publish-dispatch`
- 実装commit: 実装後に追記
- Draft PR: 実装後に追記
- Issue #30: workflow・Secret運用・安全境界の実装を完了し、PRレビュー待ち
- 未解決事項: `SANDBOX_PAGES_DISPATCH_TOKEN`の実PAT登録と手動公開E2Eは未実施

## GitHub Issue状況（2026-08-24時点の現在値）

確認日: 2026-08-24（JST）

GitHub APIで取得した`tj-999-comp/B_Stats_Site`のIssueを確認した。Pull Requestは対象外とした。Issue #30の最新状態はOPEN（2026-08-18 15:42:41 JST更新）である。Issue状況同期スクリプトはsub-issues APIへの接続が一時的に失敗したため、取得できたIssue一覧と直前のsub-issues確認結果をもとに記録し、API復旧後に`--check`で再確認する。

### 親子関係

```text
#7（未完了・親Issue）
├── #45（完了・子Issue）
└── #46（完了・子Issue）
```

GitHubのsub-issues APIで確認済みの親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は`github_issue_status_policy.json`の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 2 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 3 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立。優先度未設定 |
| 4 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立。優先度未設定 |
| 5 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 6 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 7 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
| 8 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
