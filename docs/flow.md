# スクレイピング〜DB Upsert〜正規化 フロー

スクレイピングからDBへのUpsert、各種正規化を行うまでの完全なフローをまとめる。

---

## PHASE 1: DBセットアップ（初回のみ）

初回セットアップは、統合SQLを1回実行する。

| ファイル | 内容 |
|---------|------|
| `supabase/rebuild/00_rebuild_all.sql` | 再構築SQL統合版（01〜07を順序込みで内包） |

```bash
# 代表例: 手動実行（1回）
psql $DATABASE_URL -f supabase/rebuild/00_rebuild_all.sql
```

---

## PHASE 2: スクレイピング〜Upsert（日次）

### ステップ 1: スクレイピング

**スクリプト:** `scripts/scraping/scraper.py` → `scripts/scraping/game_scraper.py`

- `/schedule/` API からスケジュール一覧（ScheduleKey）を取得
- 各ScheduleKeyに対して `/game_detail/` HTMLを取得・パース
- リクエスト間に 1〜3 秒のランダム待機（スロットリング）を挿入し、レートリミットを回避
- 5xx / 接続エラー時は Exponential Backoff（2秒 → 4秒）で最大3回リトライ
- 取得失敗 schedule_key のサマリーは `scraper/logs/game_detail_fetch_log.json` に記録される

```bash
python -m scripts.scraping.scraper --date YYYY-MM-DD
# または期間指定
python -m scripts.scraping.scraper --start-date YYYY-MM-DD --end-date YYYY-MM-DD --season 2024-25
```

#### 失敗分のみ再取得して月次JSONへマージ

スクレイピング後に失敗が残った場合、対象の月次JSONを指定して失敗分だけ再取得・上書きできる。

```bash
# ログから失敗キーを自動取得してマージ
python -m scripts.scraping.scraper \
  --retry-failed \
  --merge-into scraper/data/games_2024-25_2024-10-01_2024-10-31.json

# 失敗キーを手動指定してマージ
python -m scripts.scraping.scraper \
  --retry-failed \
  --merge-into scraper/data/games_2024-25_2024-10-01_2024-10-31.json \
  --failed-keys 502794,502813
```

- `--merge-into` のJSONに含まれる `season` / `start_date` / `end_date` を参照し、ログの最新 run から `failed_schedule_keys` を自動取得
- ログに該当 run がない場合は JSON 内の `failed_schedule_keys` をフォールバック利用
- 再取得した game は schedule_key 単位で既存データを置換（存在しないキーは末尾に追記）
- 再取得の失敗サマリーも `game_detail_fetch_log.json` に追記される

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

**game_team_stats.points の変換・検証:**

- `HomeTeamScore` / `AwayTeamScore` を各チームの最終得点として採用する
- 最終得点が欠損している場合だけ `2 × fg2m + 3 × fg3m + ftm` を使用する
- 最終得点とシュート式が不一致なら、いずれのテーブルもUpsertする前に処理を停止する
- `TeamPTR` はフィールドゴール成功率に相当し、`points` への変換や別カラムへの保存には使用しない
- 変換後の `points` を使ってTS%、ORtg、DRtg、得点比率、相手指標、接戦フラグなどを計算する

**points監査:**

- dry-runと通常実行のどちらでも、Upsert前に入力スコア・シュート式・変換後 `points` を照合する
- 変換行の欠落、余剰、重複も検出し、1件でも不整合があれば処理を停止する
- `points_validation` に監査行数、スコア欠損数、各不一致件数を表示する

**is_playing の補正ロジック（直接SQL更新時）:**
- `play_time = 'DNP'` → `false`
- それ以外 → `true`

**高度スタッツの計算式:**
- eFG% = (FGM + 0.5 × 3PM) / FGA
- TS% = Points / (2 × (FGA + 0.44 × FTA))
- ORtg = 100 × Points / Possession
- Pace = 40 × (Poss + OppPoss) / (2 × GameMinutes)

```bash
python -m scripts.db.upsert_games \
  --input scraper/data/season_YYYY-YYYY/games_SEASON_START_END.json \
  --dry-run

# points_validationの不一致件数がすべて0であることを確認してからUpsert
python -m scripts.db.upsert_games \
  --input scraper/data/season_YYYY-YYYY/games_SEASON_START_END.json
```

### 未投入データの追いつきフロー（2026-08-13時点）

通常の日次取得とは別に、2026年5月末までの未投入試合をまとめて追加する場合は、次の順序で進める。

1. [GitHub Issue #24](https://github.com/tj-999-comp/B_Stats_Site/issues/24)で、2026-05-31（JST）までの試合を対象に、DBの `schedule_key` と追跡済みJSONを照合する。未取得分をスクレイピングし、取得済み未投入分と合わせてdry-run、得点監査、失敗分の再取得を行った後、古い試合からDBへ投入する。
2. Issue #24の投入後検証が完了してから、子Issue [#25](https://github.com/tj-999-comp/B_Stats_Site/issues/25)を開始する。最新の試合データを根拠にplayer_idの重複を調査・統合し、その後に選手・スタッフ相当を再分類してプロフィール欠損を補完する。

Issue #25では、45848〜45865周辺を含む既存の [Issue #23](https://github.com/tj-999-comp/B_Stats_Site/issues/23) の調査結果を引き継ぐ。プロフィール補完をDBへ反映するときは、`supabase/patches/` に目視確認済みの入力を保存し、`supabase/sql/` の `backup → verify（前）→ fix → verify（後）` 4ファイル構成を使う。問題がある場合は `rollback → verify` で復旧する。

---

## PHASE 3: 正規化（必要な時）

### プレイヤーID名寄せ

シーズン中に player_id が変わる選手を同一人物としてマージする処理。

**スクリプト:** `scripts/dev/build_player_id_map.py` → 手動確認 → `scripts/dev/merge_player_ids.py`

```bash
# 1. マッピング候補を生成
python -m scripts.dev.build_player_id_map \
  --players scraper/data/players.json \
  --candidate-ids OLD_ID_1 OLD_ID_2 \
  --games 'scraper/data/season_*/games_*.json' \
  --output /tmp/player_id_map_candidates.csv

# 2. CSVを手動確認（status: ok / ambiguous / not_found）
#    status='ok' のみ残してマージ実行

# 3. マージ適用
python -m scripts.dev.merge_player_ids \
  --csv /tmp/player_id_map_candidates.csv \
  --yes
```

旧ID候補は事前調査で確定したIDを `--candidate-ids` へ明示する。
廃止済みの `nationality` など、プロフィールの欠損だけから旧IDを自動推測しない。

**対象テーブル:** players, player_game_stats, player_id_map

### プロフィール補完

**監査スクリプト:** `scripts/dev/audit_players_snapshot.py`

live DB の `players` をページングして全件取得し、正本
`scraper/data/players.json` とのID・欠損・値差分を確認する。出力は既定で
`/tmp` に作られ、正本とDBは変更しない。

```bash
python -m scripts.dev.audit_players_snapshot \
  --local-input scraper/data/players.json \
  --snapshot-output /tmp/players_live_snapshot.json \
  --report /tmp/players_snapshot_audit.json
```

**選手・スタッフ分類:** `scripts/dev/classify_player_entities.py`

追跡済みゲームJSONの試合通算行を全件調べる。`PeriodCategory == 18` であっても、
背番号、出場フラグ、先発フラグ、正の出場時間がすべてない行はスタッフ候補として
プロフィール補完と今後の投入から除外する。追跡済み試合に存在しないIDは自動除外しない。

```bash
python -m scripts.dev.classify_player_entities \
  --live-snapshot /tmp/players_live_snapshot.json \
  --local-input scraper/data/players.json \
  --report /tmp/player_entity_classification.json
```

**差分補完スクリプト:** `scripts/dev/fill_missing_player_profile_fields.py`

- `roster_detail` ページから国籍・出身地を取得
- `league_registered_nationality`（リーグ登録国籍）と `birthplace`（出身地）を保存
- 既存値は上書きせず、欠損列に実値を取得できた場合だけ差分を提案
- `player_slot_category` は `日本人選手`、`外国籍選手`、`帰化選手` の3値を正規値とし、未確認はNULLで保持する。投入層でも表記ゆれを正規化し、未知の非空値はエラーにする
- 選手別に取得成功、公式空欄、404、通信失敗、提案差分をJSONレポートへ記録

```bash
# 5件だけ取得し、DBを更新せず監査
python -m scripts.dev.fill_missing_player_profile_fields \
  --players-input /tmp/players_live_snapshot.json \
  --classification-report /tmp/player_entity_classification.json \
  --limit 5 \
  --workers 1 \
  --report /tmp/fill_player_profiles_preview.json

# 差分レポート、バックアップ、対象件数を確認後に限りDBへ反映
python -m scripts.dev.fill_missing_player_profile_fields \
  --classification-report /tmp/player_entity_classification.json \
  --apply \
  --report /tmp/fill_player_profiles_applied.json
```

`--apply` を指定しない限りlive DBは更新されない。全列のUPSERTが必要な場合は、
`scripts/dev/upsert_players_json.py` を実行する前にliveスキーマ、重複ID、
`last_seen_team_id` の参照整合性を個別に確認する。

正本候補は、監査済みliveスナップショットを基準に、分類レポートの除外IDと
プロフィール監査の提案差分だけを適用して `/tmp` へ生成する。既存の正本は上書きしない。

```bash
python -m scripts.dev.build_players_canonical_candidate \
  --live-snapshot /tmp/players_live_snapshot.json \
  --classification-report /tmp/player_entity_classification.json \
  --profile-audit /tmp/fill_player_profiles_audit.json \
  --output /tmp/players_canonical_candidate.json \
  --report /tmp/players_canonical_candidate_report.json
```

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `scripts/scraping/scraper.py` | CLIエントリポイント（通常・再取得モード） |
| `scripts/scraping/game_scraper.py` | スクレイピング・日付正規化・失敗分再取得マージ |
| `scraper/logs/game_detail_fetch_log.json` | 取得失敗サマリーログ（run単位） |
| `scraper/logs/schedule_fetch_log.json` | schedule API 失敗ログ |
| `scripts/db/upsert_games.py` | JSON変換・Upsert |
| `scripts/db/db.py` | Supabaseクライアント・チャンク処理 |
| `scripts/db/config.py` | 定数（SUPABASE_URL, SEASONS等） |
| `scripts/dev/audit_players_snapshot.py` | live playersスナップショットと正本の差分監査 |
| `scripts/dev/classify_player_entities.py` | 追跡済みゲームJSONによる選手・スタッフ候補分類 |
| `scripts/dev/fill_missing_player_profile_fields.py` | 欠損プロフィールの選手別監査・差分補完 |
| `scripts/dev/build_players_canonical_candidate.py` | 監査済み入力から上書きなしで正本候補を生成 |
| `scripts/dev/enrich_players_profile.py` | 正本JSONのプロフィール補完（出力先を分けて使用） |
| `scripts/dev/build_player_id_map.py` | 明示した旧IDの名寄せ候補生成 |
| `scripts/dev/merge_player_ids.py` | ID名寄せ適用 |
| `.github/workflows/scrape.yml` | 日次スクレイピング自動実行 |
| `.github/workflows/migrate.yml` | マイグレーション自動適用 |
