# DB設計ブラッシュアップ（改名・移籍対応）

## 背景

現行スキーマでは、`teams` / `players` は最新値をUPSERTするため、以下の履歴が失われる。

- チーム名変更（改名、略称変更）
- 選手名変更（表記変更、登録名変更）
- 選手の移籍（所属チーム変更、背番号変更）

このドキュメントは、既存スクレイパーのUPSERT処理を大きく変えずに、履歴を保存できるようにする設計を示す。

---

## 方針

1. **既存テーブルは維持**（`teams`, `players`, `player_game_stats` など）
2. 追加テーブルで履歴を管理
3. トリガーで履歴を自動記録（投入アプリ改修を最小化）
4. 既存データをバックフィルして運用開始

---

## 追加するテーブル

### 1) `team_name_history`

- 用途: チーム名・略称の変更履歴
- 単位: `team_id` ごと
- 期間管理: `valid_from`, `valid_to`

### 2) `player_name_history`

- 用途: 選手名（和英）の変更履歴
- 単位: `player_id` ごと
- 期間管理: `valid_from`, `valid_to`

### 3) `player_affiliations`

- 用途: 選手の所属履歴（移籍、背番号変更）
- 単位: `player_id` ごと
- 期間管理: `valid_from`, `valid_to`
- 補助キー: `first_schedule_key`, `last_schedule_key`

---

## 実装ファイル

- マイグレーション: `supabase/migrations/20260224_identity_history.sql`

このマイグレーションで以下を実施する。

- 履歴テーブル作成
- 既存データのバックフィル
- 履歴更新トリガー作成
- 参照用ビュー作成

---

## トリガー仕様（要点）

### `teams` 更新時

- `team_name_j`, `team_name_e`, `team_short_name_j`, `team_short_name_e` の差分を検出
- 差分があれば、履歴の現行行（`valid_to IS NULL`）をクローズして新行を追加

### `players` 更新時

- `player_name_j`, `player_name_e` の差分を検出
- 差分があれば、履歴をクローズして新行を追加

### `player_game_stats` 挿入/更新時

- `player_id` の現行所属（`valid_to IS NULL`）を参照
- `team_id` または `jersey_number` が変われば移籍（または背番号変更）として新履歴を開始
- 同一所属なら `last_schedule_key` を更新

---

## 参照ビュー

### `v_teams_current`

- 現在有効なチーム名を返す

### `v_players_current`

- 現在有効な選手名と所属を返す

### `v_player_transfer_events`

- 連続する所属履歴の差分から移籍イベントを確認できる

---

## 想定クエリ

```sql
-- 現在のチーム表示名
SELECT *
FROM v_teams_current
ORDER BY team_id;

-- ある選手の改名履歴
SELECT player_id, player_name_j, player_name_e, valid_from, valid_to
FROM player_name_history
WHERE player_id = '12345'
ORDER BY valid_from;

-- ある選手の移籍履歴
SELECT player_id, from_team_id, to_team_id, transferred_at, jersey_number
FROM v_player_transfer_events
WHERE player_id = '12345'
  AND from_team_id IS NOT NULL
ORDER BY transferred_at;
```

---

## 運用上の注意

- `schedule_key` の順序と実際の時系列が一致しないデータが混入する場合、移籍判定がズレる可能性がある。
- 既存スクレイパーは `player_id`, `team_id` を主軸にしているため、今回の対応でアプリ側の必須改修はない。
- 将来的に「同一選手のID変更」まで対応する場合は、`player_identity_map`（旧ID→正規ID）テーブルを追加するのが望ましい。
