# Issue_ex_003: プロフィール項目（リーグ登録国籍・出身地）取得とUpsert準備
作成日: 2026-05-26

## 背景
- `players.json` のプロフィール補完で、`league_registered_nationality` と `birthplace` を保持したい。
- 取得済みデータをそのまま `players` テーブルへ反映できる運用を追加したい。

## 対応内容
1. 取得ロジック強化
- `scripts/dev/enrich_players_profile.py` を更新。
- `league_registered_nationality` / `birthplace` を `players.json` に保存するよう変更。
- 通信例外時の継続処理を追加。
- `Accept-Encoding` から `br` を外し、取得レスポンスの文字化けを回避。

2. 並列取得スクリプト追加
- `scripts/dev/fetch_profile_fields_parallel.py` を新規追加。
- 未補完行を並列で取得して `players.json` を更新。

3. Upsert専用スクリプト追加
- `scripts/dev/upsert_players_json.py` を新規追加。
- 取得済み `players.json` を再フェッチせず `players` テーブルへ upsert 可能にした。

4. SQL・ドキュメント更新
- `supabase/rebuild/05_batch_game_and_players_columns.sql`
  - `players.player_slot_category`
  - `players.league_registered_nationality`
  - `players.birthplace`
  を追加。
- `supabase/rebuild/00_rebuild_all.sql` にも同内容を反映。
- `docs/flow.md` / `docs/table_definition.md` / `supabase/rebuild/README.md` を更新。

## 取得結果（players.json）
- total: 713
- `league_registered_nationality` 非null: 673
- `birthplace` 非null: 646
- いずれか欠損: 67

## Upsert実行結果
- 実行コマンド: `python3 -m scripts.dev.upsert_players_json --input scraper/data/players.json`
- 結果: 失敗（`PGRST204`）
- エラー: `Could not find the 'birthplace' column of 'players' in the schema cache`

## 次アクション
1. Supabase側で以下SQLを実行
```sql
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS player_slot_category TEXT;

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS league_registered_nationality TEXT;

ALTER TABLE players
    ADD COLUMN IF NOT EXISTS birthplace TEXT;
```

2. 再度Upsert
```bash
python3 -m scripts.dev.upsert_players_json --input scraper/data/players.json
```
