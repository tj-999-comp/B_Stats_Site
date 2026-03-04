## 概要

作成日: 2026-03-04

このレポートは、スクレイパーで収集した `games_2024-25_2025-01-01_2025-02-28.json` の試合日付がSupabaseへアップサートされる際に「2026年」として登録される現象についての調査結果をまとめたものです。

**短い結論**: サイトの生レスポンス（`game_detail` の contexts JSON）が `ymd` / `GameDateTime` を 2026 年の日付で返しており、スクレイパーはその値をそのまま JSON に保存・DB に書き込んでいるため、DB に 2026 年として登録されています。Supabase 側の誤りではありません。

## 再現手順（調査で行ったこと）

- 対象ファイル: [B_Stats_Site/scraper/data/games_2024-25_2025-01-01_2025-02-28.json](B_Stats_Site/scraper/data/games_2024-25_2025-01-01_2025-02-28.json)
- スクレイパーの抽出処理: `scraper/src/game_scraper.py`（`_extract_context_data` / `scrape_date_range_games`）
- アップサート処理: `scraper/src/upsert_games.py`（`_extract_games` と `_unix_to_jst_date`）
- 生レスポンス取得と contexts 抽出はローカル環境から実際に `https://www.bleague.jp/game_detail/` を `ScheduleKey` 指定で照会して確認。

実行したスクリプトはリポジトリに保存されており、全 149 件の `schedule_key` について contexts を照会した結果を次のログに出力しています:

- [B_Stats_Site/scraper/logs/contexts_scan.json](B_Stats_Site/scraper/logs/contexts_scan.json)

## 証拠

- 元 JSON の `date_to_schedule_keys` は 2025 年の日付（例: `"2025-01-03"` に `schedule_key` が属する）を示しているが、各 `schedule_key` を `game_detail` で照会すると contexts の `ymd` が `2026-01-03` のように 2026 年を返す。例:
  - `schedule_key=505116` → `date_to_schedule_keys` では `2025-01-01` に含まれるが、contexts の `ymd` は `2026-01-03`、`GameDateTime` 生値 `1767416400` → JST `2026-01-03T14:00:00+09:00`。
- サンプリング／フル走査結果: 149 件中 149 件が contexts の `ymd` を 2026 年として返していた。

（ログ・出力ファイル）
- スキャン結果: [B_Stats_Site/scraper/logs/contexts_scan.json](B_Stats_Site/scraper/logs/contexts_scan.json)
- 調査に使用したデータ: [B_Stats_Site/scraper/data/games_2024-25_2025-01-01_2025-02-28.json](B_Stats_Site/scraper/data/games_2024-25_2025-01-01_2025-02-28.json)

## 原因分析

1. スクレイピング元ページの構造
   - `game_detail` ページ内に埋め込まれた JavaScript の contexts（`_contexts_s3id.data`）内の `Game` オブジェクトに `GameDateTime`（Unix 秒）が含まれている。
2. サイト側の値
   - 上記 `GameDateTime` は Unix 秒であり、JST に変換すると 2026 年の日時になる（例を参照）。
3. スクレイパーの動作
   - スクレイパーは contexts から取得した `GameDateTime` をそのまま JSON に格納し、`upsert_games` の `_unix_to_jst_date` がその Unix 秒を JST 日付に変換して DB に格納する。
4. したがって発生源は「サイト側の contexts が 2026 年の日付を返している」ことにある。考えられる理由は次の通り:
   - サイト側が `ymd` と `date_to_schedule_keys` の対応を更新した（公開カレンダーと内部コンテキストの非整合）。
   - サイト側で `GameDateTime` を返すロジックがサーバー側のタイムゾーンや年オフセット等で変更された。
   - あるいは `date_to_schedule_keys` を生成したスクレイピング側コード（別処理）が古い日付（2025）でマップを作成している可能性もあるが、今回確認したファイルの `generated_at` は 2026-03-03 であり、ファイルはスクレイパーで生成されたもののように見える（ただし `date_to_schedule_keys` は 2025 範囲）。

## 影響範囲

- 現在のデータセット（該当 JSON 範囲）に含まれる全 149 件の試合が contexts 側で 2026 年の日付を返しているため、`games` テーブルに登録される `game_datetime` / `game_date` は 2026 年として記録されます。
- これによりシーズン・期間フィルタや日付に依存する分析・表示が誤った年に対して行われる可能性があります。

## 推奨対応（短期・長期）

短期（すぐできる、安全な対処）

- スクレイパー側でフォールバックを追加: 出力時に contexts 内の `GameDateTime` を使う前に、元 JSON の `date_to_schedule_keys` マップ（scrape の段階で保持されている）を参照して、その `schedule_key` がどのカレンダー日 (`YYYY-MM-DD`) に割り当てられているかを優先値として使う。両者が不一致の場合は警告ログを出す。
  - 実装箇所: `scraper/src/upsert_games.py` の `_extract_games`（`game_datetime_unix` / `game_datetime` の決定処理）にフォールバックを入れる。

中長期（根本対処）

- サイト側に問い合わせ: contexts の `ymd` / `GameDateTime` が 2026 年を返す意図があるか、あるいは内部データの取り違いが生じていないか確認する。問い合わせには本レポートのサンプル（例: `schedule_key=505116` 等）と、我々の `date_to_schedule_keys` マップとの不整合を添える。
- サイトが仕様変更を行っている場合はスクレイパーを仕様に合わせて更新。サイトがバグであれば修正後にスクレイパーを再実行して正規データを取得する。

## 参考（再現コマンド）

調査で使用した簡易スクリプトはリポジトリ内に残しており、全 schedule_key を走査して contexts を保存しています。ログ: [B_Stats_Site/scraper/logs/contexts_scan.json](B_Stats_Site/scraper/logs/contexts_scan.json)

最低限の再現コマンド（ローカル環境）:

```bash
source .venv/bin/activate
python -c "from datetime import timezone,timedelta,datetime; print(datetime.fromtimestamp(1767416400,tz=timezone(timedelta(hours=9))).isoformat())"
```

## 次のアクション提案

1. まずサイト運営に問い合わせ（本レポートと `contexts_scan.json` を添付）。
2. 問い合わせの回答を待つ間、スクレイパーにフォールバック（`date_to_schedule_keys` 優先）を実装してデータの一貫性を保つ。

---
レポートを保存しました: [B_Stats_Site/scraper/docs/contexts_date_mismatch_report.md](B_Stats_Site/scraper/docs/contexts_date_mismatch_report.md)
