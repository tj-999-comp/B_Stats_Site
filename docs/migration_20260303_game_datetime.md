# Migration適用ガイド（20260303_add_game_datetime）

対象マイグレーション:

- `supabase/migrations/20260303_add_game_datetime.sql`

`games` テーブルに試合日時（JST）の文字列カラム `game_datetime` を追加する。

---

## 変更内容

```sql
ALTER TABLE games ADD COLUMN IF NOT EXISTS game_datetime TEXT;
```

- カラム名: `game_datetime`
- 型: `TEXT`
- 値形式: `YYYY-MM-DD HH:MM`（JST）
- スクレイパー側で `game_datetime_unix`（Unix秒）から変換して UPSERT する

---

## 適用方法

### 方法A: GitHub Actions（推奨）

1. GitHub Secrets に `SUPABASE_DB_PASSSWORD` を登録する（未登録の場合）
   - 取得先: [Supabase ダッシュボード → Project Settings → Database → Database password](https://supabase.com/dashboard/project/mngqmfvsxcqjhsgkbyju/settings/database)
   - 登録先: [GitHub Secrets](https://github.com/tj-999-comp/B_Stats_Site/settings/secrets/actions)
   - Secret名: `SUPABASE_DB_PASSSWORD`

2. ワークフローを手動実行する

   ```bash
   gh workflow run migrate.yml --repo tj-999-comp/B_Stats_Site
   ```

3. 結果を確認する

   ```bash
   gh run list --workflow="migrate.yml" --repo tj-999-comp/B_Stats_Site --limit 1
   ```

### 方法B: Supabase SQL Editor（手動）

[SQL Editor](https://supabase.com/dashboard/project/mngqmfvsxcqjhsgkbyju/sql) に以下を貼り付けて実行:

```sql
ALTER TABLE games ADD COLUMN IF NOT EXISTS game_datetime TEXT;
```

### 方法C: psql（ローカル）

```bash
PGPASSWORD="<DBパスワード>" psql \
  "postgresql://postgres@db.mngqmfvsxcqjhsgkbyju.supabase.co:5432/postgres" \
  -f supabase/migrations/20260303_add_game_datetime.sql
```

---

## 適用確認

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'games' AND column_name = 'game_datetime';
```

`game_datetime | text` が返れば適用済み。
