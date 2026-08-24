# GitHub App ローカル設定
作成日: 2026-08-24

## 目的

GitHub Issueの状態取得、Issueコメント、Draft PRの作成に使うGitHub App Installation tokenを、ローカル環境で都度発行する。秘密鍵と発行済みtokenはリポジトリへ保存しない。

## 設定手順

1. テンプレートをローカル設定へ複製する。

   ```bash
   cp config/github_app.example.json config/github_app.json
   ```

2. `config/github_app.json`を編集する。`app_id`はGitHub App ID、`client_id`はGitHub App設定画面のClient ID、`repository`はtokenの利用先を1リポジトリへ制限する。`installation_id`は不要で、CLIが対象リポジトリから自動解決する。
3. macOSの「キーチェーンアクセス」で、ログインキーチェーンに汎用パスワード項目を作成する。`keychain_service`を項目の名前へ合わせ、アカウントにはmacOSのログインユーザー名を設定する。パスワード欄にはGitHub AppのPEM形式秘密鍵またはそのBase64エンコード値を保存する。PEMファイル、秘密鍵、tokenをリポジトリやシェル履歴へ保存しない。

   `keychain_account`を省略した場合、CLIはmacOSのログインユーザー名を使う。既存の`keychain: {"service", "account"}`形式または`keychain`文字列形式も受け付ける。新規設定ではテンプレートどおりの4項目を推奨する。
4. 形式とキーチェーン項目を確認する。どちらのコマンドもtokenを出力しない。

   ```bash
   python -m scripts.dev.github_app_token --check-config
   python -m scripts.dev.github_app_token --check-keychain
   python -m scripts.dev.github_app_token --verify
   ```

5. tokenが必要なコマンドだけに一時的に渡す。`--print-token`の標準出力は画面へ表示しない。

   ```bash
   GH_TOKEN="$(python -m scripts.dev.github_app_token --print-token)" \
     gh issue view 45 --repo tj-999-comp/B_Stats_Site --json number,title,state,url
   ```

## 権限の目安

このリポジトリの作業記録・PR運用では、GitHub App側に`contents: read`、`issues: write`、`pull_requests: write`を付与する。CI確認も行う場合は`actions: read`を追加する。configの`permissions`は任意で、指定した場合だけ発行時にtokenの権限を絞り込む。実際に発行できるInstallation tokenの権限は、GitHub Appに付与済みの権限を超えられない。

GitHub AppのJWTはRS256で署名し、`iat`、`exp`、`iss`を含める必要がある。Installation tokenはJWTを使って発行し、有効期限は最長1時間である。[GitHub公式JWTガイド](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app)と[Installation token API](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app)を参照する。
