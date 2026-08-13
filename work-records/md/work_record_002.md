# 作業記録 002: players.nationality 追加手順整理とrebuild SQL一本化
作成日: 2026-05-26

## 背景
- `players.nationality` を追加してプロフィール補完（nationality が null の選手中心）を進める必要がある。
- rebuild SQL が分散しており、実行場所・実行順が分かりづらい状態だった。

## 対応内容
1. 実行用SQLを1ファイルに統合
- `supabase/rebuild/00_rebuild_all.sql` を新規作成。
- `01`〜`07` の rebuild SQL を順序付きで連結し、1回実行で必要処理を通せる構成にした。

2. ドキュメント更新
- `supabase/rebuild/README.md`
  - 推奨実行を `00_rebuild_all.sql` に一本化。
  - 個別ファイルは保守・差分確認用途と明記。
- `docs/flow.md`
  - PHASE 1 の実行手順を1ファイル実行へ更新。
- `docs/setup.md`
  - Supabase初期セットアップのSQLを `supabase/migrations/20260221_init.sql` から `supabase/rebuild/00_rebuild_all.sql` へ更新。
- `docs/table_definition.md`
  - `players` セクションに `nationality` と `old_player_id` を追記。

## ユーザー側で実行するSQL
```sql
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS nationality TEXT;
```

## 反映確認SQL
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'players'
  AND column_name = 'nationality';
```

## 補足
- 今後の再構築は原則 `supabase/rebuild/00_rebuild_all.sql` を実行する。
- 既存の分割ファイル（`01`〜`07`）は、保守・差分追跡・部分再実行のため残置。

## 追記（2026-05-26: 再実行時エラー対応）
- 現象: `duplicate key value violates unique constraint "ux_player_affiliations_open"`
- 原因: `03_identity_history.sql` の `player_affiliations` バックフィルINSERTが、再実行時に既存の open 行（`valid_to IS NULL`）と競合した。
- 対応: バックフィルINSERT末尾に `ON CONFLICT DO NOTHING` を追加し、再実行時の重複衝突を吸収して継続できるように修正。
- 反映先:
  - `supabase/rebuild/03_identity_history.sql`
  - `supabase/rebuild/00_rebuild_all.sql`

## 完了報告（2026-05-26）
- ユーザー側で SQL 実行が完了した前提で、本記録を完了扱いに更新。
- `players.nationality` 追加、および再実行時の重複衝突回避修正を反映済み。
- あわせて、当時の作業記録ディレクトリの命名規則を明文化し、CIでの自動検証を追加。
