# 作業記録 029: Supabase公開読み取り設定の工程整理
作成日: 2026-08-27

## 概要

GitHub Pages版MVP（#58）の公開確認で、Pages workflowとHTML配信は成功した一方、未認証ブラウザからSupabaseの`games`を取得するとHTTP 200の空配列になり、画面が読み込み中のままになることを確認した。ログインなしで公開データを表示するために、Supabase側で必要な確認・設定・検証工程を明文化した子Issueを#56へ追加する。

完了条件は、#56の子Issue作成、#56→新規Issueのsub-issues登録、Supabaseの接続先・Data API・RLS・キー・REST確認・Pages再デプロイ・ブラウザ受入を含む実行手順の記載、Issue状況の同期、作業記録の検証、PR作成とマージである。Supabaseのlive DB変更はこの作業の対象外とする。

対象Issue:

- [#56 GitHub Pages版の親Issue](https://github.com/tj-999-comp/B_Stats_Site/issues/56)
- [#58 GitHub Pages版MVP](https://github.com/tj-999-comp/B_Stats_Site/issues/58)
- [#63 Supabase公開読み取り設定](https://github.com/tj-999-comp/B_Stats_Site/issues/63)

## 適用した役割

### 実際に担当したRole

- `Issue planning`: Supabase側の作業を接続先、Data API、RLS、キー、REST、Pages受入へ分解
- `Documentation`: #63の実行手順・完了条件・対象外と作業記録を作成
- `GitHub operation`: #63の作成、#56との親子関係登録、PRとIssue状態の確認

## 主要な判断

- 公開サイトはログインなしで動かすため、publishable keyによる未認証リクエストを前提にする。publishable keyは公開されるため、行単位の公開範囲はRLSで制御する。
- Pagesのブラウザへ`sb_secret_...`を渡さない。`SUPABASE_PUBLISHABLE_KEYS`には`sb_publishable_...`だけを設定し、secret keyはサーバー用途に限定する。
- MVPの読み取り対象は`public.games`、`public.teams`、`public.players`、`public.game_team_stats`、`public.player_game_stats`の5テーブルとする。
- 5テーブルは未認証ブラウザからSELECTだけを許可し、INSERT・UPDATE・DELETEは許可しない方針をIssueに記載した。
- データ投入、テーブル変更、live DBへのSQL適用は実行しない。IssueではDashboard確認、読み取り専用REST確認、公開サイト受入までを案内する。
- RLSとpublishable keyの関係、API keyの用途はSupabase公式ドキュメントを参照して記載した。

## 実行内容

1. `main`の作業ツリーがクリーンで、#56がOPEN、#58が未完了であることを確認した。
2. 公開URLをブラウザで検証し、Pages workflow成功後も`games`のREST応答が`200 []`であることを再現した。
3. Supabase公式ドキュメントでpublishable/secret key、RLS、Data APIの確認事項を確認した。
4. #56の最新情報を取得したうえで、#63「[DB][GitHub Pages] Supabase公開読み取り設定を整備する」を作成した。
5. GitHub APIのsub-issuesエンドポイントで#56→#63を登録し、#58と#63が子Issueとして返ることを確認した。
6. `scripts/dev/github_issue_status_policy.json`へ#63をP2、#56の子Issueとして追加した。
7. 本作業記録のMarkdownを作成し、Issue状況をGitHub APIから同期してHTMLを生成・検証する。

## #63に記載した工程

- 対象プロジェクトのProject URLとGitHub Secretの`SUPABASE_URL`を照合
- 5テーブルのデータ有無を読み取り専用で確認
- `public` schemaと5テーブルのData API公開対象を確認
- 5テーブルの未認証`anon` SELECTと書き込み拒否を確認・設定
- `SUPABASE_PUBLISHABLE_KEYS`へpublishable keyだけを設定し、secret keyをPagesから排除
- REST APIのHTTP status、空配列、必要テーブルの応答を確認
- Pages workflow再実行と、ログインなしの公開URLでのMVP受入
- 1280px/320px、画面遷移、コンソールエラー、失敗リクエストを確認

## 検証

- GitHub Pages workflow再実行: 成功（run 33070623791）
- 公開URLのHTTP status: 200
- Supabase REST接続: `games`はHTTP 200だが空配列。公開読み取り設定または接続先データの未成立を確認
- Issue #56のsub-issues: #58、#63を確認
- SQL実行・DB変更: 未実施
- 作業ツリー: ブランチ作成時点で変更なし

## 最終結果

- #56の子Issue [#63](https://github.com/tj-999-comp/B_Stats_Site/issues/63)を作成した。
- #63へ、Supabase Dashboardでの確認箇所、5テーブルの権限方針、キーの使い分け、REST確認、Pages受入の具体的な工程と完了条件を記載した。
- #56→#63の親子関係をGitHub APIへ登録した。
- 優先順位設定へ#63をP2として追加した。
- 未解決事項: Supabase側の設定適用と公開データの読み取り確認は、#63の手順に従って実施する必要がある。
- 次アクション: #63の設定完了後、Pages workflowを再実行し、#58の公開受入を再確認する。
- ブランチ: `agent/issue-63-supabase-public-read`
- commit: 作成後に追記
- PR: 作成後に追記

## GitHub Issue状況（2026-08-27時点の現在値）

確認日: 2026-08-27（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは10件だった。

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
#56（未完了・親Issue）
├── #58（未完了・子Issue）
└── #63（未完了・子Issue）
#57（未完了・親Issue）
└── #59（未完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P1 | [#56](https://github.com/tj-999-comp/B_Stats_Site/issues/56) [Web][GitHub Pages] 静的版の統計サイトを実装・公開する | 未完了 | Web導入のGitHub Pages親Issue。#58、#63を管理 |
| 2 | P1 | [#57](https://github.com/tj-999-comp/B_Stats_Site/issues/57) [Web][Vercel] SSR/ISR版の統計サイトを実装・公開する | 未完了 | Web導入のVercel親Issue。#59を管理。#58のデータ契約・共通UIを前提 |
| 3 | P2 | [#58](https://github.com/tj-999-comp/B_Stats_Site/issues/58) [Web][GitHub Pages] B1データを表示する静的サイトMVPを実装する | 未完了 | #56の子Issue。GitHub Pages版のMVP |
| 4 | P2 | [#59](https://github.com/tj-999-comp/B_Stats_Site/issues/59) [Web][Vercel] B1データを表示するSSR/ISR MVPを実装する | 未完了 | #57の子Issue。Vercel版のMVP。#58のデータ契約・共通UIを前提 |
| 5 | P2 | [#63](https://github.com/tj-999-comp/B_Stats_Site/issues/63) [DB][GitHub Pages] Supabase公開読み取り設定を整備する | 未完了 | #56の子Issue。#58の公開データ読み取り設定を前提 |
| 6 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 7 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 8 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 9 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 10 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
