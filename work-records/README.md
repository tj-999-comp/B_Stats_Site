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
├── work_record.css            # HTML共通スタイル
├── work_record_###.html       # 番号付き作業記録の閲覧用HTML
├── work_record_extra_##.html   # 補助Markdownの閲覧用HTML
└── md/
    ├── work_record_001.md    # 番号付き作業記録
    ├── phase_1_tasks.md      # 補助Markdown
    └── scraping_db_automation.md
```

- HTMLはサブディレクトリを作らず、`work-records/` 直下へ置く。
- `work-records/` 直下のMarkdownは `README.md` と `design.md` だけとする。
- 作業記録と補助Markdownは `work-records/md/` に置く。
- 番号付きMarkdownは同じベース名のHTMLを `work-records/` 直下に置く。
- 補助Markdownは `phase_1_tasks.md` を `work_record_extra_01.html`、
  `scraping_db_automation.md` を `work_record_extra_02.html` として出力する。
- HTMLは共通の `work_record.css` を参照し、外部ライブラリには依存しない。

MarkdownからHTMLを再生成する場合は、リポジトリルートで次を実行する。

```bash
python -m scripts.dev.convert_work_records_to_html
```

既存HTMLを変更せず、Markdownからの再生成結果と一致するかだけを確認する場合は、次を実行する。

```bash
python -m scripts.dev.convert_work_records_to_html --check
```

番号付き作業記録だけを再生成・確認し、補助文書を対象外にする場合は `--numbered-only` を追加する。

## 作業記録の命名規則

- 作業記録は `work-records/md/work_record_###.md` 形式とする。
- 連番は3桁ゼロ埋めとし、既存最大番号の次を採番する。
- 見出しは `# 作業記録 ###: <内容>` とする。
- タイトル直下に `作成日: YYYY-MM-DD` を記載する。
- GitHub Issueに対応する場合は、本文に `GitHub Issue #<番号>` とリンクを明記する。
- 1つの作業記録が複数のGitHub Issueを扱う場合は、親子・関連・依存を分けて記載する。

## GitHub Issue状況の記録

- GitHub Issueの一覧、優先順位、親子関係、確認日時は、関連する番号付き作業記録の中に保存する。
- HTMLがある場合は、GitHub Issue状況をその `work_record_###.html` の末尾へ追加する。
- GitHub Issue状況だけを扱う独立したMarkdownやHTMLは作成しない。
- 現在値のIssue状況は、対象プロジェクトのGitHub APIから `state=open` で取得した全Issueを記載する。Pull Requestは除外し、手作業の抜粋や件数だけの記録は認めない。表示は `work_record_010.html` に合わせ、親子関係ツリーと、`順位`、`優先度`、`GitHub Issue`、`状態`、`関係・着手条件` の5列を持つ優先順位表を使う。
- 親子関係はGitHubのsub-issues APIから取得し、優先度と補足関係は `scripts/dev/github_issue_status_policy.json` で管理する。
- Issue状況の更新とHTML再生成は、リポジトリルートで `python -m scripts.dev.sync_github_issue_status --repo owner/name --write` を実行する。対象を省略した場合は番号が最大の作業記録を更新する。
- 更新後は `python -m scripts.dev.sync_github_issue_status --repo owner/name --check` を実行し、MarkdownのIssue番号集合がGitHub APIの全オープンIssueと一致することを確認する。
- 2026-08-13時点の一覧の初回記録は [作業記録008](md/work_record_008.md) と、その閲覧用 [work_record_008.html](work_record_008.html) の末尾に保存する。その後に確認した状態は、確認作業に対応する作業記録の末尾へ追記する。今回のチャットで確認した状態は [作業記録010](md/work_record_010.md) と、その閲覧用 [work_record_010.html](work_record_010.html) の末尾に保存する。
- 一覧を更新するときは、更新作業と関係する作業記録に、その時点のオープンIssue全件、確認日時、親子関係、優先順位、変更理由を残す。
- 優先順位は `P0`（今すぐ）から `P3`（後回し）で表す。
- 新規作成を強調する場合は `NEW` と作成日を記載し、次回の一覧更新時に外す。
- 親子関係はGitHub上の登録状態を優先し、単なる関連Issueと混同しない。

## HTMLの作成ルール

- 番号付きHTMLは対応する作業記録と同じ番号の `work-records/work_record_###.html` とする。
- 補助MarkdownのHTMLは、登録済みの `work_record_extra_##.html` とする。
- 作業記録と分離した一覧専用HTMLは作成しない。Issue状況などの付随情報は、関連する作業記録HTMLの末尾へ入れる。
- HTMLを新規作成・編集するときは、[design.md](design.md) を原則として守る。
- デザイン原則から外れる必要がある場合は、対応する作業記録に理由を書く。
- HTMLは外部ライブラリなしでローカル表示でき、320px幅でもページ全体の横スクロールが発生しないようにする。
- HTML内から対応するMarkdown作業記録へ相対リンクを設ける。
- 過去時点のスナップショットを保存する作業記録は、見出しの日付時点の記録として保持する。現在値として更新する作業記録では、Issue状況を省略せず、必ず同期スクリプトで全オープンIssueを取得する。

## 自動検証

`.github/workflows/validate-work-record-filenames.yml` が次を確認する。

1. `work-records/` 直下のMarkdownが `README.md` と `design.md` だけであること。
2. `work-records/md/work_record_*.md` が `work_record_###.md` 形式であること。
3. 番号付き作業記録の先頭見出しが `# 作業記録 ###:` 形式であること。
4. `work-records/md/` 内の各Markdownと同じベース名のHTMLが `work-records/` 直下に存在すること。
5. 最新の番号付き作業記録について、GitHub API上の全オープンIssue（Pull Request除外）がIssue状況表に記載されていること。

ローカルでは次を実行する。

```bash
python scripts/dev/validate_work_record_filenames.py
```
