# 作業記録 023: 欠落B1試合40件の取得と月次JSON統合
作成日: 2026-08-24

## 概要

GitHub Issue [#45](https://github.com/tj-999-comp/B_Stats_Site/issues/45)で、`scraper/data/game_supplement_candidates.csv`に確定したB1の補完候補40試合を、公式スケジュールと試合詳細から取得して既存の月次JSONへ統合した。

候補は38日付にまとまるため、候補CSVを入力に日付単位で取得するCLIを追加した。取得結果から候補の対戦カードだけを抽出し、40試合すべてが月次JSONに各1件ずつ存在することを確認した。39試合はチームIDで一致し、公式Box Scoreが存在しない`ScheduleKey=1810`だけはチーム名の別名照合で特定して、ユーザー判断によりヘッダ情報のみを保存した。

## 適用した役割

### 実際に担当したRole

- `Data extraction`: 候補CSVを38日付へ集約し、公式スケジュールと試合詳細を取得
- `Data integration`: チームIDを優先し、ヘッダ情報だけの1試合はチーム名の別名で対象40試合を特定して既存の月次JSONへ統合
- `Data validation`: schedule_key、開催日、対戦チーム、詳細情報の有無を候補全件で検証
- `Documentation`: 実行方法、例外処理、次のUpsert作業の入力範囲を記録

## 主要な判断

- 38回の手作業実行を避けるため、`scripts/scraping/scrape_candidate_dates.py`で候補CSVから日付を重複排除し、一度の実行で取得する方式にした。
- 取得日には対象外の試合も含まれるため、統合時は候補CSVの2チームの`team_id`組み合わせが一致する試合を優先して採用する。チームIDが存在しない公式ヘッダだけは、明示したチーム名の別名照合を許容する。
- `ScheduleKey=3130`はシーズンと開催日を`2018-19` / `2018-11-18`として扱い、`GameDateTime`も同日の値へ補正した。
- `ScheduleKey=7440`と`500017`は9月の月次JSONが存在しなかったため、既存命名規則に合わせた9月ファイルを新規作成した。
- 2022-10-23の対象は富山対群馬（`ScheduleKey=500080`）へ訂正して統合した。
- `ScheduleKey=1810`は公式サイトにBox Scoreが残っておらず、再取得しても詳細を取得できなかったため、ヘッダ情報のみを許容した。
- Supabaseへの変換・Upsertは実施しない。取得済みJSONを入力とするDB反映は子Issue [#46](https://github.com/tj-999-comp/B_Stats_Site/issues/46)で扱う。

## 最終結果

### 取得・統合結果

| 項目 | 結果 |
|---|---:|
| 補完候補試合 | 40件 |
| 取得対象日 | 38日 |
| 対戦カードを統合できた試合 | 40件 |
| チームID一致で特定した試合 | 39件 |
| チーム名の別名照合で特定した試合 | 1件（`ScheduleKey=1810`） |
| 試合詳細を含む試合 | 39件 |
| ヘッダ情報のみの試合 | 1件（`ScheduleKey=1810`） |
| 更新した既存月次JSON | 20ファイル |
| 新規作成した月次JSON | 2ファイル |

新規作成した月次JSONは次の2ファイルである。

- `scraper/data/season_2021-2022/games_2021-22_2021-09-01_2021-09-30.json`（`ScheduleKey=7440`）
- `scraper/data/season_2022-2023/games_2022-23_2022-09-01_2022-09-30.json`（`ScheduleKey=500017`）

### 変更ファイル

- `scraper/data/game_supplement_candidates.csv`
  - 40件の候補を正規化し、`2018-11-18`、2022-10-23の富山対群馬、2024-10-26の仙台対越谷を反映
- `scripts/scraping/scrape_candidate_dates.py`
  - 候補CSVから日付別の取得を一括実行し、取得結果を日付JSONへ出力するCLIを追加
- `scripts/dev/merge_candidate_games.py`
  - チームID一致を優先し、公式ヘッダだけの例外にはチーム名の別名照合を用いて月次JSONへ統合する。不足月次JSONの作成、詳細未取得時の明示的許容、バックアップ作成を行うCLIを追加
- `scripts/dev/refetch_game_detail.py`
  - 特定`ScheduleKey`の試合詳細をタブ候補付きで再取得するCLIを追加
- `scripts/scraping/game_scraper.py`
  - 試合詳細取得でタブ候補を指定できるようにした
- `scraper/README.md`
  - 一括取得、統合、個別再取得の実行手順を追記
- `config/github_app.example.json`、`config/README.md`、`scripts/dev/github_app_token.py`
  - GitHub Appのローカル設定テンプレート、macOS KeychainからのInstallation token発行、設定確認手順を追加
- `.gitignore`、`requirements.txt`、`scraper/requirements.txt`、`docs/PORTFOLIO_STANDARD.md`
  - 実設定のGit管理除外、JWT依存、テンプレートを使う認証手順を追加
- `scraper/data/season_*/games_*.json`
  - 対象40試合を22個の月次JSONへ統合

統合後、日付別に取得した38個の生JSONはユーザー指示により削除した。統合前の既存月次JSON 20ファイルは`/tmp/issue45_merge_backup_20260824`へ退避した。

### 確認結果

- 候補40件すべてについて、対象の`ScheduleKey`が月次JSON内に1件だけ存在することを確認した。
- 39試合は候補CSVのシーズン、開催日、2チームの`team_id`組み合わせと統合済みJSONが一致することを確認した。`ScheduleKey=1810`はヘッダにチームIDが無いため、A東京・千葉の対戦カードをチーム名の別名で照合した。
- `ScheduleKey=3130`の`GameDateTime`が2018-11-18（JST）へ補正されていることを確認した。
- `ScheduleKey=1810`以外の39試合は試合詳細を含むことを確認した。
- `ScheduleKey=1810`はヘッダ情報を保存し、再取得結果としてBox Score由来の詳細がないことを確認した。

### Git・PR

- 作業ブランチ: `agent/issue-45-scrape-missing-b1-games`
- コミット: Draft PR作成後に追記
- Draft PR: 作成後に追記
- `main`への直接Push、Supabaseへの接続・変換・Upsertは行っていない。

## 検証

- `scripts/scraping/game_scraper.py`、一括取得CLI、個別再取得CLI、統合CLIのPython構文を確認した。
- 候補CSVを入力に、40候補、38日付であることを確認した。
- 統合後の22月次JSONに対して、候補40件の一意性、開催日、対戦チーム、`GameDateTime`補正を確認した。
- GitHub App設定テンプレートの有効な構成と、テンプレート値が残る構成の拒否を確認した。macOS Keychainからの秘密鍵取得、`tj-999-comp/B_Stats_Site`へのInstallation token発行、リポジトリ読み取りを確認した。
- `git diff --check`を実行した。

## 未完了事項と次アクション

- #45の取得・JSON統合は完了とする。レビュー・マージ後にIssueをクローズする。
- GitHub Appは既存の4項目設定（`app_id`、`client_id`、`repository`、`keychain_service`）で確認済み。`installation_id`は不要で、対象リポジトリから自動解決する。
- #46ではこの40試合を入力に、dry-run変換、対象件数確認、DB変更用のbackup・verify・fix・rollback一式の作成とレビューを行う。
- `ScheduleKey=1810`は公式Box Scoreが公開されない限り、ヘッダ情報のみの記録として扱う。

## GitHub Issue状況（2026-08-24時点の現在値）

確認日: 2026-08-24（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは10件だった。

### 親子関係

```text
#7（未完了・親Issue）
├── #8（完了・子Issue）
├── #45（未完了・子Issue）
└── #46（未完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（完了・子Issue）
└── #23（完了・子Issue）
#24（完了・親Issue）
└── #25（完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 2 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 3 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 4 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 5 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 6 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 7 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
| 8 | P3 | [#44](https://github.com/tj-999-comp/B_Stats_Site/issues/44) [DB] live DBへB2・B3スタッツを追加する | 未完了 | 独立。優先度未設定 |
| 9 | P3 | [#45](https://github.com/tj-999-comp/B_Stats_Site/issues/45) [Scraping] 特定済みの欠落B1試合をスクレイピングする | 未完了 | #7の子Issue。#7完了後 |
| 10 | P3 | [#46](https://github.com/tj-999-comp/B_Stats_Site/issues/46) [DB] 特定済みの欠落B1試合をUpsertする | 未完了 | #7の子Issue。#7完了後 |
