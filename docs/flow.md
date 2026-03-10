# スクレイピング〜DB Upsert〜正規化 フロー

スクレイピングからDBへのUpsert、各種正規化を行うまでの完全なフローをまとめる。

---

## PHASE 1: DBセットアップ（初回のみ）

マイグレーションを以下の順番で適用する。

| ファイル | 内容 |
|---------|------|
| `20260221_init.sql` | テーブル作成（teams, games, players, game_team_stats, player_game_stats） |
| `20260224_identity_history.sql` | player_name_history, player_affiliations, トリガー設定 |
| `20260303_add_game_datetime.sql` | games に game_datetime カラム追加 |
| `20260303_add_game_date.sql` | games に game_date カラム追加 |
| `20260306_add_players_nationality.sql` | players に nationality, player_slot_category カラム追加 |
| `20260308_player_id_aliases.sql` | player_id_map テーブル作成 |
| `20260308b_rename_player_id_map.sql` | FK カスケード設定 |
| `20260308c_add_game_type.sql` | games に game_type カラム追加（RS / CS） |
| `20260308d_fix_affiliation_trigger.sql` | affiliationトリガー修正 |
| `20260308e_add_old_player_id_to_players.sql` | players に old_player_id カラム追加 |

```bash
# 適用コマンド例（migrate.yml ワークフロー、または手動実行）
psql $DATABASE_URL -f supabase/migrations/20260221_init.sql
# ...以降も同様に順番通りに適用
```

---

## PHASE 2: スクレイピング〜Upsert（日次）

### ステップ 1: スクレイピング

**スクリプト:** `scripts/scraping/scraper.py` → `scripts/scraping/game_scraper.py`

- `/schedule/` API からスケジュール一覧（ScheduleKey）を取得
- 各ScheduleKeyに対して `/game_detail/` HTMLを取得・パース

```bash
python -m scripts.scraping.scraper --date YYYY-MM-DD
# または --season 2024-25 で全シーズン指定
```

### ステップ 2: 年・日付の正規化（`game_scraper.py` 内で自動処理）

- UnixタイムスタンプをGameDateTimeに変換
- シーズン年度の計算（Oct〜Dec → 当年、Jan〜May → 前年）
  - 例: 2024-10-15 → 2024、2025-01-10 → 2024

### ステップ 3: JSONファイルに保存

**出力:** `games_{season}_{date}.json`

- `game_scraper.py` がスクレイピング結果をJSONとしてローカルに保存

### ステップ 4: 変換 & Upsert

**スクリプト:** `scripts/db/upsert_games.py`

JSONを読み込み、各テーブル向けのデータに変換してDBにUpsertする（変換とUpsertは一体）。

| 対象テーブル | conflict key |
|------------|-------------|
| teams | team_id |
| games | schedule_key |
| game_team_stats | schedule_key + team_id |
| players | player_id |
| player_game_stats | schedule_key + player_id |

**game_type の判定ロジック:**
- `setu <= 100` → `'RS'`（レギュラーシーズン）
- `setu >= 101` → `'CS'`（チャンピオンシップシリーズ）

**is_playing の補正ロジック（直接SQL更新時）:**
- `play_time = 'DNP'` → `false`
- それ以外 → `true`

**高度スタッツの計算式:**
- eFG% = (FGM + 0.5 × 3PM) / FGA
- TS% = Points / (2 × (FGA + 0.44 × FTA))
- ORtg = 100 × Points / Possession
- Pace = 40 × (Poss + OppPoss) / (2 × GameMinutes)

```bash
python -m scripts.db.upsert_games
```

---

## PHASE 3: 正規化（必要な時）

### プレイヤーID名寄せ

シーズン中に player_id が変わる選手を同一人物としてマージする処理。

**スクリプト:** `scraper/scripts/build_player_id_map.py` → 手動確認 → `scraper/scripts/merge_player_ids.py`

```bash
# 1. マッピング候補を生成
python -m scraper.scripts.build_player_id_map \
  --players players.json \
  --games games_*.json \
  --output player_id_map_candidates.csv

# 2. CSVを手動確認（status: ok / ambiguous / not_found）
#    status='ok' のみ残してマージ実行

# 3. マージ適用
python -m scraper.scripts.merge_player_ids \
  --csv player_id_map_candidates.csv \
  --yes
```

**対象テーブル:** players, player_game_stats, player_id_map

### プロフィール補完

**スクリプト:** `scripts/dev/enrich_players_profile.py`

- `roster_detail` ページから国籍・出身地を取得
- `nationality`（日本 or 外国）、`player_slot_category`（日本人選手 / 外国籍選手）を更新

```bash
python -m scripts.dev.enrich_players_profile --input players.json --upsert
```

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `scripts/scraping/scraper.py` | CLIエントリポイント |
| `scripts/scraping/game_scraper.py` | スクレイピング・日付正規化 |
| `scripts/db/upsert_games.py` | JSON変換・Upsert |
| `scripts/db/db.py` | Supabaseクライアント・チャンク処理 |
| `scripts/db/config.py` | 定数（SUPABASE_URL, SEASONS等） |
| `scripts/dev/enrich_players_profile.py` | プロフィール補完 |
| `scraper/scripts/build_player_id_map.py` | ID名寄せ候補生成 |
| `scraper/scripts/merge_player_ids.py` | ID名寄せ適用 |
| `.github/workflows/scrape.yml` | 日次スクレイピング自動実行 |
| `.github/workflows/migrate.yml` | マイグレーション自動適用 |
