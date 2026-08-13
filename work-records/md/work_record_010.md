# 作業記録 010: 作業記録の呼称・配置・表示ルール再編
作成日: 2026-08-13

## 目的

GitHub Issueとリポジトリ内の調査・実行記録の呼称が混在していたため、役割、名称、保存場所、HTML表示のルールを分離する。

## 決定事項

- `Issue` はGitHub Issueだけを指す。
- リポジトリ内の調査、実行結果、判断経緯は `作業記録` と呼ぶ。
- 旧 `issues/` は `work-records/` へ変更する。
- 作業記録Markdownは `work-records/md/work_record_###.md` に置く。
- 閲覧用HTMLはサブディレクトリを作らず、`work-records/` 直下に置く。
- `work-records/` 直下のMarkdownは `README.md` と `design.md` だけとする。
- HTMLは `work-records/design.md` を原則として守る。
- GitHub Issue状況は独立した一覧ファイルにせず、関連する作業記録へ保存する。HTMLがある場合は、その作業記録HTMLの末尾へ追加する。

## GitHub側の整理

- GitHub Issue #24 → #25の親子登録を確認した。
- GitHub Issue #22・#23を#12の正式な子Issueとして登録した。
- #12配下が#21（完了）、#22・#23（open）の3件であることを確認した。

## 作成・更新物

- `work-records/README.md`: 呼称、配置、命名、Issue状況、HTMLの運用ルール
- `work-records/design.md`: 作業記録HTMLのデザイン原則
- `work-records/md/work_record_008.md`: 2026-08-13時点のGitHub Issue状況を実施記録の末尾へ統合
- `work-records/work_record_008.html`: 上記の閲覧用HTML
- `scripts/dev/validate_work_record_filenames.py`: 作業記録の配置・命名検証
- `.github/workflows/validate-work-record-filenames.yml`: CI検証

## 検証

- `work-records/` 直下のMarkdownが`README.md`と`design.md`だけであることを確認した。
- 作業記録の配置、ファイル名、見出し番号、HTMLとMarkdownの対応を検証スクリプトで確認した。
- `work_record_008.html`を1280、900、640、320px幅で確認し、横overflow、console error、page errorがないことを確認した。
- 320px実寸で見出し44px、本文16px、Issue行12件を確認した。
