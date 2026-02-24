# Scraper

BリーグのスタッツデータをスクレイピングしてSupabase PostgreSQLに保存するPythonパッケージ。

現在は、試合単位データ（Game + PlayByPlays）を優先して取得する。
ただしデフォルトではデータ量を抑えるため、`play_by_plays` 本体は保存・UPSERTしない。

## セットアップ

```bash
cd scraper
cp .env.example .env
# .envを編集してSupabaseの接続情報を設定
pip install -r requirements.txt
```

## 実行

```bash
python -m scraper.src.scraper
```

実行すると、指定シーズンの開幕日を自動特定し、開幕1週間分の試合データを
`scraper/data/games_<season>_opening_week.json` に出力します。

- `game`: 試合ヘッダ情報（カード、スコア、クォーター得点など）
- `play_by_play_count`: その試合のプレー件数
- `play_by_plays`: デフォルトでは空配列（必要時のみオプションで保持）

## SupabaseへのUPSERT

DDLは軽量版 `docs/schema_draft_games_light.sql` を適用してください。
（`play_by_play` も含める場合のみ `docs/schema_draft_game_events.sql` を使用）

`game_team_stats` テーブルには、B.League Analytics のスタッツ用語集（1,2ページ）に対応した列を追加済みです。
取り込みスクリプトは `teams` / `games` / `game_team_stats` をデフォルトでUPSERTします。

適用後、以下で取り込みできます。

```bash
# 変換確認のみ（DB更新なし）
python -m scraper.src.upsert_games --dry-run

# 実際にUPSERT（デフォルト: teams / games / game_team_stats）
python -m scraper.src.upsert_games

# ファイルを明示する場合
python -m scraper.src.upsert_games --input scraper/data/games_2024-25_opening_week.json

# play_by_play も含める場合（任意）
python -m scraper.src.upsert_games --with-play-by-play
```

## ファイル構成

- `src/scraper.py` — メインスクレイパー（エントリーポイント）
- `src/game_scraper.py` — 試合単位データ取得（開幕週）
- `src/upsert_games.py` — JSONからteams/games/play_by_playへのUPSERT
- `src/config.py` — 設定（URL、シーズンなど）

## GitHub Actionsでの自動実行

`.github/workflows/scrape.yml` により毎日自動実行されます。
Supabaseの接続情報はGitHub Secretsに設定してください：

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEYS`
