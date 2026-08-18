# GitHub Actions ワークフロー解説

`.github/workflows/` 配下にある各 yml ファイルの内容を説明します。

---

## scrape.yml — Bリーグ統計データのスクレイピング

**ファイル:** `.github/workflows/scrape.yml`

### トリガー

| トリガー | 説明 |
|---|---|
| `workflow_dispatch` | GitHub UI または API からの手動実行 |

> スクレイピングの頻度が必要になった場合は、`schedule` トリガー（例: `cron: '0 15 * * *'`）を追加することで定期実行に切り替えられます。

### 処理概要

1. リポジトリをチェックアウト
2. Python 3.11 をセットアップ
3. `scraper/requirements.txt` の依存パッケージをインストール
4. `python -m scripts.scraping.scraper` を実行し、Bリーグ公式サイトからデータを取得して Supabase に保存
   - `play_by_play` はデータ量が大きいため運用上インポートしない（`--with-play-by-play` フラグ未使用）

### 必要なシークレット

| シークレット名 | 説明 |
|---|---|
| `SUPABASE_URL` | Supabase プロジェクトの URL |
| `SUPABASE_SECRET_KEYS` | Supabase の service_role キー |

---

## validate-work-record-filenames.yml — 作業記録の配置・命名規則チェック

**ファイル:** `.github/workflows/validate-work-record-filenames.yml`

### トリガー

| トリガー | 説明 |
|---|---|
| `push` | `work-records/**` の変更時に自動実行 |
| `pull_request` | `work-records/**` を含むPRで実行 |
| `workflow_dispatch` | 手動実行 |

### 処理概要

1. リポジトリをチェックアウト
2. Python 3.11 をセットアップ
3. `scripts/dev/validate_work_record_filenames.py` を実行
   - `work-records/` 直下のMarkdownが `README.md` と `design.md` だけであることを検査
   - 作業記録が `work-records/md/work_record_###.md` 形式であることを検査
   - ファイル番号と `# 作業記録 ###:` の見出し番号が一致することを検査
   - HTMLが `work-records/work_record_###.html` にあり、同番号のMarkdownが存在することを検査
4. `scripts/dev/sync_github_issue_status.py --check` を実行し、最新の作業記録にGitHub API上の全オープンIssue（Pull Request除外）が記載されていることを検査

Issue状況を更新する場合は、リポジトリルートで次を実行する。

```bash
python -m scripts.dev.sync_github_issue_status \
  --repo tj-999-comp/B_Stats_Site \
  --write
```

このコマンドはGitHub APIから全オープンIssueとsub-issuesの親子関係を取得し、`github_issue_status_policy.json` の優先度設定を使って、番号が最大の作業記録のMarkdown末尾へ `work_record_010.html` と同じツリー・優先順位表を生成した後、対応するHTMLを再生成する。確認だけを行う場合は `--check` を使う。

---

## deploy-pages.yml — GitHub Pages へのデプロイ

**ファイル:** `.github/workflows/deploy-pages.yml`

### トリガー

| トリガー | 説明 |
|---|---|
| `push` (main ブランチ) | `apps/web-static/**` または `packages/**` への変更時に自動実行 |
| `workflow_dispatch` | 手動実行 |

### 処理概要

1. **build ジョブ**
   - リポジトリをチェックアウト
   - pnpm 9 と Node.js 20 をセットアップ
   - `pnpm install --frozen-lockfile` で依存パッケージをインストール
   - `pnpm --filter web-static build` で Next.js 静的サイトをビルド
   - `apps/web-static/out` を GitHub Pages アーティファクトとしてアップロード

2. **deploy ジョブ**（build 完了後に実行）
   - GitHub Pages にデプロイ

### 必要なシークレット

| シークレット名 | 説明 |
|---|---|
| `SUPABASE_URL` | Supabase プロジェクトの URL |
| `SUPABASE_PUBLISHABLE_KEYS` | Supabase の Publishable key |

> `deploy-pages.yml` では上記シークレットを `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` にマッピングしてビルド時に利用します。

---

## deploy-vercel.yml — Vercel へのデプロイ

**ファイル:** `.github/workflows/deploy-vercel.yml`

### トリガー

| トリガー | 説明 |
|---|---|
| `push` (main ブランチ) | `apps/web-vercel/**` または `packages/**` への変更時に自動実行 |
| `workflow_dispatch` | 手動実行 |

### 処理概要

1. リポジトリをチェックアウト
2. pnpm 9 と Node.js 20 をセットアップ
3. Vercel CLI をグローバルインストール
4. `pnpm install --frozen-lockfile` で依存パッケージをインストール
5. `vercel deploy --prod` で Vercel の本番環境にデプロイ

### 必要なシークレット

| シークレット名 | 説明 |
|---|---|
| `VERCEL_TOKEN` | Vercel の認証トークン |
| `VERCEL_ORG_ID` | Vercel の組織 ID |
| `VERCEL_PROJECT_ID` | Vercel のプロジェクト ID |
