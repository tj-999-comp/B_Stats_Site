# 作業記録 021: Colab版スクレイパーのB2・B3対応
作成日: 2026-08-22

## 概要

GitHub Issue [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7)に関連して、`Colab/` の試合情報スクレイパーがB1だけでなくB2・B3も取得できるように整理・検証した。

Google Drive上のColab実行環境から、リーグを引数で指定して月単位または任意期間のJSONを保存できることを完了条件とした。既存のB1利用者の保存先・ファイル名は維持し、B2・B3ではリーグ識別用のプレフィックスを付ける仕様とした。

## 適用した役割

### 実際に担当したRole

- `Scraper maintenance`: 公式スケジュールAPIと試合詳細HTMLのリーグ別取得条件を整理
- `Validation`: B1、B2、B3の実データ取得結果とJSON内容を確認
- `Documentation`: ColabでのGoogle Drive運用、引数、出力ファイル命名を更新

## 主要な判断

- `--league {B1,B2,B3}` を追加し、既定値は従来互換のB1とする。
- B1の出力ファイル名は既存どおり `games_SEASON_DATE.json` または `games_SEASON_START_END.json` とする。
- B2・B3は `games_B2_SEASON_DATE.json`、`games_B3_SEASON_DATE.json` の形式で保存する。
- スケジュールAPIではリーグIDを、試合詳細ページではリーグ別タブを指定する。取得後に `ConventionTitleJ` も検証し、別リーグの試合をJSONへ混在させない。
- `Accept-Encoding` から`br`を外した。ローカルのHTTPクライアントがBrotli本文を復号できず、試合詳細HTMLをJSONとして解釈できないケースを避けるためである。
- 通常取得ではplay-by-playを扱わず、Supabaseへの投入も行わない。Colab版は取得したJSONの保存までを担当する。
- B3は対象期間に試合がないことがあるため、該当月の取得件数が0でも直ちに取得失敗とは判定しない。

## 最終結果

### 変更対象

- `Colab/bleague_parallel_scraper.py`
  - B1/B2/B3のリーグ指定
  - リーグ別スケジュール・試合詳細取得
  - リーグ別出力ファイル名
  - 出力先ディレクトリの自動作成
- `Colab/run_scrape_colab.py`
  - `--league` の受け取りとスクレイパーへの引き渡し
- `Colab/README.md`
  - Google Driveへ`Colab`フォルダだけを配置する構成と実行例
- `Colab/Colab_Scraping_Template.ipynb`
  - B1/B2/B3を指定するColab実行例

### 取得確認

次のJSONを生成し、取得結果を確認した。

| リーグ | 対象 | 結果 |
|---|---|---|
| B1 | 2018-10-06 | 9/9試合成功、ボックススコアあり |
| B2 | 2018-10-06 | 9/9試合成功、`ConventionTitleJ`は`2018-19 B2リーグ`、ボックススコアあり |
| B3 | 2018-11-03 | 1/1試合成功、`ConventionTitleJ`は`2018-19 B3レギュラーシーズン`、ボックススコアあり |
| B1 | 2018-10-21〜2018-10-25 | 19/19試合成功、全件B1 |
| B2 | 2018-10-21〜2018-10-25 | 25/25試合成功、失敗キーなし、全件B2 |
| B3 | 2018-11-03 | 1/1試合成功、失敗キーなし、全件B3 |

検証用JSONの主な保存先は次のとおりである。

- `/tmp/b2_b3_validation/games_2018-19_2018-10-06.json`
- `/tmp/b2_b3_validation/games_B2_2018-19_2018-10-06.json`
- `/tmp/b2_b3_validation/games_B3_2018-19_2018-11-03.json`
- `/tmp/b2_b3_test/games_2018-19_2018-10-21_2018-10-25.json`
- `/tmp/b2_b3_test/games_B2_2018-19_2018-10-21_2018-10-25.json`
- `/tmp/b2_b3_test/games_B3_2018-19_2018-11-03.json`

### Git・公開情報

実装変更は次のコミットで`main`へPush済みである。

- `7790327` `feat: support B2 and B3 Colab scraping`

- Draft PR [#43](https://github.com/tj-999-comp/B_Stats_Site/pull/43)

作業記録は当初記録専用ブランチへ追加したが、今回はユーザー指定の特例として、作業記録のコミットを`main`へ取り込み、直接Pushした。無関係な次の未追跡ファイルは変更・削除・コミットしない。

- `scraper/data/club_season_game_counts.csv`
- `scripts/dev/scrape_club_season_game_counts.py`

作業記録のmain反映コミットは次のとおりである。

- `0c87462` `docs: add work record 021 for Colab league scraping`
- `ad0629e` `docs: link work record 021 draft PR`

先に作成したDraft PR [#43](https://github.com/tj-999-comp/B_Stats_Site/pull/43)は、mainへ直接Pushする方針に変更したためクローズした。

## 検証

- B1、B2、B3の単日取得と期間取得を実行した。
- B2・B3のJSONでリーグ名、試合詳細、ボックススコア、失敗キーを確認した。
- `python3 -m py_compile`でColab用Pythonファイルの構文を確認した。
- `git diff --check`を実行した。
- DB変更操作、Supabaseへの投入、play-by-playの取得は行っていない。
- Google Drive上のファイルコピーやColabの実行環境自体は、ユーザーの運用環境で行う範囲であるため変更していない。

## 完了判定

B1の既存仕様を維持したまま、B2・B3の試合情報をリーグ混在なしで取得できることを確認した。B2・B3の出力ファイル名にもリーグプレフィックスが付くため、複数リーグ・複数月のJSONを同じ保存先で管理できる。

## GitHub Issue状況（2026-08-22時点の現在値）

確認日: 2026-08-22（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは7件だった。

### 親子関係

```text
#7（未完了・親Issue）
└── #8（完了・子Issue）
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
