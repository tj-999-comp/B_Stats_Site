# セットアップガイド

## 前提条件

- Node.js 20+
- pnpm 9+
- Python 3.11+
- Supabaseアカウント

## 1. リポジトリのクローン

```bash
git clone https://github.com/tj-999-comp/B_Stats_Site.git
cd B_Stats_Site
```

## 2. 依存関係のインストール

```bash
pnpm install
```

## 3. Supabaseのセットアップ

1. [Supabase](https://supabase.com) でプロジェクトを作成
2. `supabase/migrations/20260221_init.sql` を実行してテーブルを作成
3. Supabase AuthenticationでEmail+Password認証を有効化
4. 新規登録を無効化（Settings > Authentication > Disable signups）
5. 自分用のアカウントを作成
6. MFA（多要素認証）を有効化

## 4. 環境変数の設定

```bash
# apps/web-static/.env.local
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEYS=your-publishable-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key

# apps/web-vercel/.env.local
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEYS=your-publishable-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key

# scraper/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEYS=your-secret-key
```

## 5. スクレイパーのセットアップ

```bash
cd scraper
pip install -r requirements.txt
cp .env.example .env
# .envを編集して接続情報を設定
```

## 6. GitHub Secrets の設定

GitHub Actions（スクレイピング・マイグレーション）が使用するシークレットを登録する。

登録先: [Settings → Secrets and variables → Actions](https://github.com/tj-999-comp/B_Stats_Site/settings/secrets/actions)

| Secret名 | 値の取得先 | 用途 |
|---|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL | スクレイパーのDB接続先 |
| `SUPABASE_SECRET_KEY` | Supabase → Project Settings → API → service_role key | スクレイパーのDB認証 |
| `SUPABASE_PUBLISHABLE_KEYS` | Supabase → Project Settings → API → anon key | フロントエンドの公開キー |
| `SUPABASE_DB_PASSWORD` | Supabase → Project Settings → Database → Database password | マイグレーション適用（psql接続） |

> **`SUPABASE_DB_PASSWORD` の取得手順**
> 1. [Supabase ダッシュボード](https://supabase.com/dashboard) を開く
> 2. 対象プロジェクト → **Project Settings** → **Database**
> 3. **Database password** 欄の「Reset database password」またはコピーアイコンから取得
> 4. 上記の GitHub Secrets 登録先に `SUPABASE_DB_PASSWORD` として登録

## 7. 開発サーバーの起動

```bash
# 構成1: GitHub Pages
pnpm --filter web-static dev

# 構成2: Vercel
pnpm --filter web-vercel dev
```
