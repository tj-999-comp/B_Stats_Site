# Changelog

## 2026-03-10

### 概要
Supabase 上で `games.game_type` の追加と全シーズン向け backfill を実施。テーブル定義ドキュメントに反映。

### 実施内容
- `games` テーブルに `game_type (text)` を追加
- `setu` ベースで全シーズン一括更新
  - `setu::integer <= 100` -> `RS`（Regular Season）
  - `setu::integer >= 101` -> `CS`（Championship Series）
- 必要時はシーズン指定 (`WHERE year = <season_start_year>`) で更新可能
- `player_game_stats.is_playing` を `play_time` ベースで全件更新
  - `play_time = 'DNP'` -> `false`
  - それ以外 -> `true`

### 反映ドキュメント
- `docs/table_definition.md`（`games.game_type` を追加）
- `docs/schema_draft_games_light.sql`（`games.game_type` を追加）
- `docs/flow.md`（`is_playing` 補正ロジックを追記）

## 2026-03-08

### 概要
スクレイパー・DBスキーマの大規模整備。`games` テーブルの `year` カラム定義変更、選手ID管理機能の追加、`players.json` の整備（nationality補完）、試合データの全削除＆再投入を実施。

---

### スキーマ変更

#### `games` テーブル
- **`year` カラムの定義変更**：暦年ではなく「シーズン開始年（Season Year）」を管理するよう変更。
  - 10〜12月の試合 → 当該年、1〜5月の試合 → 前年
  - 例: `2025-01-10` の試合は `year = 2024`（2024-25シーズン）
- **`game_type` カラムの追加**（`20260308c_add_game_type.sql`）：
  - `setu <= 100` → `RS`（レギュラーシーズン）
  - `setu >= 101` → `CS`（チャンピオンシップシリーズ）

#### `players` テーブル
- **`old_player_id` カラムの追加**（`20260308e_add_old_player_id_to_players.sql`）：PlayerID が変わった選手の旧IDを保持

#### `player_id_map` テーブルの新設（`20260308_player_id_aliases.sql`、`20260308b_rename_player_id_map.sql`）
- 選手のPlayerIDが変わったケースを管理するマッピングテーブル
- `old_player_id`（旧ID）→ `player_id`（現ID）

#### トリガー修正（`20260308d_fix_affiliation_trigger.sql`）
- `track_player_affiliation_from_game_stats` に時系列ガードを追加
- 過去データを逆順でUPSERTした際に `valid_to < valid_from` の制約違反が発生するバグを修正

---

### スクレイパー変更

#### `scripts/db/upsert_games.py`
- `_season_year_from_date()` 関数を追加：`game_date` からシーズン開始年を算出
- `_game_type()` 関数を追加：`setu` から `RS`/`CS` を判定
- `player_id_map` を参照して旧IDを新IDに読み替える処理を追加
- `PlayerID=None` のボックススコアレコードをスキップするよう修正（`str(None)='None'` バグ修正）
- `play_by_play` はデフォルト無効（データ量大・運用上非推奨）

#### `scripts/dev/enrich_players_profile.py`
- 404エラー時にクラッシュせずスキップするよう修正
- 503エラー時の指数バックオフリトライ追加（3s→6s→12s）
- `--force` オプション追加（デフォルトは `nationality=null` のみ処理）
- `--upsert` オプション追加（補完後にSupabaseへupsert）
- `--id-map` オプション追加（旧IDで取得）

#### `scripts/db/config.py`
- User-AgentをブラウザUAに変更（Botと判定されていた問題を修正）

#### `scripts/db/db.py`
- `fetch_player_id_map()` 追加：`player_id_map` テーブルから旧→新IDマップを取得
- `fetch_all_players()` 追加

---

### 新規スクリプト

| スクリプト | 用途 |
|---|---|
| `scraper/scripts/build_player_id_map.py` | 旧IDと新IDの照合CSV生成 |
| `scraper/scripts/merge_player_ids.py` | players.json更新 + DB統合 |
| `scraper/scripts/players_csv.py` | players.json ↔ CSV 双方向変換 |

---

### データ投入

試合データを全削除後、以下3シーズン分を再投入：

| シーズン | ファイル数 | 備考 |
|---|---|---|
| 2022-23 | 8 | 10月〜翌年5月 |
| 2023-24 | 8 | 10月〜翌年5月 |
| 2024-25 | 8 | 10月〜翌年5月 |

`players.json`（713人）の `nationality` / `player_slot_category` / `old_player_id` を整備しSupabaseへupsert。

---

### ドキュメント更新

- `docs/table_definition.md`：`year` カラムの説明をシーズン開始年に更新
- `docs/schema_draft_games_light.sql`：`year` カラムにコメント追加
- `docs/workflows.md`：`play_by_play` は運用上使用しない旨を追記
