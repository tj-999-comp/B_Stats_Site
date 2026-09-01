# 作業記録の運用ルール
作成日: 2026-08-13

## 呼称

- `Issue` はGitHub Issueだけを指す。
- リポジトリ内に保存する調査、実行結果、判断経緯は `作業記録` と呼ぶ。
- `ローカルIssue`、`ローカル Issue`、`Issueログ` という呼称は使わない。

## ディレクトリ構成

```text
work-records/
├── README.md                 # 作業記録の運用ルール
├── design.md                 # HTMLのデザイン原則
├── metadata/
│   └── work_record_###.yml    # 公開用metadata
└── md/
    ├── work_record_001.md    # 番号付き作業記録
    ├── phase_1_tasks.md      # 補助Markdown
    └── scraping_db_automation.md
```

- HTMLはサブディレクトリを作らず、`work-records/` 直下へ置く。
- `work-records/` 直下のMarkdownは `README.md` と `design.md` だけとする。
- 作業記録と補助Markdownは `work-records/md/` に置く。
- HTMLは生成元リポジトリで管理・生成しない。番号付きMarkdownとmetadataを
  sandbox-pagesへ固定SHAで渡し、A側の `a_rendered` rendererが共通HTMLとCSSを生成する。
- 既存のHTML、CSS、design、補助資料は移行期間の履歴として残るが、公開要求の入力・検証対象外とする。
- 番号付き作業記録には、同じベース名の `metadata/work_record_###.yml` を置く。
- metadataは `schema_version`、`title`、`date`、`project_id`、`tags`、`publish` を持つ。
- 現在の `project_id` は `B_Stats_Site` とし、公開対象範囲は001〜014である。

## 公開候補commitの確認

このリポジトリのvalidatorとCIは、公開要求を出せる状態かを確認するものであり、公開承認そのものではない。公開候補commitは、次のいずれかを満たしてから公開要求の対象にする。

1. 対象branchの保護設定で、必要なreviewと `Validate Work Record Filenames` checkの成功を必須にする。
2. branch protectionを設定しない場合は、作成者とは別の人がmetadata、公開要求、CI結果、差分を確認した記録を残す。

公開先の受入workflowやPagesへの反映をこのリポジトリのCIが直接行うことはない。公開要求workflowを追加する場合も、まずこの確認を通過したcommit SHAを固定して扱う。

HTMLはsandbox-pagesのA側rendererが生成するため、このリポジトリではHTMLの生成・再生成を行わない。

## 作業記録の命名規則

- 作業記録は `work-records/md/work_record_###.md` 形式とする。
- 連番は3桁ゼロ埋めとし、既存最大番号の次を採番する。
- 見出しは `# 作業記録 ###: <内容>` とする。
- タイトル直下に `作成日: YYYY-MM-DD` を記載する。
- GitHub Issueに対応する場合は、本文に `GitHub Issue #<番号>` とリンクを明記する。
- 1つの作業記録が複数のGitHub Issueを扱う場合は、親子・関連・依存を分けて記載する。

## GitHub Issue状況の記録

作業記録を作成する直前に、Pull Requestを除くこのリポジトリの全Open IssueをGitHub APIから再取得する。取得件数と優先順位表のIssue行数を一致させ、番号、タイトル、URL、state、state reason、作業記録との関係・着手条件を各Issueについて記録する。親子関係はsub-issues APIで確認できたものだけを記載し、Issue本文の言及から推測したツリーを作らない。外部リポジトリのIssueは一覧へ混在させず、必要な場合だけ対象と理由を補足する。API取得に失敗した場合は状態を推測せず、未確認範囲と再取得手順を記録する。

- GitHub Issueの一覧、優先順位、親子関係、確認日時は、関連する番号付き作業記録の中に保存する。
- GitHub Issue状況は対応するMarkdownへ記録し、公開時にsandbox-pages側rendererがHTMLへ反映する。
- GitHub Issue状況だけを扱う独立したMarkdownやHTMLは作成しない。
- 現在値のIssue状況は、対象プロジェクトのGitHub APIから `state=open` で取得した全Issueを記載する。Pull Requestは除外し、手作業の抜粋や件数だけの記録は認めない。表示は `work_record_010.html` に合わせ、親子関係ツリーと、`順位`、`優先度`、`GitHub Issue`、`状態`、`関係・着手条件` の5列を持つ優先順位表を使う。
- 親子関係はGitHubのsub-issues APIから取得し、優先度と補足関係は `scripts/dev/github_issue_status_policy.json` で管理する。
- Issue状況の更新は、リポジトリルートで `python -m scripts.dev.sync_github_issue_status --repo owner/name --write` を実行する。対象を省略した場合は番号が最大の作業記録を更新する。
- 更新後は `python -m scripts.dev.sync_github_issue_status --repo owner/name --check` を実行し、MarkdownのIssue番号集合がGitHub APIの全オープンIssueと一致することを確認する。
- このリポジトリでは対象を明示して取得・検証する。

  ```bash
  python -m scripts.dev.sync_github_issue_status --repo tj-999-comp/B_Stats_Site --write
  python -m scripts.dev.sync_github_issue_status --repo tj-999-comp/B_Stats_Site --check
  ```

  同期スクリプトの出力後、各Issueの`state reason`をGitHub API結果で補完し、GitHub APIの取得件数と表の行数を照合する。一致しない場合は完了扱いにしない。
- 2026-08-13時点の一覧の初回記録は [作業記録008](md/work_record_008.md) と、その閲覧用 [work_record_008.html](work_record_008.html) の末尾に保存する。その後に確認した状態は、確認作業に対応する作業記録の末尾へ追記する。今回のチャットで確認した状態は [作業記録010](md/work_record_010.md) と、その閲覧用 [work_record_010.html](work_record_010.html) の末尾に保存する。
- 一覧を更新するときは、更新作業と関係する作業記録に、その時点のオープンIssue全件、確認日時、親子関係、優先順位、変更理由を残す。
- 優先順位は `P0`（今すぐ）から `P3`（後回し）で表す。
- 新規作成を強調する場合は `NEW` と作成日を記載し、次回の一覧更新時に外す。
- 親子関係はGitHub上の登録状態を優先し、単なる関連Issueと混同しない。

## HTMLの作成ルール

- HTMLはsandbox-pagesの `a_rendered` rendererが生成する。生成元でHTMLを新規作成・編集しない。
- 共通デザイン、CSS、HTML構造、安全性、320px幅の表示確認はsandbox-pages側で管理する。
- 作業記録の内容とIssue状況はMarkdownへ記録し、公開時にA側rendererがHTMLへ反映する。
- 過去時点のスナップショットを保存する作業記録は、見出しの日付時点の記録として保持する。現在値として更新する作業記録では、Issue状況を省略せず、必ず同期スクリプトで全オープンIssueを取得する。

## 共通HTMLデザイン

公開HTMLの正本は `tj-999-comp/sandbox-pages` の [`work-records/design.md`](https://github.com/tj-999-comp/sandbox-pages/blob/main/work-records/design.md) とA側renderer/CSSである。`a_rendered` の公開ページは、生成元ごとのHTML・CSS・designを使わず、`record-page`、`shell`、`topbar`、`record-header`、`record-meta`、番号付き`record-section`、共通footerを同じ構造で出力する。新規・更新時は1280px、900px、640px、320pxのviewportで横overflow、console/page error、failed requestがないこと、生成元間の主要構造・スタイルが一致することを確認する。デザイン不一致が残る場合は公開導入を完了扱いにしない。

## 自動検証

`.github/workflows/validate-work-record-filenames.yml` が次を確認する。

1. `work-records/` 直下のMarkdownが `README.md` と `design.md` だけであること。
2. `work-records/md/work_record_*.md` が `work_record_###.md` 形式であること。
3. 番号付き作業記録の先頭見出しが `# 作業記録 ###:` 形式であること。
4. `work-records/md/` 内の番号付きMarkdownが命名規則に従い、同じベース名のmetadataが存在すること。
5. 最新の番号付き作業記録について、GitHub API上の全オープンIssue（Pull Request除外）がIssue状況表に記載されていること。
6. 番号付きMarkdown、metadataの対応とmetadata schemaが一致すること。
7. HTML・CSS・URLのallowlistと共通rendererの表示確認はsandbox-pages側で行うこと。

ローカルでは次を実行する。

```bash
python scripts/dev/validate_work_record_source.py
python scripts/dev/validate_work_record_source.py --check-fixtures
```
