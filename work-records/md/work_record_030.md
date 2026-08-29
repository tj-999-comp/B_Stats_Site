# 作業記録 030: 認証方式・Secret名・運用文書の整合確認
作成日: 2026-08-28

## 概要

Issue #68「[Actions][Docs] 認証方式・Secrets名・運用ドキュメントの整合を確認する」について、GitHub Actions、Supabase、Web公開、公開先リポジトリの受入workflow、Portfolio作業の認証境界をソースコードから照合した。資格情報の値、本番Secretの変更、DB変更、workflow dispatchの実行は対象外とした。

完了条件は、対象workflowごとの認証方式・権限・対象範囲の確定、Secret名の整合、GitHub Appの発行・短期token・rotation・失効・障害復旧手順の文書化、Publishable keyとserver-side Secretの境界の表化、旧表記の再検索、文書と作業記録の検証である。

対象Issue:

- [#68 認証方式・Secrets名・運用ドキュメントの整合を確認する](https://github.com/tj-999-comp/B_Stats_Site/issues/68)
- [sandbox-pages#25 dispatch認証をFine-grained PATからGitHub Appへ移行する](https://github.com/tj-999-comp/sandbox-pages/issues/25)

## 適用した役割

### 実際に担当したRole

- `Security review`: workflowの権限、Secretの用途、公開キーとserver-side Secretの露出範囲を確認
- `Documentation`: workflow、deployment、setup、Portfolio標準の記載を現行実装へ同期
- `GitHub operation`: Issueと公開先Issueの最新状態、公開先受入workflow、GitHub App接続を確認

## 主要な判断

- B側の`.github/workflows/request-publish.yml`は、2026-08-28時点で`SANDBOX_PAGES_DISPATCH_TOKEN`というFine-grained PATを使い、`tj-999-comp/sandbox-pages`の`accept-source.yml`へdispatchしている。B側workflowにGitHub App Installation tokenの参照はない。
- `sandbox-pages#25`はGitHub上で`closed`・`completed`だが、Issue本文の完了条件は未チェックのままで、公開先の現行`accept-source.yml`はworkflow内のcheckout・commit・Pages deployに`github.token`を使う。公開要求を開始するB側PATが廃止されたとは確認できないため、移行済みとは断定しない。
- ローカルPortfolio作業のGitHub App Installation tokenは、Issue・PR・CIのAPI操作用であり、Actions workflowのdispatch認証とは別である。App tokenは短期発行・保存しない運用を文書化した。
- `--verify`の表示可能なメタデータでは、現行Installation tokenに`actions: write`、`contents: write`、`workflows: write`などが含まれていた。Portfolio作業に必要な最小権限（`contents: read`、`issues: write`、`pull_requests: write`、`actions: read`）を設定テンプレートへ追加したが、実インストールの権限変更は行っていない。
- Python scraperと`scrape.yml`のSupabase Secret名は`SUPABASE_SECRET_KEYS`、Pages buildのGitHub Secret名は`SUPABASE_PUBLISHABLE_KEYS`、Webアプリの公開環境変数名は`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`である。
- `migrate.yml`が参照する`SUPABASE_DB_PASSSWORD`は綴りを含む現行Secret名として文書化した。実Secretを改名するにはworkflowと登録を同時に切り替える必要があるため、本作業では変更しない。
- GitHub Actions Secret一覧APIは、使用したGitHub App Installation tokenにActions Secretの参照権限がなくHTTP 403となった。登録有無・発行主体・PAT期限は推測せず、workflowが参照する名前と必要権限だけを記録した。

## 実行内容

1. 作業開始時の`git status --short`が空であることを確認し、`issue-68-auth-docs`ブランチを作成した。
2. Issue #68と公開先`sandbox-pages#25`の最新状態をGitHub APIで取得した。#68は`open`、更新日時は2026-08-28 15:12:56 JST、#25は`closed`・`completed`、更新日時は2026-08-20 15:40:50 JSTだった。
3. `.github/workflows/request-publish.yml`、`scrape.yml`、`migrate.yml`、`deploy-pages.yml`、`deploy-vercel.yml`を確認し、Secret名、job permissions、tokenの用途、triggerを一覧化した。`scrape.yml`の既存設定を確認し、`migrate.yml`にもcheckoutに必要な`contents: read`を明示した。
4. 公開先の`.github/workflows/accept-source.yml`（取得SHA: `ca676e852f37d470f3d45631a627dd7b25680760`）を確認し、dispatch後は公開先の`github.token`で固定SHA checkout、commit、Pages deployを行う契約を確認した。
5. `scripts/db/config.py`、`scripts/db/db.py`、`scripts/generate_table_definition_live.mjs`、Web側のSupabase clientとmiddlewareを検索し、runtimeで使う環境変数名と互換フォールバックを確認した。
6. `docs/workflows.md`へ認証方式対応表、PAT現行状態、GitHub Appとの境界、rotation・失効・障害復旧手順を追加した。
7. `docs/deployment.md`と`docs/setup.md`へ、workflowの実際のtrigger、Secret名の単複、`SUPABASE_DB_PASSSWORD`の綴り、公開キーとWeb環境変数の境界を反映した。
8. `config/github_app.example.json`と`config/README.md`へ、ローカルGitHub App Installation tokenの最小権限要求を追加し、`docs/PORTFOLIO_STANDARD.md`へActions workflow認証との境界を追記した。

## 検証

- GitHub App設定の形式確認: 成功
- GitHub App Installation tokenによるB側repository確認: 成功。token本体は表示・保存していない
- GitHub App tokenの権限メタデータ確認: 成功。現行Installation側に標準文書より広い権限があることを確認
- GitHub Actions Secret一覧取得: 未確認。GitHub APIがHTTP 403（AppにActions Secret参照権限なし）
- `sandbox-pages#25`と公開先受入workflowの読み取り: 成功
- 旧表記・認証境界の`rg`再検索: 実施。単数形はライブ定義生成スクリプトの互換フォールバック1か所だけで、新規設定では使わない旨を文書化
- Markdownリンク・日付・作業記録配置: `git diff --check`、作業記録filename検証で確認
- 作業記録HTML生成・filename検証・GitHub Issue状況同期: 成功。Issue状況は8件の未完了Issueを取得
- PR CI（push検証run `33148437366`、pull request検証run `33148440870`）: 成功。Node.js 20廃止予定warningのみ
- 初回PR CIのmetadata不足: `work_record_030.yml`を追加して解消
- DB変更、Supabase Secret変更、PATのrotation・失効、公開要求dispatch: 未実施（Issueの非対象）

## 最終結果

- 変更ファイル: `.github/workflows/migrate.yml`、`config/README.md`、`config/github_app.example.json`、`docs/workflows.md`、`docs/deployment.md`、`docs/setup.md`、`docs/PORTFOLIO_STANDARD.md`、本作業記録のMarkdown/HTML/metadata。`scrape.yml`は既存の`contents: read`を確認した。
- 現行実装と公開先workflowの認証方式を整理し、B側dispatchのPATをGitHub App移行済みと誤認しない記載へ更新した。
- `SUPABASE_SECRET_KEYS`、`SUPABASE_PUBLISHABLE_KEYS`、`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`、`SUPABASE_DB_PASSSWORD`の役割と正確な綴りを文書化した。
- 未解決事項: GitHub Actions SettingsにおけるSecret登録有無、PATの発行主体・期限・実値はApp権限不足と非対象条件により確認していない。必要ならリポジトリ管理者が値を表示せず、Secret名・有効期限・fine-grained対象repository・Actions権限だけを確認する。
- 次アクション: Draft PR #69のレビューとmerge後、ユーザーまたは管理者が本番Secretの登録状態を確認する。PATからAppへ移行する場合は、別Issueで公開先install、最小権限、段階的切替、非回帰、旧PAT失効を実施する。
- ブランチ: `issue-68-auth-docs`
- commit: `8b57b47`（実装・作業記録初回commit）
- PR: [#69 Draft PR: 認証方式とSecret運用の記載を整合](https://github.com/tj-999-comp/B_Stats_Site/pull/69)

## GitHub Issue状況（2026-08-29時点の現在値）

確認日: 2026-08-29（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは7件だった。

### 親子関係

```text
#7（未完了・親Issue）
├── #8（完了・子Issue）
├── #45（完了・子Issue）
└── #46（完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（完了・子Issue）
└── #23（完了・子Issue）
#24（完了・親Issue）
└── #25（完了・子Issue）
#56（完了・親Issue）
├── #58（完了・子Issue）
└── #63（完了・子Issue）
#57（未完了・親Issue）
└── #59（未完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P1 | [#57](https://github.com/tj-999-comp/B_Stats_Site/issues/57) [Web][Vercel] SSR/ISR版の統計サイトを実装・公開する | 未完了 | Web導入のVercel親Issue。#59を管理。#58のデータ契約・共通UIを前提 |
| 2 | P2 | [#59](https://github.com/tj-999-comp/B_Stats_Site/issues/59) [Web][Vercel] B1データを表示するSSR/ISR MVPを実装する | 未完了 | #57の子Issue。Vercel版のMVP。#58のデータ契約・共通UIを前提 |
| 3 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 4 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 5 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 6 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 7 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
