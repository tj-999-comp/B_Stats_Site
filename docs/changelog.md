# Changelog

## 2026-08-05

### Issue #11: game_team_statsの得点誤マッピング補正完了

- `scripts/db/upsert_games.py` が `TeamPTR` を `game_team_stats.points` に保存していた誤マッピングを修正
- `HomeTeamScore` / `AwayTeamScore` を得点の正本とし、欠損時だけ `2 × fg2m + 3 × fg3m + ftm` へフォールバックするよう変更
- 試合スコアとシュート式が不一致の場合、および変換後pointsの不一致・欠落・余剰・重複を検出した場合はUpsert前に停止する監査を追加
- 追跡済み全74月次JSONをdry-runし、サマリーを持つ5,423試合・10,846チーム行で得点関連の不一致0件を確認
- live DBの10,846行について、`points` と得点依存22列の計23列をバックアップ付きデータパッチで補正
- live DB適用後、試合・チームペア、基礎値、試合スコア、シュート式、PFT復元値、得点依存22列を全件監査し、すべて不整合0件を確認
- canonical rebuild SQL、投入フロー、SQL運用READMEを同期し、詳細を `issues/Issue_ex_006.md` に記録
- JSON、DBカラム、`games`、`player_game_stats.points` は変更対象外

## 2026-08-04

### Issue #10: 2021-22シーズンの試合日時補正完了

- 2022年1月〜4月を再取得し、追跡済み月次JSON 4ファイルを正しい日時へ更新
- 対象303件のschedule_key、対戦、スコア、boxscoreが旧JSONと一致することを確認
- `games` だけを更新する件数ガード・バックアップ付きデータパッチSQLとロールバックSQLを追加
- トランザクションプーラー経由でも一時テーブルのセッション切替に依存しないよう、更新・復旧本体をそれぞれ単一の `DO` 文として実装
- live DBへパッチを適用し、`year = 2020 AND season = '2021-22'` の303件が解消されたことを確認
- 適用後の `year = 2021 AND season = '2021-22'` は618件（既存315件 + 補正303件）
- 調査、再取得、比較、SQL適用、最終確認の詳細を `issues/Issue_ex_005.md` に記録
- 一回限りの運用SQLを `supabase/sql/` に集約し、`YYYYMMDD_<action>_<target>.sql` の命名規則を追加

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
- `supabase/rebuild/01_base_schema.sql`（`games.game_type` を追加）
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
- `supabase/rebuild/01_base_schema.sql`：`year` カラムにコメント追加
- `docs/workflows.md`：`play_by_play` は運用上使用しない旨を追記
