# GitHub Actions ワークフロー解説

更新日: 2026-08-28

`.github/workflows/` 配下にある各 yml ファイルの内容を説明します。

## 認証方式の対応表

| workflow | 外部処理の認証方式 | 参照するSecret・token | 権限と対象 |
|---|---|---|---|
| `scrape.yml` | Supabase Secret key | `SUPABASE_URL`、`SUPABASE_SECRET_KEYS` | Bリーグデータの取得・Supabase投入。server-side専用 |
| `migrate.yml` | PostgreSQL password | `SUPABASE_DB_PASSSWORD` | Supabase接続用。現行workflowのSecret名は綴りを含めこの表記 |
| `deploy-pages.yml` | GitHub Actions内蔵token、Pages OIDC | `GITHUB_TOKEN`、`SUPABASE_URL`、`SUPABASE_PUBLISHABLE_KEYS` | Pages artifactの公開とビルド時の公開キー。Contents writeは不要 |
| `deploy-vercel.yml` | Vercel token | `VERCEL_TOKEN`、`VERCEL_ORG_ID`、`VERCEL_PROJECT_ID` | Vercelへの本番デプロイ。Supabaseの`NEXT_PUBLIC_*`はVercel側の環境変数 |
| `request-publish.yml` | Fine-grained PAT | `SANDBOX_PAGES_DISPATCH_TOKEN` | `tj-999-comp/sandbox-pages`のActions dispatchだけ。Contents writeは付与しない |
| `sandbox-pages/.github/workflows/accept-source.yml` | GitHub Actions内蔵token | dispatch元はBのPAT、workflow内は`github.token` | 公開先自身のcheckout・commit・Pages deploy。jobごとに権限を限定 |

この表はworkflowのソースコードが参照する名前と権限を示すもので、GitHub SettingsにSecretが登録されていること自体は確認しません。Secretの値、token、秘密鍵は表示・保存・記録しません。

Portfolio作業で使うGitHub App Installation tokenは、ローカルからIssue・PR・CIのGitHub APIを操作するための認証です。Actions workflowへ自動的に引き継がれるものではなく、`SANDBOX_PAGES_DISPATCH_TOKEN`の代替として設定済みとは扱いません。

ローカル用App tokenは最長1時間の短期tokenをコマンドごとに発行し、保存しません。秘密鍵のrotation・失効、Keychain確認、発行障害時の確認順は[`config/README.md`](../config/README.md)に従います。

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
| `SUPABASE_SECRET_KEYS` | Supabase の Secret key（旧service_role相当） |

`workflow_dispatch`だけが定義されており、現行workflowは定期実行しません。通常版のscraperは後段の`python -m scripts.db.upsert_games`まで実行します。

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

## request-publish.yml — 作業記録の公開要求

**ファイル:** `.github/workflows/request-publish.yml`

### トリガー

- `push`（`main`ブランチの`work-records/**`変更時）
- `workflow_dispatch`（手動復旧経路）

自動実行ではpushの差分から変更された番号付き作業記録のbasenameだけを抽出します。対象metadataの`publish: true`、同名Markdown・metadata・HTMLの存在、生成元validatorなどの検証に成功したbasenameごとに、`sandbox-pages`へ1件ずつ公開要求をdispatchします。差分に番号付き作業記録がない場合、対象metadataが`publish: true`でない場合、または`work-records/README.md`など無関係な変更だけの場合はdispatchしません。

PR、`pull_request`、fork向けのtriggerは定義していません。Secretを使うdispatch jobは、`main`へのpushまたは利用者が明示した手動実行でのみ動作します。

### 処理概要

1. 自動実行ではpushのbefore/after SHAから変更対象を抽出し、手動実行では入力形式を検査する
2. 対象SHAをcheckoutして`HEAD`と一致することを確認する
3. filename、metadata、HTML再生成、HTML・CSS・URL安全性、fixtureを検証する
4. 対象metadataの`publish: true`、`project_id: B_Stats_Site`、同名Markdown・metadata・HTMLの存在を確認する
5. `sandbox-pages`の`accept-source.yml`へ`project_id`、`source_commit_sha`、`target_basename`だけをworkflow dispatchする

このworkflowは公開先リポジトリをcheckout、編集、commit、pushしません。公開先側の受入・provenance・Pages反映は公開先workflowの責務です。公開要求元の検証成功は公開承認を意味しません。

### 自動triggerの停止と切り戻し

自動公開要求だけを止める場合は、`.github/workflows/request-publish.yml`の`push` triggerを削除して`workflow_dispatch`を残す変更をmainへ反映します。これにより手動公開要求を復旧経路として維持できます。緊急時はActions画面でworkflow自体を一時停止できますが、その場合は手動経路も停止するため、原因確認後にworkflowを再有効化してください。

誤dispatchや障害が発生した場合は、まず自動triggerを停止し、`sandbox-pages`側の受入workflowとprovenance・Pages公開結果を確認します。生成元のmain変更を戻す必要がある場合は、原因となったcommitをrevertして検証workflowを通し、必要な作業記録だけを固定SHA指定の手動実行で再送します。公開先の反映済みデータを直接このrepositoryから削除・上書きせず、公開先のrollback手順に従います。

### dispatch用Secretの運用

| Secret名 | 設定内容 |
|---|---|
| `SANDBOX_PAGES_DISPATCH_TOKEN` | Fine-grained PAT。repository accessは`tj-999-comp/sandbox-pages`だけ、Repository permissionsは`Actions: Read and write`だけ（Contents writeは付与しない） |

2026-08-28時点のB側実装はこのFine-grained PATで`sandbox-pages`の`accept-source.yml`をdispatchします。公開先Issue [sandbox-pages#25](https://github.com/tj-999-comp/sandbox-pages/issues/25)は完了状態ですが、B側workflowの参照方式はPATのままであり、GitHub App Installation tokenへ移行済みとは断定しません。移行する場合は、公開先へのApp install、dispatchに必要な最小Actions権限、B側Secretの段階的廃止、手動・push triggerの非回帰を別途確認します。

PATは作成時に有効期限を設定し、最大90日で運用します。期限の14日前をrotation開始目安とし、新PATを同じSecretへ登録して手動公開要求を1件テストした後、旧PATをGitHubで失効させます。漏えいまたは不要化が判明した場合は、直ちにPATを失効させてSecretを削除または置換し、該当Actions実行を監査します。PAT値、期限付きtoken、API応答をworkflowのmetadata・artifact・ログ・作業記録へ保存しません。

### Secretの変更・障害時手順

1. 変更前に対象workflow、参照名、対象repository、必要権限を確認する。
2. rotationでは新しい資格情報を同じSecret名へ登録し、固定SHAの手動公開要求など最小の疎通確認を行う。
3. 成功を確認してから旧資格情報を失効し、Actions実行履歴と失敗の有無を監査する。
4. dispatch障害時は自動triggerを停止して公開先の受入・provenance・Pages反映を確認する。原因となったsource commitを推測で再送せず、固定SHAを指定した手動実行で復旧する。
5. 秘密値はログ、artifact、workflow出力、Issue、PR、作業記録へ記録しない。

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
