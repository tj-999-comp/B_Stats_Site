# 作業記録 011: Issue #24 試合データ取得・Live DB投入
作成日: 2026-08-18

## 目的

GitHub Issue #24の対象である、2026-05-31（JST）までの未投入試合データを取得し、Live DBへ投入する。

## 対象と入力

- 2025-05-18の未取得試合: `schedule_key=503896`
- 2025-26シーズン: 2025年10月〜2026年5月の月次JSON 8ファイル
- 保存先: `scraper/data/season_2025-2026/`
- `play_by_play` は取得・投入しない。

## 実行結果

- `schedule_key=503896` を再取得し、2024-25年5月JSONへ反映した。
- 2025-26シーズンの10月、11月、12月、2026年1月、2月、3月、4月、5月を月順に取得した。
- ユーザー環境のPython 3.11仮想環境で、古い月から順にLive DBへUPSERTした。
- GitHub Issue #24へ実施結果をコメントした。

## 実行上の問題と対応

Codexの既定サンドボックスでは外部ネットワークが無効だったため、B.LEAGUEのスケジュールAPIでDNS解決に失敗した。スクレイパーはこの失敗を空のスケジュールとして扱い、`game_count=0` のJSONを保存していた。

空JSONをUPSERTしても更新件数が0件になることを確認した後、ユーザーのネットワーク接続可能なローカル環境で再取得し、その結果をLive DBへ投入した。

## 残件

- Live DB上で、試合・チーム・選手試合成績・チーム試合成績の件数、抜け漏れ、重複、参照整合性を確認する。
- Issue #24の確認結果を踏まえ、子Issue #25（player_id重複整理・プロフィール欠損補完）へ引き継ぐ。

## 関連ファイル

- `scraper/data/season_2024-2025/games_2024-25_2025-05-01_2025-05-31.json`
- `scraper/data/season_2025-2026/`
- `scraper/logs/game_detail_fetch_log.json`
- `scraper/logs/schedule_fetch_log.json`
