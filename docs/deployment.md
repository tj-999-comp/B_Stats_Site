# デプロイガイド

## 構成1: GitHub Pages

### 必要なGitHub Secrets

| Secret名 | 説明 |
|---------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | SupabaseプロジェクトURL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase公開キー |

### デプロイ手順

1. GitHubリポジトリの Settings > Pages で GitHub Actionsをソースに設定
2. 上記Secretsを設定
3. `main`ブランチへのプッシュで自動デプロイ（`apps/web-static/`変更時）

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
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. 上記GitHub Secretsを設定
4. `main`ブランチへのプッシュで自動デプロイ（`apps/web-vercel/`変更時）

## スクレイパーの自動実行

### 必要なGitHub Secrets

| Secret名 | 説明 |
|---------|------|
| `SUPABASE_URL` | SupabaseプロジェクトURL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabaseサービスロールキー |

毎日UTC 15:00（JST 深夜0時）に自動実行されます。
手動実行はGitHub ActionsのWorkflow dispatchから可能です。
