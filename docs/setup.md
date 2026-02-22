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

## 6. 開発サーバーの起動

```bash
# 構成1: GitHub Pages
pnpm --filter web-static dev

# 構成2: Vercel
pnpm --filter web-vercel dev
```
