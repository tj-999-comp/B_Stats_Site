# Scraper

BリーグのスタッツデータをスクレイピングしてSupabase PostgreSQLに保存するPythonパッケージ。

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

## ファイル構成

- `src/scraper.py` — メインスクレイパー（エントリーポイント）
- `src/parser.py` — HTMLパーサー（Bリーグサイトからデータ抽出）
- `src/db.py` — Supabaseへのデータ挿入処理
- `src/config.py` — 設定（URL、シーズンなど）

## GitHub Actionsでの自動実行

`.github/workflows/scrape.yml` により毎日自動実行されます。
Supabaseの接続情報はGitHub Secretsに設定してください：

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEYS`
