# Portfolio作業標準

更新日: 2026-08-20

この文書は、B、C、Dなど複数の生成元リポジトリで作業記録を作成し、GitHub IssueとPull Requestを使って公開可能な状態まで届けるための共通標準である。リポジトリ固有の細部は`AGENTS.md`、公開受入の契約は[`projects/README.md`](../projects/README.md)、作業記録HTMLの見た目は[`work-records/design.md`](../work-records/design.md)を正本とする。

## 1. 「作業記録を残して」の解釈

ユーザーが「作業記録を残して」と依頼した場合、次を一式として扱う。

1. 対象Issue、完了条件、変更範囲を確定する。
2. 課題専用ブランチを作成する。ドキュメントだけの短縮工程は`AGENTS.md`の例外規則に従う。
3. 実装または文書変更を行う。
4. `work-records/md/work_record_###.md`を作成する。
5. `python3 scripts/dev/convert_work_records_to_html.py`で同番号のHTMLを生成する。
6. filename・Markdown・HTML・構文・テスト・必要なブラウザ確認を実行する。
7. 対象ファイルだけをstageし、commitする。
8. 作業ブランチをpushする。
9. GitHub App tokenでIssueの実状態とPR情報を取得し、Issueへ完了コメントを残す。
10. PRを作成し、差分・レビュー・CIを確認する。

「完了」は、実装・検証・作業記録・push・PR作成までを指す。Issueのクローズは、PRがmergeされた後、またはユーザーが明示的に早期クローズを指定した場合に行う。PR未mergeの状態でIssueを閉じる場合は、理由とPR URLをIssueコメントへ残す。

## 2. GitHub接続の標準

初回セットアップでは、`PyJWT`と`cryptography`を実行環境へ用意する。秘密鍵を含むファイルを依存インストール用のログやリポジトリへ置かない。

```bash
python3 -c 'import jwt, cryptography; print("GitHub App dependencies OK")'
```

### 認証方式

Issue、PR、レビュー、CIの取得には、個人の期限付きOAuth/PATではなくGitHub AppのInstallation tokenを使う。

これはローカルのPortfolio作業でGitHub APIを操作するための標準です。GitHub Actions workflowの認証方式を変更する規定ではありません。公開要求workflowなどが参照するActions Secretは、各workflowと公開先の受入契約を確認したうえで別途管理します。現行の`request-publish.yml`は`SANDBOX_PAGES_DISPATCH_TOKEN`のFine-grained PATを参照しており、ローカル用GitHub App tokenへ置き換わったとは扱いません。

- 設定: `config/github_app.json`（`config/github_app.example.json`を複製してローカルで作成。`permissions`はテンプレートの最小権限を維持する）
- 秘密鍵: Macキーチェーンの一般パスワード項目
- 発行: `python3 scripts/dev/github_app_token.py`
- token: 実行ごとに発行し、保存しない
- `GH_TOKEN`: 対象コマンドのサブプロセスだけへ渡す

設定値、Keychain項目、確認コマンドは[`config/README.md`](../config/README.md)を正本とする。`config/github_app.json`はGit管理外とし、追跡するのは秘密値を含まない`config/github_app.example.json`だけにする。

標準コマンドは次の形式にする。`--print-token`の出力を画面やログへ直接表示しない。

```bash
GH_TOKEN="$(python3 scripts/dev/github_app_token.py --print-token)" \
  gh issue view <番号> --repo <owner/repository> --json number,title,state,url
```

Git操作の認証はSSHを基本とし、GitHub API用のInstallation tokenと混ぜない。Appの秘密鍵、Installation token、JWTをリポジトリ、作業記録、ログ、PR本文へ記録しない。

### Issueスナップショット

Issue状況を作業記録へ記載する場合、作成直前に次を取得する。

- 対象Issueの番号、タイトル、URL、state、state reason
- 関連する親Issue・子Issue・依存Issue
- 取得日時（JST）
- 作業記録との関係と着手条件

GitHub APIが失敗した場合は、状態を推測せず「取得不可」と記載する。取得不可のまま完了扱いにする場合は、原因、未確認Issue、再取得すべき次アクションを記録する。

## 3. Issue・commit・PRの状態遷移

| 段階 | 必須成果物 | Issue操作 | 完了条件 |
| --- | --- | --- | --- |
| 着手 | ブランチ、作業計画 | 状況確認 | baseと対象Issueを確認 |
| 実装中 | ソース、テスト | 必要なら着手コメント | 作業記録へ事実を蓄積 |
| 検証済み | MD、生成HTML、テスト結果 | 完了コメント案 | 重大な未解決事項0件 |
| PR中 | push済みcommit、PR | PR URLをコメント | CI・差分・レビュー確認 |
| 完了 | merge済み成果物 | Issue close | mergeまたは明示承認を確認 |

PR本文は日本語で、概要、変更ファイル、検証、ブラウザ確認、レビュー結果、対応Issue、未解決事項を含める。PRは原則Draftで作成し、外部確認が不要な場合でも勝手にmergeしない。

## 4. 作業記録の共通フォーマット

### Markdown

ファイル名と見出し番号を一致させる。

```text
work-records/md/work_record_###.md
work-records/work_record_###.html
```

必須構成は次のとおりである。

```md
# 作業記録 ###: <内容>
作成日: YYYY-MM-DD

## 概要
## 適用した役割
### 実際に担当したRole
## 主要な判断
## 最終結果
## GitHub Issue状況
```

`概要`には課題、目的、完了条件、`最終結果`には解決内容、変更ファイル、検証結果、ブランチ、commit、PR、未解決事項、次アクションを記録する。未使用の役割欄は作らない。

### HTML

- HTMLはMarkdownからconverterで生成し、直接編集しない。
- CSSは`work-record.css`を参照する。
- タイトル、見出し、表、コードブロック、リンクを同じ変換規則で生成する。
- Markdownのraw HTMLは実行せず、文字列としてescapeする。
- 相対リンクはHTMLの出力位置を基準に解決する。
- 320px幅で横overflowを発生させない。
- GitHub Issue状況は専用一覧ページを作らず、該当作業記録の末尾へ含める。

検証コマンド:

```bash
python3 scripts/dev/convert_work_records_to_html.py
python3 scripts/dev/convert_work_records_to_html.py --check
python3 scripts/dev/validate_work_record_filenames.py
```

表示変更がある場合は、少なくとも1280pxと320pxでChromium確認を行う。

## 5. B、C、Dを追加する手順

新しい生成元は、個別の都合で公開先や命名を増やさず、公開リポジトリAの`config/sources.json`へ登録してから受入する。

### 登録前

- 不変な`project_id`を決める。
- source repository、branch、source directory、metadata directory、destination directoryを確定する。
- `a_rendered`または既存互換の`source_html`を選ぶ。新規C/Dは原則`a_rendered`。
- metadata、命名、HTML生成、リンク、安全性、容量制限を確認する。
- A側にregistry entry、validator fixture、provenanceの保管場所を追加する。
- `enabled: false`のままdry-runとno-opを通す。

### 受入後

1. source-side validationを通したcommitを固定する。
2. A側がsource registryから受入ファイルを再導出する。
3. HTML/CSS/URL・metadata・digest・driftをA側で再検証する。
4. 初期公開物がある場合は初期provenance manifestを作成する。
5. 既存分のno-op dry-runを確認する。
6. 新規1件でpublish・Pages・公開URL・必要な通知をE2E確認する。
7. 問題がなければ`enabled: true`へ変更する。

Bは既存の`source_html`互換方式を維持し、既存URLと番号を変更しない。C/Dは番号を各project内で独立採番し、`<project_id>:<work_record_###>`を一意識別子とする。project間で番号を共有する必要はない。

## 6. リポジトリへの適用範囲

| 正本 | 適用内容 |
| --- | --- |
| `AGENTS.md` | エージェントの実行手順、認証、branch、PR、Issue完了条件 |
| `README.md` | 開発者向け入口と標準文書への導線 |
| `docs/PORTFOLIO_STANDARD.md` | B/C/D共通の詳細標準 |
| `work-records/README.md` | Markdown/HTMLの作成・検証手順 |
| `projects/README.md` | 公開受入、source registry、provenance、Pages契約 |
| `config/sources.json` | projectごとの許可範囲と有効化状態 |
| `scripts/dev/` | 再現可能な生成、検証、GitHub App接続 |

ルールを変更した場合は、この文書と該当する正本を同じ変更で更新し、作業記録に影響範囲と移行手順を記録する。生成元B/C/Dへは共通ルールの要約と参照URLを配置し、公開受入の正本を複製しない。

## 7. 例外

- ユーザーがブランチ、commit、PR、Issue closeのいずれかを明示的に不要とした場合は、その範囲だけ省略する。
- 調査・説明・レビューのみでファイルを変更しない場合、作業記録は作成しない。
- GitHub接続不能時は、ローカル実装・テスト・commitまで進められるが、Issue状態を推測せず、PR工程完了とは報告しない。
- 秘密鍵やtokenを取得できない場合は、資格情報を探索・表示せず、ユーザーへ必要な再認証またはKeychain登録だけを依頼する。
