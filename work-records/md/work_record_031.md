# 作業記録 031: Secret登録状態と公開要求認証の段階移行設計
作成日: 2026-08-29

## 概要

Issue #71「[Actions][Security] Secret運用確認とPATからGitHub Appへの移行を検討する」について、B側のGitHub Actions workflowが参照するSecret名と登録名を値を表示せず確認し、公開要求のPATからGitHub App installation tokenへの段階移行経路を実装・文書化した。

GitHub Actions Secret一覧では、`SANDBOX_PAGES_DISPATCH_TOKEN`、`SUPABASE_DB_PASSSWORD`、`SUPABASE_PUBLISHABLE_KEYS`、`SUPABASE_URL`、旧単数形の`SUPABASE_SECRET_KEY`を確認した。一方、現行workflowが参照する`SUPABASE_SECRET_KEYS`と`VERCEL_*` 3件は一覧になかった。移行用の`PUBLISH_APP_ID`と`PUBLISH_APP_PRIVATE_KEY`も未登録である。

## 対象と制約

- [#71 Secret運用確認とPATからGitHub Appへの移行検討](https://github.com/tj-999-comp/B_Stats_Site/issues/71)
- [#68 認証方式・Secrets名・運用ドキュメントの整合](https://github.com/tj-999-comp/B_Stats_Site/issues/68)
- [sandbox-pages#25 dispatch認証のGitHub App移行](https://github.com/tj-999-comp/sandbox-pages/issues/25)
- Secret値、PAT値、秘密鍵、発行主体、有効期限の取得・表示・保存は行わない。
- Secret変更、PAT rotation・失効、GitHub App install、workflow dispatch、DB変更は管理者確認が必要なため行わない。

## 主要な判断

- `request-publish.yml`は、`PUBLISH_APP_ID`と`PUBLISH_APP_PRIVATE_KEY`が両方設定された場合だけGitHub App installation tokenを発行する。tokenの対象は`tj-999-comp/sandbox-pages`だけ、要求権限は`Actions: write`だけとする。
- App Secretが未設定で`SANDBOX_PAGES_DISPATCH_TOKEN`が設定されている場合は、既存PAT経路へ戻す。App IDと秘密鍵の片方だけが設定された場合、または両経路が未設定の場合はdispatch前に失敗させる。
- App経路を有効化しても旧PATを直ちに失効させず、固定SHA・単一対象の手動公開、公開先受入、provenance、Pages deploy、公開URL、Slack通知、push起点の順で非回帰を確認してから失効する。
- `sandbox-pages`側の受入workflowは、公開要求の認証方式とは独立して、同リポジトリの`github.token`で固定SHA checkout、commit、Pages deploy、Slack通知を行う。移行対象はB側のdispatch認証だけである。

## 実行内容

1. 作業開始時の作業ツリーがクリーンで、`main`と`origin/main`が一致していることを確認し、Issue専用ブランチを作成した。
2. GitHub APIでIssue #71、Issue #68、PR #69、`sandbox-pages#25`の状態を確認した。#71は未完了、#68は完了、PR #69はマージ済み、#25は完了である。
3. `gh api repos/tj-999-comp/B_Stats_Site/actions/secrets`でSecret名と更新日時だけを取得し、値は取得しなかった。
4. `.github/workflows/scrape.yml`、`migrate.yml`、`deploy-pages.yml`、`deploy-vercel.yml`、`request-publish.yml`を照合し、参照名との差異を整理した。
5. 公開先`sandbox-pages`の`accept-source.yml`を読み取り、固定SHAの受入、Pages deploy、Slack通知の経路を確認した。
6. GitHub公式仕様を確認し、workflow dispatchに必要なGitHub App installation tokenの最小権限を`Actions: write`とした。
7. `request-publish.yml`へ、App経路の選択、App tokenの短期発行、PAT fallback、片側設定検出、認証方式の非秘密ログを追加した。
8. `docs/workflows.md`、`docs/deployment.md`、`docs/setup.md`へSecret登録状態、段階移行、rollback、E2E確認手順を反映した。

## 管理者が行う残作業

1. `SUPABASE_SECRET_KEYS`の登録要否を確認し、必要なら旧単数形`SUPABASE_SECRET_KEY`との用途を切り分けて登録する。`scrape.yml`を実行するまで、一覧にない状態では復旧しない。
2. Vercel公開を利用する場合だけ、`VERCEL_TOKEN`、`VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`の登録状態と値の有効性を確認する。
3. `SANDBOX_PAGES_DISPATCH_TOKEN`について、値を表示せず発行主体、期限、対象repository、Actions権限を確認する。
4. GitHub Appを`sandbox-pages`だけへinstallし、Actions writeだけを許可してから、`PUBLISH_APP_ID`と`PUBLISH_APP_PRIVATE_KEY`を登録する。Contents writeとWorkflows権限は付与しない。
5. 固定SHA・単一対象の手動公開でApp経路を確認し、続けてpush起点、公開先受入、provenance、Pages、公開URL、Slack通知を確認する。これらのdispatchは管理者の明示承認後に行う。
6. App経路の成功を確認した後、旧PATを失効し、`SANDBOX_PAGES_DISPATCH_TOKEN`を削除または未使用状態にする。失敗時は旧PAT経路へ戻し、固定SHAの手動実行で復旧する。

## 検証

- Secret一覧の読み取り: 成功。値は取得していない。
- 現行workflowのSecret参照名との照合: 成功。
- `sandbox-pages`の受入workflow読み取り: 成功。受入、commit、Pages deploy、Slack通知を確認した。
- GitHub公式REST API仕様の確認: 成功。workflow dispatchはGitHub App installation access tokenの`Actions: write`に対応する。
- YAML差分の静的確認: Ruby YAML parserで成功。`actionlint`は環境に未導入のため未実施。
- `git diff --check`: 成功。
- Python構文確認（`scripts`、`Colab`）: 成功。
- 作業記録filename、MarkdownからHTMLへの再生成・再生成check、Issue状況同期: 成功。
- App install、Secret変更、PAT rotation・失効、公開要求dispatch、Pages公開、Slack通知: 未実施（管理者承認が必要）。

## 最終結果

- B側workflowに、既存PATを維持したままGitHub Appへ切り替えられる段階移行経路を追加した。
- Secret登録名の実測結果を文書化し、`SUPABASE_SECRET_KEYS`未登録、旧単数形のみ登録、Vercel Secret未登録という差異を明記した。
- App install、Secret登録、E2E、旧PAT失効は未完了であり、管理者操作待ちとして残した。
- ブランチ: `issue-71-secret-operations`

## GitHub Issue状況（2026-08-29時点の現在値）

確認日: 2026-08-29（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは8件だった。

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
| 8 | P3 | [#71](https://github.com/tj-999-comp/B_Stats_Site/issues/71) [Actions][Security] Secret運用確認とPATからGitHub Appへの移行を検討する | 未完了 | 独立。優先度未設定 |
