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

### 補完候補の日付を一括取得

`game_supplement_candidates.csv`の候補を読み込み、同一日付をまとめて1回ずつ取得します。
候補40試合・38日付の場合でも、シェルからの実行は1回です。日付別JSONと実行結果の
`manifest.json`は`--output-dir`へ保存されます。

```bash
python -m scripts.scraping.scrape_candidate_dates \
  --input scraper/data/game_supplement_candidates.csv \
  --output-dir scraper/data/issue45_candidate_scrapes
```

取得前の候補確認だけを行う場合:

```bash
python -m scripts.scraping.scrape_candidate_dates \
  --input scraper/data/game_supplement_candidates.csv \
  --dry-run
```

既存の出力を明示的に再作成する場合だけ`--overwrite`を指定します。

### fallbackになった試合詳細の再取得

`fallback_html`になった試合は、追加タブを含めて再取得し、サマリーと両チームのboxscoreが
そろわなければ終了コード1で失敗扱いにします。通常の`game_detail`取得を置き換えず、結果は
指定した別JSONへ保存します。

```bash
python -m scripts.dev.refetch_game_detail \
  --schedule-key 1810 \
  --date 2018-01-01 \
  --season 2017-18 \
  --output /tmp/issue45_schedule_key_1810_retry.json
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

## players の監査とプロフィール差分補完

live DB と正本 `scraper/data/players.json` を直接同期する前に、全件スナップショットと
選手別差分を別ファイルへ出力します。

```bash
python -m scripts.dev.audit_players_snapshot \
  --local-input scraper/data/players.json \
  --snapshot-output /tmp/players_live_snapshot.json \
  --report /tmp/players_snapshot_audit.json
```

追跡済みゲームJSONから選手・スタッフ候補を分類し、分類レポートを補完監査へ渡します。
追跡済み試合に存在しないIDは自動除外しません。

```bash
python -m scripts.dev.classify_player_entities \
  --live-snapshot /tmp/players_live_snapshot.json \
  --report /tmp/player_entity_classification.json
```

公式 `roster_detail` の取得は、小さい対象と別レポートで先に確認します。
`--apply` を指定しない限りlive DBは更新されません。

```bash
python -m scripts.dev.fill_missing_player_profile_fields \
  --players-input /tmp/players_live_snapshot.json \
  --classification-report /tmp/player_entity_classification.json \
  --limit 5 \
  --workers 1 \
  --report /tmp/fill_player_profiles_preview.json
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

DDLは軽量版 `supabase/rebuild/01_base_schema.sql` を適用してください。
（`play_by_play` も含める場合のみ `supabase/rebuild/08_full_schema_with_events.sql` を使用）

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
| `scripts/dev/audit_players_snapshot.py` | **players差分監査**。live全件を別出力し、正本とのID・欠損・値差分を選手単位で記録する |
| `scripts/dev/classify_player_entities.py` | **選手分類**。全月次JSONの試合通算行を根拠にスタッフ候補とダミーIDを分離する |
| `scripts/dev/fill_missing_player_profile_fields.py` | **差分プロフィール補完**。取得結果と提案差分を選手単位で記録し、`--apply` 指定時だけ欠損列をDB更新する |
| `scripts/dev/build_players_canonical_candidate.py` | **正本候補生成**。監査済みlive、分類、補完提案を統合し、既存正本を上書きせず別JSONへ出力する |
| `scripts/dev/enrich_players_profile.py` | **正本JSONのプロフィール補完**。検証時は小さい `--limit` と別 `--output` を使用する |

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
| `scripts/dev/build_player_id_map.py` | 明示した旧PlayerIDとゲームJSONを照合し、新PlayerIDの候補CSVを生成する。同名選手による曖昧性も検出する |
| `scripts/dev/merge_player_ids.py` | `build_player_id_map.py` の確認済みCSVを使い、旧IDを新IDへ統合する（`players.json` 更新 & Supabase更新、ドライラン対応） |
| `scripts/delete_games_by_date.py` | 指定した日付範囲または schedule_key リストで Supabase から試合データを削除する（`games` / `game_team_stats` / `player_game_stats` / `play_by_play`、ドライラン対応） |
| `scripts/fix_game_datetimes.py` | エクスポートされたJSONの `GameDateTime` を `mapped_date`（スケジュール実際日付）で補正する。時刻は保持し、元値を `_original_GameDateTime` に記録する |
| `scripts/players_csv.py` | `players.json` ↔ CSV の相互変換ユーティリティ。編集用にJSONをエクスポートし、編集後にJSONへインポートする |

## GitHub Actionsでの自動実行

`.github/workflows/scrape.yml` により毎日自動実行されます。
Supabaseの接続情報はGitHub Secretsに設定してください：

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEYS`
