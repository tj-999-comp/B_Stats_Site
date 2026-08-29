# セットアップガイド

更新日: 2026-08-28

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
2. `supabase/rebuild/00_rebuild_all.sql` を実行して現行テーブル群を作成
3. `web-static` は認証なしの公開閲覧とし、ブラウザからPublishable keyで読み取る
4. Publishable keyで現行4テーブルを読み取れるRLS設定を確認する

認証が必要なVercel版の設定は、#57/#59の実装範囲で別途確定する。

## 4. 環境変数の設定

```bash
# apps/web-static/.env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key

# apps/web-vercel/.env.local
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
| `SUPABASE_SECRET_KEYS` | Supabase → Project Settings → API → Secret key（旧service_role相当） | スクレイパーのDB認証 |
| `SUPABASE_PUBLISHABLE_KEYS` | Supabase → Project Settings → API → anon key | フロントエンドの公開キー |
| `SUPABASE_DB_PASSSWORD` | Supabase → Project Settings → Database → Database password | マイグレーション適用（psql接続） |
| `SANDBOX_PAGES_DISPATCH_TOKEN` | GitHub fine-grained PAT（移行完了までの既存経路） | `sandbox-pages`への公開要求dispatch |
| `PUBLISH_APP_ID` | GitHub App settings | GitHub App経路のApp ID（段階移行時だけ） |
| `PUBLISH_APP_PRIVATE_KEY` | GitHub App settingsで発行した秘密鍵 | GitHub App経路のinstallation token発行（段階移行時だけ） |

> **`SUPABASE_DB_PASSSWORD` の取得手順**
> 1. [Supabase ダッシュボード](https://supabase.com/dashboard) を開く
> 2. 対象プロジェクト → **Database** → **Settings**
> 3. **Database password** 欄の「Reset database password」またはコピーアイコンから取得
> 4. 上記の GitHub Secrets 登録先に `SUPABASE_DB_PASSSWORD` として登録

`SUPABASE_SECRET_KEYS`はPython scraperと`scrape.yml`が実際に参照する複数形です。`SUPABASE_PUBLISHABLE_KEYS`はGitHub Secret名、`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`はWebアプリ内の公開環境変数名です。`SUPABASE_DB_PASSSWORD`は現行workflowの既存名で、綴りを変更する場合はworkflowとSecret登録を同時に切り替えます。

なお、`scripts/generate_table_definition_live.mjs`には過去設定との互換性のため`SUPABASE_SECRET_KEY`（単数）のフォールバックが残っています。新規設定とGitHub Actionsでは`SUPABASE_SECRET_KEYS`（複数）を使用し、単数形へ戻さないでください。

GitHub Actions Secretの登録名はworkflowの参照名と一致させる。`SANDBOX_PAGES_DISPATCH_TOKEN`はGitHub App経路の疎通と旧PAT失効が完了するまで残し、`PUBLISH_APP_ID`と`PUBLISH_APP_PRIVATE_KEY`は管理者がAppを`sandbox-pages`だけへinstallした後に登録する。Secretの値は作業記録やログへ記載しない。

## 7. 開発サーバーの起動

```bash
# 構成1: GitHub Pages
pnpm --filter web-static dev

# 構成2: Vercel
pnpm --filter web-vercel dev
```
