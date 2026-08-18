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
├── <補助文書名>.html          # 補助Markdownの閲覧用HTML
└── md/
    ├── work_record_001.md    # 番号付き作業記録
    └── phase_1_tasks.md      # 補助Markdown
```

- HTMLはサブディレクトリを作らず、`work-records/` 直下へ置く。
- `work-records/` 直下のMarkdownは `README.md` と `design.md` だけとする。
- 作業記録と補助Markdownは `work-records/md/` に置く。
- `work-records/md/` 内のMarkdownは、同じベース名のHTMLを `work-records/` 直下に置く。
- HTMLは共通の `work_record.css` を参照し、外部ライブラリには依存しない。

MarkdownからHTMLを再生成する場合は、リポジトリルートで次を実行する。

```bash
python -m scripts.dev.convert_work_records_to_html
```

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
- 2026-08-13時点の一覧の初回記録は [作業記録008](md/work_record_008.md) と、その閲覧用 [work_record_008.html](work_record_008.html) の末尾に保存する。その後に確認した状態は、確認作業に対応する作業記録の末尾へ追記する。今回のチャットで確認した状態は [作業記録010](md/work_record_010.md) と、その閲覧用 [work_record_010.html](work_record_010.html) の末尾に保存する。
- 一覧を更新するときは、更新作業と関係する作業記録に、その時点のopen件数、親子関係、優先順位、変更理由を残す。
- 優先順位は `P0`（今すぐ）から `P3`（後回し）で表す。
- 新規作成を強調する場合は `NEW` と作成日を記載し、次回の一覧更新時に外す。
- 親子関係はGitHub上の登録状態を優先し、単なる関連Issueと混同しない。

## HTMLの作成ルール

- 番号付きHTMLは対応する作業記録と同じ番号の `work-records/work_record_###.html` とする。
- 補助MarkdownのHTMLは、同じベース名の `work-records/<補助文書名>.html` とする。
- 作業記録と分離した一覧専用HTMLは作成しない。Issue状況などの付随情報は、関連する作業記録HTMLの末尾へ入れる。
- HTMLを新規作成・編集するときは、[design.md](design.md) を原則として守る。
- デザイン原則から外れる必要がある場合は、対応する作業記録に理由を書く。
- HTMLは外部ライブラリなしでローカル表示でき、320px幅でもページ全体の横スクロールが発生しないようにする。
- HTML内から対応するMarkdown作業記録へ相対リンクを設ける。
- 当時のGitHub Issueの状態を現在の状態から再現できない場合、HTMLではIssue状況を省略し、その理由を明記する。本文中のIssue番号・リンクは参照情報として残してよい。

## 自動検証

`.github/workflows/validate-work-record-filenames.yml` が次を確認する。

1. `work-records/` 直下のMarkdownが `README.md` と `design.md` だけであること。
2. `work-records/md/work_record_*.md` が `work_record_###.md` 形式であること。
3. 番号付き作業記録の先頭見出しが `# 作業記録 ###:` 形式であること。
4. `work-records/md/` 内の各Markdownと同じベース名のHTMLが `work-records/` 直下に存在すること。

ローカルでは次を実行する。

```bash
python scripts/dev/validate_work_record_filenames.py
```
