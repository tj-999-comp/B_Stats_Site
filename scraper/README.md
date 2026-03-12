# Scraper

BリーグのスタッツデータをスクレイピングしてSupabase PostgreSQLに保存するPythonパッケージ。

現在は、試合単位データ（Game + PlayByPlays）を優先して取得する。
ただしデフォルトではデータ量を抑えるため、`play_by_plays` 本体は保存・UPSERTしない。

## セットアップ

```bash
cd scraper

# 仮想環境の作成と有効化
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envを編集してSupabaseの接続情報を設定
```

> **注意**: 以下の実行コマンドはすべて **リポジトリルート**（`B_Stats_Site/`）から実行してください。
> `scraper/` の中にいる場合は `cd ..` で一段上に移動してから実行してください。

仮想環境を有効化した状態で以下のコマンドを実行してください。

## 実行

### 日付指定

```bash
# 特定の1日のみ取得
python -m scripts.scraping.scraper --date 2024-10-05

# シーズンを明示する場合
python -m scripts.scraping.scraper --date 2024-10-05 --season 2024-25
```

### 期間指定

```bash
# 開始日〜終了日の範囲を取得
python -m scripts.scraping.scraper --start-date 2024-10-05 --end-date 2024-10-11

# シーズンを明示する場合
python -m scripts.scraping.scraper --start-date 2024-10-05 --end-date 2024-10-11 --season 2024-25
```

### オプション

| オプション | 説明 |
|---|---|
| `--date YYYY-MM-DD` | 指定した1日分の試合データを取得 |
| `--start-date YYYY-MM-DD` | 期間指定の開始日（`--end-date` と併用） |
| `--end-date YYYY-MM-DD` | 期間指定の終了日（`--start-date` と併用） |
| `--season SEASON` | シーズン識別子（例: `2024-25`）。省略時は `config.py` の `SEASONS[0]` を使用 |
| `--include-play-by-play` | `play_by_plays` データも取得する（デフォルト: 無効） |
| `--max-retries N` | `game_detail` 取得時の最大リトライ回数（デフォルト: `3`） |

補足:
- `game_detail` の contexts は取得できるが `Game` が空のケースでは、最後に `game_detail` HTML のタイトルから `ScheduleKey / GameDateTime(日付のみ) / チーム名 / 大会名` を最小フォールバック抽出します。
- この場合、出力JSONの `games[].source_tab` は `fallback_html`、`games[].game.DataSource` は `html_fallback` になります。
- さらに日程トピックHTMLにスコアがあれば、`games[].game.HomeTeamScore / AwayTeamScore` を補完し、`games[].game.ScoreDataSource` に `schedule_topics_fallback` を設定します。

### `--retry-failed` 実行例（2018-01-01）

```bash
# 1810のみ再取得して既存JSONへマージ（この日付の実運用例）
python -m scripts.scraping.scraper \
  --retry-failed \
  --merge-into scraper/data/games_2017-18_2018-01-01.json \
  --failed-keys 1810 \
  --max-retries 8
```

期待される結果:
- `failed_after=0`
- `games[].source_tab` は `fallback_html`
- `games[].game.ScoreDataSource` は `schedule_topics_fallback`

## players.json の nationality / player_slot_category 補完

`scraper/data/players.json` の `player_id` を使って `roster_detail` を取得し、
「リーグ登録国籍」「出身地」から `nationality` と `player_slot_category` を更新します。

```bash
# 入力をそのまま上書き
python -m scripts.dev.enrich_players_profile --input scraper/data/players.json

# 出力先を分ける場合
python -m scripts.dev.enrich_players_profile --input scraper/data/players.json --output scraper/data/players_enriched.json
```

### 出力ファイル

取得結果は `scraper/data/` に JSON ファイルとして保存されます。

| 実行パターン | 出力ファイル名 |
|---|---|
| 日付指定 | `games_<season>_<date>.json` |
| 期間指定 | `games_<season>_<start>_<end>.json` |

各 JSON には以下のフィールドが含まれます：

- `game`: 試合ヘッダ情報（カード、スコア、クォーター得点など）
- `play_by_play_count`: その試合のプレー件数
- `play_by_plays`: デフォルトでは空配列（`--include-play-by-play` 指定時のみ保持）

## SupabaseへのUPSERT

DDLは軽量版 `docs/schema_draft_games_light.sql` を適用してください。
（`play_by_play` も含める場合のみ `docs/schema_draft_game_events.sql` を使用）

`game_team_stats` テーブルには、B.League Analytics のスタッツ用語集（1,2ページ）に対応した列を追加済みです。
取り込みスクリプトは `teams` / `games` / `game_team_stats` をデフォルトでUPSERTします。

適用後、以下で取り込みできます。

```bash
# 変換確認のみ（DB更新なし）
python -m scripts.db.upsert_games --dry-run

# 実際にUPSERT（デフォルト: teams / games / game_team_stats）
python -m scripts.db.upsert_games

# ファイルを明示する場合
python -m scripts.db.upsert_games --input scraper/data/games_2024-25_2024-10-05.json

# play_by_play も含める場合（任意）
python -m scripts.db.upsert_games --with-play-by-play
```

## ファイル構成と処理の流れ

### スクレイピングの全体フロー

```
scraper.py（エントリーポイント）
  │  CLI引数を解析して実行モードを決定
  │
  ├─ 日付指定の場合
  │    └─ game_scraper.py: save_date_range_games(date, date, season)
  │
  └─ 期間指定の場合
       └─ game_scraper.py: save_date_range_games(start, end, season)
                │
                ├─ BリーグスケジュールAPIに日付ごとにHTTPリクエスト
                │   → ScheduleKey（試合ID）の一覧を取得
                │
                ├─ 各 ScheduleKey に対して /game_detail/ を取得
                │   → HTML内の _contexts_s3id.data（JSON）を抽出
                │   → Game / Summaries / HomeBoxscores / AwayBoxscores / PlayByPlays を取得
                │
                └─ scraper/data/ に JSON ファイルとして保存

upsert_games.py（別コマンドとして独立実行）
  │  上記で生成した JSON を読み込む
  │
  ├─ チーム情報 (teams) を抽出
  ├─ 試合情報 (games) を抽出
  ├─ チーム別試合スタッツ (game_team_stats) を算出
  │   → eFG%, TS%, ORtg, DRtg, Pace など高度なスタッツも計算
  ├─ 選手情報 (players) を抽出
  ├─ 選手別試合スタッツ (player_game_stats) を抽出
  └─ db.py 経由で Supabase へ UPSERT
```

### 各ファイルの役割

#### スクレイピング実行系

| ファイル | 役割 |
|---|---|
| `scripts/scraping/scraper.py` | **エントリーポイント**。argparse で `--date` / `--start-date` / `--end-date` / `--season` / `--include-play-by-play` を受け取り、`game_scraper.py` の適切な関数を呼び出す |
| `scripts/scraping/parser.py` | **HTMLパーサー（選手・順位スタッツ用）**。`/stats/player` や `/standings/` ページを解析して選手スタッツ・順位表を取得する。試合単位スクレイピングとは独立した処理 |
| `scripts/scraping/game_scraper.py` | **スクレイピング本体**。日付→ScheduleKey の解決（スケジュールAPI）、ScheduleKey→試合詳細の取得（`/game_detail/` HTML内の `_contexts_s3id.data` を解析）、結果を JSON ファイルへ保存 |
| `scripts/db/upsert_games.py` | **DB取り込みコマンド**。`game_scraper.py` が出力した JSON を読み込み、`teams` / `games` / `game_team_stats` / `players` / `player_game_stats` / `play_by_play` へ変換・UPSERT する |
| `scripts/dev/enrich_players_profile.py` | **選手プロフィール補完**。選手プロフィールページをスクレイピングし、国籍・出身地から `nationality` と `player_slot_category` を補完・DB更新する |

#### 設定・基盤系

| ファイル | 役割 |
|---|---|
| `scripts/db/config.py` | **設定**。Supabaseの接続情報（環境変数から読み込み）、BASE_URL、リクエストヘッダ、対象シーズン（`SEASONS`）を定義する |
| `scripts/db/db.py` | **Supabase接続・UPSERT処理**。`supabase-py` クライアントの初期化と、テーブルごとの UPSERT 関数（1000件単位のチャンク処理）を提供する |

#### 開発・検証・デバッグ用

| ファイル | 役割 |
|---|---|
| `scripts/dev/inspect_full_context.py` | 指定した ScheduleKey の `/game_detail/` HTML から `_contexts_s3id.data` の全構造を取得・表示・保存する開発時の確認用ツール |
| `scripts/dev/inspect_player_data.py` | `game_scraper.fetch_game_context()` を呼び出し、返却されるデータ構造（Game・Summaries・Boxscoresなど）を確認する開発時の確認用ツール |
| `scripts/build_player_id_map.py` | `players.json` とゲームJSONを照合し、旧PlayerID → 新PlayerID のマッピング候補CSVを生成する。同名選手による曖昧性も検出する |
| `scripts/merge_player_ids.py` | `build_player_id_map.py` の出力CSVを使い、確認済みの旧IDを新IDへ統合する（`players.json` 更新 & Supabase更新、ドライラン対応） |
| `scripts/delete_games_by_date.py` | 指定した日付範囲または schedule_key リストで Supabase から試合データを削除する（`games` / `game_team_stats` / `player_game_stats` / `play_by_play`、ドライラン対応） |
| `scripts/fix_game_datetimes.py` | エクスポートされたJSONの `GameDateTime` を `mapped_date`（スケジュール実際日付）で補正する。時刻は保持し、元値を `_original_GameDateTime` に記録する |
| `scripts/players_csv.py` | `players.json` ↔ CSV の相互変換ユーティリティ。編集用にJSONをエクスポートし、編集後にJSONへインポートする |

## GitHub Actionsでの自動実行

`.github/workflows/scrape.yml` により毎日自動実行されます。
Supabaseの接続情報はGitHub Secretsに設定してください：

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEYS`
