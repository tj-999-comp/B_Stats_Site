# 作業記録 028: Web導入親IssueとMVP子Issueの作成
作成日: 2026-08-27

## 概要

GitHub Pages版とVercel版のWeb導入を別々の親Issueとして整理し、それぞれにB1データを表示するMVP子Issueを作成する。

完了条件は、Pages親・Vercel親・各MVP子の4件をGitHubへ作成し、GitHub上のsub-issues APIで親子関係を登録すること、現行DBスキーマを前提にした対象範囲・完了条件・対象外を各Issueへ記載すること、作成後のオープンIssue状況を本作業記録へ同期することである。

対象Issue:

- [#56 GitHub Pages版の親Issue](https://github.com/tj-999-comp/B_Stats_Site/issues/56)
- [#57 Vercel版の親Issue](https://github.com/tj-999-comp/B_Stats_Site/issues/57)
- [#58 GitHub Pages版MVP子Issue](https://github.com/tj-999-comp/B_Stats_Site/issues/58)
- [#59 Vercel版MVP子Issue](https://github.com/tj-999-comp/B_Stats_Site/issues/59)

## 適用した役割

### 実際に担当したRole

- `Issue planning`: Web構成をGitHub PagesとVercelの親Issueへ分離し、各MVPの範囲と依存関係を定義
- `GitHub operation`: GitHub App tokenを使ったIssue作成、sub-issues関係登録、状態確認
- `Documentation`: 作成したIssue、優先順位、親子関係、次の着手条件を作業記録へ保存

## 主要な判断

- GitHub Pages版とVercel版は、計画上のPhase 3とPhase 4に対応するため、別の親Issueとして管理する。
- 各親Issueの最初の実装単位は、現在利用可能なB1データを読み取るMVP子Issueとする。B2・B3投入は既存の#44で扱う。
- MVPの表示範囲は、シーズン選択、試合一覧、試合詳細、チーム・選手スタッツ、基本ランキングとする。
- Pages版は`output: export`の制約とクライアント側認証チェック、Vercel版はSSR/ISRとMiddleware認証を完了条件に含める。
- 現行DBのRLS状態を確認せず、認証や公開範囲の安全性を断定しない。live DBのRLS変更とDB投入は今回のIssueの対象外とする。
- Web導入を#44より先に着手できるよう、Pages親・Vercel親をP1、各MVP子をP2として`github_issue_status_policy.json`へ追加する。

## 実行内容

1. `origin/main`を基準に専用ブランチ`agent/web-mvp-issues`を作成した。
2. GitHub Pages版の親Issue #56を作成した。
3. Vercel版の親Issue #57を作成した。
4. GitHub Pages版MVP子Issue #58を作成した。
5. Vercel版MVP子Issue #59を作成した。
6. GitHub APIのsub-issuesエンドポイントで、#56→#58、#57→#59を登録した。
7. 作成したIssueと親子関係をGitHub APIで再取得して確認した。

## 作成したIssue

| Issue | 区分 | 内容 |
|---:|---|---|
| [#56](https://github.com/tj-999-comp/B_Stats_Site/issues/56) | GitHub Pages親Issue | 静的版の統計サイトを実装・公開する |
| [#57](https://github.com/tj-999-comp/B_Stats_Site/issues/57) | Vercel親Issue | SSR/ISR版の統計サイトを実装・公開する |
| [#58](https://github.com/tj-999-comp/B_Stats_Site/issues/58) | #56の子Issue | B1データを表示する静的サイトMVPを実装する |
| [#59](https://github.com/tj-999-comp/B_Stats_Site/issues/59) | #57の子Issue | B1データを表示するSSR/ISR MVPを実装する |

## 検証

- GitHub App秘密鍵のKeychain項目確認: 成功
- GitHub App tokenによるGitHub API接続: 成功
- 親Issue #56のsub-issues取得結果: #58を確認
- 親Issue #57のsub-issues取得結果: #59を確認
- リポジトリ作業ツリー: Issue作成時点で変更なし

## 最終結果

- GitHub Pages版とVercel版を分離した親Issueを作成した。
- 各親IssueにB1データ表示MVPの子Issueを正式登録した。
- Issue本文へ現行DBテーブル、画面範囲、認証・公開条件、対象外、完了条件を記載した。
- 作業記録の優先順位設定へ#56〜#59を追加した。
- 未解決事項: Web実装、live DBのRLS確認、公開環境のデプロイ確認は各MVP・親Issueで実施する。
- 次アクション: まず#58のGitHub Pages版MVPへ着手し、現行DBの型・クエリと共通UIを整理する。その後#59へ展開する。

## GitHub Issue状況（2026-08-27時点の現在値）

確認日: 2026-08-27（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは9件だった。

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
└── #58（未完了・子Issue）
#57（未完了・親Issue）
└── #59（未完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P1 | [#56](https://github.com/tj-999-comp/B_Stats_Site/issues/56) [Web][GitHub Pages] 静的版の統計サイトを実装・公開する | 未完了 | Web導入のGitHub Pages親Issue。#58を管理 |
| 2 | P1 | [#57](https://github.com/tj-999-comp/B_Stats_Site/issues/57) [Web][Vercel] SSR/ISR版の統計サイトを実装・公開する | 未完了 | Web導入のVercel親Issue。#59を管理。#58のデータ契約・共通UIを前提 |
| 3 | P2 | [#58](https://github.com/tj-999-comp/B_Stats_Site/issues/58) [Web][GitHub Pages] B1データを表示する静的サイトMVPを実装する | 未完了 | #56の子Issue。GitHub Pages版のMVP |
| 4 | P2 | [#59](https://github.com/tj-999-comp/B_Stats_Site/issues/59) [Web][Vercel] B1データを表示するSSR/ISR MVPを実装する | 未完了 | #57の子Issue。Vercel版のMVP。#58のデータ契約・共通UIを前提 |
| 5 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 6 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 7 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 8 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 9 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
