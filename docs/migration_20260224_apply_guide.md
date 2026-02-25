# Migration適用ガイド（20260224_identity_history）

対象マイグレーション:

- `supabase/migrations/20260224_identity_history.sql`

このガイドは、チーム改名・選手改名・移籍履歴テーブルを安全に適用するための手順。

---

## 0. 事前条件

- Supabase プロジェクトの SQL Editor にアクセスできる
- 既存テーブル `teams`, `players`, `games`, `player_game_stats` が存在する

---

## 1. 事前確認（読み取り専用）

`supabase/sql/20260224_precheck.sql` の内容を SQL Editor で実行。

確認ポイント:

- 依存テーブルが存在すること
- 追加予定テーブル/ビュー/関数がまだ存在しない（または想定どおり）
- 現在行数（`teams`, `players`, `player_game_stats`）を把握

---

## 2. マイグレーション適用

`supabase/migrations/20260224_identity_history.sql` を SQL Editor で実行。

実行時の注意:

- データ量が多い場合、バックフィルで時間がかかる
- エラー発生時は、該当エラー行を確認して中断（再実行可な設計）

---

## 3. 事後確認（読み取り専用）

`supabase/sql/20260224_postcheck.sql` の内容を SQL Editor で実行。

確認ポイント:

- 履歴テーブルの作成確認
- トリガーの作成確認
- バックフィル件数確認
- `v_teams_current`, `v_players_current`, `v_player_transfer_events` が参照可能

---

## 4. 簡易動作確認（任意）

SQL Editor で以下を確認:

```sql
SELECT * FROM v_teams_current LIMIT 10;
SELECT * FROM v_players_current LIMIT 10;
SELECT * FROM v_player_transfer_events WHERE from_team_id IS NOT NULL LIMIT 20;
```

---

## 5. ロールバック方針（必要時）

今回の変更は追加中心のため、緊急時は以下を実行して切り戻し可能。

1. 追加トリガーの削除
2. 追加ビューの削除
3. 追加テーブルの削除（履歴データは失われる）

※ 本番運用では、実行前に Supabase のバックアップ/復元ポイント確保を推奨。
