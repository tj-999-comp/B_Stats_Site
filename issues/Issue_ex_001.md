# Issue_ex_001: 2016-2017 シーズン投入（初回失敗→再チャレンジ成功）
作成日: 2026-05-26

## 概要
最古シーズン（2016-2017）の投入を実行したが、`teams` テーブルへの upsert で Row Level Security (RLS) に拒否され、投入が停止した。

## 実行内容
- 対象シーズン: `scraper/data/season_2016-2017/`
- 実行コマンド:

```bash
/Users/ryosuketajima/git-tj999/B_Stats_Site/.venv/bin/python -m scripts.db.upsert_games --input scraper/data/season_2016-2017/games_2016-17_2016-10-01_2016-10-31.json
```

## 初回結果
- エラー: `new row violates row-level security policy for table "teams"` (code: `42501`)
- 停止箇所: `upsert_teams()` 実行時

## 件数増分確認
投入前後で件数に変化なし。

| テーブル | 投入前 | 投入後 | 増分 |
|---|---:|---:|---:|
| teams | 0 | 0 | 0 |
| games | 0 | 0 | 0 |
| game_team_stats | 0 | 0 | 0 |
| players | 0 | 0 | 0 |
| player_game_stats | 0 | 0 | 0 |

## 補足
- dry-run では抽出件数を確認できる（例: teams=18, games=89, game_team_stats=178, players=228, player_game_stats=2185）。
- データ形式の問題ではなく、DB書き込み権限（キー種別またはRLSポリシー）起因の可能性が高い。

## 次アクション案
1. `scraper/.env` の `SUPABASE_SECRET_KEYS` が service_role キーか再確認する。
2. Supabase 側で `teams` テーブルの RLS 設定と書き込みポリシーを確認する。
3. 書き込み権限確認後、同コマンドで再実行して件数増分を再計測する。

## 再チャレンジ結果

### 実施内容
- `SUPABASE_SECRET_KEYS` を publishable ではなく secret キーへ変更後に再実行。
- 2016-2017 シーズンの月次9ファイルを順次 `upsert_games` で投入。

### 再チャレンジ後の件数増分

| テーブル | 投入前 | 投入後 | 増分 |
|---|---:|---:|---:|
| teams | 0 | 21 | +21 |
| games | 0 | 557 | +557 |
| game_team_stats | 0 | 1114 | +1114 |
| players | 0 | 280 | +280 |
| player_game_stats | 0 | 13972 | +13972 |

### 補足
- `games` テーブルの `season='2016-17'` 件数は `557` 件。
- 再チャレンジでは RLS エラーは発生せず、`upsert completed` を確認。
