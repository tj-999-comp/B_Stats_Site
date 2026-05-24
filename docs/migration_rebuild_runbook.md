# Supabase 再構築 Migration 実行手順書（完成系スキーマ基準）

作成日: 2026-05-24

この手順書は、**前回の完成系スキーマを正解**として新規 Supabase プロジェクトを再構築するための実行ガイドです。

目的は次の2つです。

1. どの SQL を、なぜ、その順で流すかを明確にする
2. SQL Editor で手動実行しても失敗しにくいようにする

---

## 前提

- 実行場所: Supabase SQL Editor
- 対象: 新規に作り直した Supabase プロジェクト
- 本手順は `docs/schema_draft_games_light.sql` をベースにする

> 注意:
> `supabase/migrations/20260221_init.sql` は旧来の `player_stats` / `team_stats` / `rankings` 中心の初期構成で、
> 現在の投入フロー（`teams`, `games`, `game_team_stats`, `players`, `player_game_stats`）と整合しないため、
> 完成系スキーマ再構築のベースには使用しない。

---

## 実行ステップ一覧（順番固定）

### Step 0: ベーススキーマ作成

- 実行ファイル: `docs/schema_draft_games_light.sql`
- 意味/目的:
  - 現行投入コードが前提にしている主テーブル群を一度に作る
  - 具体的には `teams`, `games`, `game_team_stats`, `players`, `player_game_stats` を作成
  - 以降の migration が依存する土台（FK 参照先）を先に確保する
- 実行しないと起きること:
  - 履歴テーブル migration で `teams` / `players` / `games` 不在エラーになる

---

### Step 1: 事前チェック（履歴系 migration 前）

- 実行ファイル: `supabase/sql/20260224_precheck.sql`
- 意味/目的:
  - 履歴 migration に必要な依存テーブルが揃っているか確認
  - 重複作成や想定外状態（既に同名オブジェクトがあるなど）を事前検知
- 実行しないと起きること:
  - migration 途中で止まり、原因調査に時間がかかる

---

### Step 2: 履歴管理の導入

- 実行ファイル: `supabase/migrations/20260224_identity_history.sql`
- 意味/目的:
  - 改名・移籍履歴を保持する仕組みを追加
  - 追加される主な要素:
    - `team_name_history`
    - `player_name_history`
    - `player_affiliations`
    - 履歴更新トリガー/関数
    - 参照ビュー（現在値・移籍イベント）
  - 既存データがある場合はバックフィルも行う
- 実行しないと起きること:
  - チーム名変更や移籍の履歴が保持されず、完成系仕様を満たせない

---

### Step 3: 事後チェック（履歴系 migration 後）

- 実行ファイル: `supabase/sql/20260224_postcheck.sql`
- 意味/目的:
  - 履歴テーブル/トリガー/ビューが正しく作成されたか検証
  - 「作れたつもり」を防ぎ、次の migration に進んで良いか判断する

---

### Step 4: 試合日時カラム追加

- 実行ファイル: `supabase/migrations/20260303_add_game_datetime.sql`
- 意味/目的:
  - `games.game_datetime`（JST 文字列）を追加
  - 表示やデバッグで日時を直接扱いやすくする

---

### Step 5: 試合日カラム追加

- 実行ファイル: `supabase/migrations/20260303_add_game_date.sql`
- 意味/目的:
  - `games.game_date`（JST 日付文字列）を追加
  - 日次集計、日付フィルタ、運用補正処理を簡単にする

---

### Step 6: 選手国籍カラム追加

- 実行ファイル: `supabase/migrations/20260306_add_players_nationality.sql`
- 意味/目的:
  - `players.nationality` を追加
  - プロフィール補完処理（国籍/カテゴリ）の受け皿を作る

---

### Step 7: 旧ID→新IDマッピング導入

- 実行ファイル: `supabase/migrations/20260308_player_id_aliases.sql`
- 意味/目的:
  - 選手 ID 変更に追従するためのマップテーブルを導入
  - 当初名は `player_id_aliases`（後続 migration でリネーム）
  - 関連 FK を `ON UPDATE CASCADE` 対応にし、ID 統合時の整合性を担保

---

### Step 8: マップテーブルを完成系命名へ変更

- 実行ファイル: `supabase/migrations/20260308b_rename_player_id_map.sql`
- 意味/目的:
  - `player_id_aliases` を `player_id_map` にリネーム
  - 列名も `old_player_id`, `player_id` に統一
  - 投入コード側の参照名と一致させる

---

### Step 9: 試合区分カラム追加と初期値投入

- 実行ファイル: `supabase/migrations/20260308c_add_game_type.sql`
- 意味/目的:
  - `games.game_type` を追加
  - `setu` から `RS` / `CS` を判定して更新
  - レギュラーシーズン/チャンピオンシップの切り分けを DB 側で保持

---

### Step 10: 所属履歴トリガーの不整合防止修正

- 実行ファイル: `supabase/migrations/20260308d_fix_affiliation_trigger.sql`
- 意味/目的:
  - 時系列逆順の UPSERT で `valid_to < valid_from` が起きる問題を回避
  - 過去イベントが後から来た時に、現在オープン行を壊さないガードを追加

---

### Step 11: players に旧ID列を追加

- 実行ファイル: `supabase/migrations/20260308e_add_old_player_id_to_players.sql`
- 意味/目的:
  - `players.old_player_id` を追加
  - 選手ID移行時の参照性・追跡性を上げる

---

## 実行後に確認すべき最低限チェック

以下は SQL Editor で順に実行。

```sql
-- 1) テーブル存在確認
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'teams','games','game_team_stats','players','player_game_stats',
    'team_name_history','player_name_history','player_affiliations','player_id_map'
  )
order by table_name;

-- 2) 主要カラム確認
select table_name, column_name
from information_schema.columns
where table_schema = 'public'
  and (
    (table_name = 'games' and column_name in ('game_datetime','game_date','game_type'))
    or (table_name = 'players' and column_name in ('nationality','old_player_id'))
  )
order by table_name, column_name;

-- 3) ビュー確認（identity_history で作成済み想定）
select table_name
from information_schema.views
where table_schema = 'public'
  and table_name in ('v_teams_current','v_players_current','v_player_transfer_events')
order by table_name;
```

---

## ここまで終わったら

この時点で「完成系スキーマの土台」は準備完了。
次は JSON 再投入（`scripts/db/upsert_games.py --input <file>` を対象ファイルごとに実行）に進む。
