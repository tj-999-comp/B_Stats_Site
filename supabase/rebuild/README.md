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
- 本手順は `supabase/rebuild/01_base_schema.sql` をベースにする

## 最短実行（推奨）

- 実行ファイル: `supabase/rebuild/00_rebuild_all.sql`
- 目的: 再構築に必要な SQL（01〜07）を 1 ファイルに統合し、実行漏れを防ぐ
- 実行方法: Supabase SQL Editor に `00_rebuild_all.sql` の内容を貼り付けて実行

> 補足:
> - 既存の `01` 〜 `07` は保守・差分確認用に保持
> - 通常運用は `00_rebuild_all.sql` のみ実行すればよい

> 注意:
> `supabase/migrations/20260221_init.sql` は旧来の `player_stats` / `team_stats` / `rankings` 中心の初期構成で、
> 現在の投入フロー（`teams`, `games`, `game_team_stats`, `players`, `player_game_stats`）と整合しないため、
> 完成系スキーマ再構築のベースには使用しない。

> 実行ファイル削減ポリシー（2026-05-24 反映）:
> - Step4/5/6/9 は `supabase/rebuild/05_batch_game_and_players_columns.sql` に統合
> - Step7/8/11 は `supabase/rebuild/06_batch_player_identity.sql` に統合
> - 旧分割 migration は不要化したため削除

---

## 実行ステップ一覧（順番固定）

通常は `supabase/rebuild/00_rebuild_all.sql` の一括実行で完了する。
以下は内容確認・個別再実行が必要な場合の内訳。

### Step 0: ベーススキーマ作成

- 実行ファイル: `supabase/rebuild/01_base_schema.sql`
- 意味/目的:
  - 現行投入コードが前提にしている主テーブル群を一度に作る
  - 具体的には `teams`, `games`, `game_team_stats`, `players`, `player_game_stats` を作成
  - 以降の migration が依存する土台（FK 参照先）を先に確保する
- 実行しないと起きること:
  - 履歴テーブル migration で `teams` / `players` / `games` 不在エラーになる

---

### Step 1: 事前チェック（履歴系 migration 前）

- 実行ファイル: `supabase/rebuild/02_precheck_identity_history.sql`
- 意味/目的:
  - 履歴 migration に必要な依存テーブルが揃っているか確認
  - 重複作成や想定外状態（既に同名オブジェクトがあるなど）を事前検知
- 実行しないと起きること:
  - migration 途中で止まり、原因調査に時間がかかる

---

### Step 2: 履歴管理の導入

- 実行ファイル: `supabase/rebuild/03_identity_history.sql`
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

- 実行ファイル: `supabase/rebuild/04_postcheck_identity_history.sql`
- 意味/目的:
  - 履歴テーブル/トリガー/ビューが正しく作成されたか検証
  - 「作れたつもり」を防ぎ、次の migration に進んで良いか判断する

---

### Step 4: 試合日時カラム追加

- 実行ファイル: `supabase/rebuild/05_batch_game_and_players_columns.sql`
- 意味/目的:
  - Step4/5/6/9 を統合して一括適用する
  - 追加対象:
    - `games.game_datetime`
    - `games.game_date`
    - `games.game_type`（`setu` から `RS/CS` をバックフィル）
    - `players.player_slot_category`
    - `players.league_registered_nationality`
    - `players.birthplace`
    - `players.entity_type`
  - ファイル分散を減らし、実行漏れを防ぐ

---

### Step 5: player_id 変更追跡を統合導入

- 実行ファイル: `supabase/rebuild/06_batch_player_identity.sql`
- 意味/目的:
  - Step7/8/11 を統合して一括適用する
  - 実施内容:
    - `players.old_player_id` 追加
    - `player_id_map` 作成（旧名 `player_id_aliases` がある場合は自動吸収）
    - `player_game_stats` / `player_name_history` / `player_affiliations` の FK を `ON UPDATE CASCADE` 対応
  - Step8 の「テーブルが存在しない」系エラーを設計上防止する

補足（Step5内で統合した理由）:

- Step7 と Step8 は本来同じ論点（`player_id_map` の定義統一）であり、分割する必要が薄い
- Step11（`players.old_player_id`）は `player_id_map` の運用補助情報なので、同時に入れる方が一貫する

---

### Step 6: 所属履歴トリガーの不整合防止修正

- 実行ファイル: `supabase/rebuild/07_fix_affiliation_trigger.sql`
- 意味/目的:
  - 時系列逆順の UPSERT で `valid_to < valid_from` が起きる問題を回避
  - 過去イベントが後から来た時に、現在オープン行を壊さないガードを追加

---

### Step 7: 最終確認

- この runbook の「実行後に確認すべき最低限チェック」「完了判定基準」を実行する
- 合格後に JSON 再投入へ進む

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
    or (table_name = 'players' and column_name in (
      'player_slot_category','league_registered_nationality','birthplace',
      'entity_type','old_player_id'
    ))
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

## 完了判定基準（これを満たせば次工程へ進んでOK）

以下は「migration が正しく完了したか」を判断するための基準。

### 判定A: 必須テーブルが全て存在する

- 合格条件: 結果件数が **9件**（不足0件）
- 対象:
  - `teams`
  - `games`
  - `game_team_stats`
  - `players`
  - `player_game_stats`
  - `team_name_history`
  - `player_name_history`
  - `player_affiliations`
  - `player_id_map`

```sql
select count(*) as table_count
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'teams','games','game_team_stats','players','player_game_stats',
    'team_name_history','player_name_history','player_affiliations','player_id_map'
  );
```

### 判定B: 追加カラムが全て存在する

- 合格条件: 結果件数が **8件**（不足0件）
- 対象:
  - `games.game_datetime`
  - `games.game_date`
  - `games.game_type`
  - `players.player_slot_category`
  - `players.league_registered_nationality`
  - `players.birthplace`
  - `players.entity_type`
  - `players.old_player_id`

```sql
select count(*) as column_count
from information_schema.columns
where table_schema = 'public'
  and (
    (table_name = 'games' and column_name in ('game_datetime','game_date','game_type'))
    or (table_name = 'players' and column_name in (
      'player_slot_category','league_registered_nationality','birthplace',
      'entity_type','old_player_id'
    ))
  );
```

### 判定C: 参照ビューが存在する

- 合格条件: 結果件数が **3件**
- 対象:
  - `v_teams_current`
  - `v_players_current`
  - `v_player_transfer_events`

```sql
select count(*) as view_count
from information_schema.views
where table_schema = 'public'
  and table_name in ('v_teams_current','v_players_current','v_player_transfer_events');
```

### 判定D: 所属履歴トリガー修正が反映されている

- 合格条件: クエリ結果に `event_at <= current_open.valid_from` が含まれる
- 目的: `20260308d_fix_affiliation_trigger.sql` が有効化されていることを確認

```sql
select pg_get_functiondef('track_player_affiliation_from_game_stats()'::regprocedure) as fn;
```

### 判定E: players 参照エラーが解消している

- 合格条件: 下記がエラーなく `0` 以上の件数を返す

```sql
select count(*) as players_count from players;
```

### 総合判定

- A〜E がすべて合格: migration 完了。JSON 再投入へ進んでよい。
- 1つでも不合格: 不足している migration を再実行してから再判定する。

---

## ここまで終わったら

この時点で「完成系スキーマの土台」は準備完了。
次は JSON 再投入（`scripts/db/upsert_games.py --input <file>` を対象ファイルごとに実行）に進む。
