# デプロイガイド

更新日: 2026-08-28

## 構成1: GitHub Pages

### 必要なGitHub Secrets

| Secret名 | 説明 |
|---------|------|
| `SUPABASE_URL` | SupabaseプロジェクトURL |
| `SUPABASE_PUBLISHABLE_KEYS` | Supabase Publishable key |

### デプロイ手順

1. GitHubリポジトリの Settings > Pages で GitHub Actionsをソースに設定
2. 上記Secretsを設定
3. `main`ブランチへのプッシュで自動デプロイ（`apps/web-static/`変更時）

`web-static` は認証なしの公開閲覧で、データは公開キーを使ってブラウザからSupabaseへ読み取る。service role keyはフロントエンドへ渡さない。リポジトリサイトのURLは `https://tj-999-comp.github.io/B_Stats_Site/` を前提とし、Next.jsの `basePath` は `/B_Stats_Site` に設定する。

`SUPABASE_PUBLISHABLE_KEYS`はworkflowで使うGitHub Secret名であり、ビルド後のブラウザ変数名は`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`（単数）です。Secretの登録有無や値はこの文書では確認しません。

B2・B3などのDB更新後は、ブラウザの再読み込みで同じ画面から参照できる。RLSを変更する場合は、Web実装とは別のDB作業としてバックアップ・検証・修正・ロールバックの手順を用意する。

## 構成2: Vercel

### 必要なGitHub Secrets

| Secret名 | 説明 |
|---------|------|
| `VERCEL_TOKEN` | VercelのAPIトークン |
| `VERCEL_ORG_ID` | Vercel組織ID |
| `VERCEL_PROJECT_ID` | VercelプロジェクトID |

### デプロイ手順

1. [Vercel](https://vercel.com) でプロジェクトを作成
2. Vercel側で環境変数を設定
   - `NEXT_PUBLIC_SUPABASE_URL`（値は `SUPABASE_URL` と同じ）
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`（値は `SUPABASE_PUBLISHABLE_KEYS` と同じ）
3. 上記GitHub Secretsを設定
4. `main`ブランチへのプッシュで自動デプロイ（`apps/web-vercel/`変更時）

`deploy-vercel.yml`はGitHub SecretのVercel認証情報だけを使います。Supabaseの`NEXT_PUBLIC_SUPABASE_URL`と`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`は、Vercelプロジェクト側の環境変数として設定します。

## スクレイパーの自動実行

### 必要なGitHub Secrets

| Secret名 | 説明 |
|---------|------|
| `SUPABASE_URL` | SupabaseプロジェクトURL |
| `SUPABASE_SECRET_KEYS` | Supabaseシークレットキー |

現行の`scrape.yml`は`workflow_dispatch`だけで、定期実行は設定されていません。手動実行はGitHub ActionsのWorkflow dispatchから可能です。

### Supabaseマイグレーション

| Secret名 | 用途 |
|---|---|
| `SUPABASE_DB_PASSSWORD` | `migrate.yml`の`PGPASSWORD`。現行workflowが参照するSecret名を綴りどおり記載 |

`SUPABASE_DB_PASSSWORD`は既存のGitHub Secret名で、`PASSWORD`ではありません。改名する場合はSecret登録、workflow、手動実行手順を同時に切り替える必要があるため、このIssueでは本番Secretを変更しません。

## 作業記録の手動公開要求

公開要求は`.github/workflows/request-publish.yml`のmainへの`work-records/**` push、またはWorkflow dispatchから実行します。検証済みの固定commit SHAと、`publish: true`の対象basenameを指定してください。公開先`sandbox-pages`へのdispatchには現行実装では`SANDBOX_PAGES_DISPATCH_TOKEN`（Fine-grained PAT）を使います。PATは`sandbox-pages`だけに限定し、ActionsのRead and writeだけを付与し、Contents writeは付与しません。GitHub App Installation tokenはローカルのIssue・PR操作用で、公開要求workflowの認証方式とは別です。期限、rotation、失効手順は[`docs/workflows.md`](workflows.md)に記録しています。
