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

## Planning 統合メモ（2026-05-26）

この Issue に `docs/Planning_20260526.md` の要点と進捗を統合して管理する。

### 目的
- スクレイピング済みデータを、棚卸し・投入・検証まで含めて段階的にDBへ投入する。

### 前提
- データソースは `scraper/data/` 配下。
- 投入スクリプトは `scripts/db/upsert_games.py` を利用。
- 正本マスタは `players.json`。

### 実行チェックリスト（統合版）

#### 本体
- [x] `scraper/.env` に `SUPABASE_URL` と `SUPABASE_SECRET_KEYS` が設定済み。
- [x] `scraper/data/` は月次JSON中心の構成へ整理済み。
- [x] `season_2016-2017` から `season_2024-2025` まで投入対象が揃っていることを確認済み。
- [x] `season_2022-2023` への命名統一を確認済み。
- [x] 代表JSONで dry-run 成功を確認済み。
- [x] 最古1シーズン（2016-2017）を投入実行済み。
- [x] 投入後の件数増分を確認済み（本Issue記録）。
- [ ] 問題なければ残りシーズンへ横展開する。
- [ ] 全シーズン投入後に主要テーブル件数・代表レコードを確認する。

#### 保留（意思決定済み）
- [x] `player_alias_candidates.csv` は `status=ok` 行を `player_id_map` 適用対象として扱う。
- [x] 正本は `players.json`、`players.csv` は参考用。
- [x] `game_team_stats_preview.csv` は保持しない（削除済み）。
- [x] `play_by_play` 系は本運用から切り離す。
- [x] プロフィール補完はDB投入後に再実行する（`nationality` が `null` の選手中心）。

#### 手動確認（意思決定済み）
- [x] 接続先は本番投入先であることを確認済み。
- [x] `SUPABASE_SECRET_KEYS` は service_role 相当キー利用で再試行済み。
- [x] 既存投入データなし（衝突リスクなし）。
- [x] `player_id_map` 利用方針は採用。
- [x] 件数チェック観点は本Issueの増分表で固定。
- [x] 差し戻し詳細メモは厳密運用しない方針。

## ここまでの完了事項（サマリー）

1. データ整理（確認用JSON削除、命名統一、不要フィールド除去）を実施し、GitHubへ反映済み。
2. Planning ドキュメントに実行チェックリストを整備し、意思決定内容を反映済み。
3. 初回投入失敗（RLS 42501）を検知し、原因をキー権限と切り分け。
4. `SUPABASE_SECRET_KEYS` を secret キーへ切替後、再チャレンジ成功。
5. 最古シーズン（2016-2017）投入を完了し、件数増分を確認済み。
