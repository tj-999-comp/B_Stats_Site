# デプロイガイド

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

## スクレイパーの自動実行

### 必要なGitHub Secrets

| Secret名 | 説明 |
|---------|------|
| `SUPABASE_URL` | SupabaseプロジェクトURL |
| `SUPABASE_SECRET_KEYS` | Supabaseシークレットキー |

毎日UTC 15:00（JST 深夜0時）に自動実行されます。
手動実行はGitHub ActionsのWorkflow dispatchから可能です。

## 作業記録の手動公開要求

公開要求は`.github/workflows/request-publish.yml`をWorkflow dispatchから実行します。検証済みの固定commit SHAと、`publish: true`の対象basenameを指定してください。公開先`sandbox-pages`へのdispatchには`SANDBOX_PAGES_DISPATCH_TOKEN`を使います。PATは`sandbox-pages`だけに限定し、ActionsのRead and writeだけを付与し、Contents writeは付与しません。期限、rotation、失効手順は[`docs/workflows.md`](workflows.md)に記録しています。
