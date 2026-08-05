# データパッチSQL運用
作成日: 2026-08-04

このディレクトリには、live DBへ一回限りで適用するデータ補正・バックフィル・削除などの運用SQLを置く。現行スキーマの正本ではなく、新規DBの再構築には `supabase/rebuild/00_rebuild_all.sql` を使う。

## ファイル名

基本形は `YYYYMMDD_<action>_<target>.sql` とする。

- `YYYYMMDD`: 作成日または実施判断日
- `action`: `fix`、`backfill`、`delete`、`drop` などの小文字snake_case
- `target`: 対象テーブルやデータ範囲を短く表す小文字snake_case
- ロールバックSQLは `YYYYMMDD_rollback_<action>_<target>.sql` とする
- 同日に実行順が必要な場合だけ、日付直後に `_01_`、`_02_` を付ける

例:

```text
20260804_fix_2021_22_game_datetimes.sql
20260804_rollback_fix_2021_22_game_datetimes.sql
```

## SQLに記載する情報

- 目的、関連Issue、対象テーブル
- 想定件数と実行前条件
- バックアップまたは復旧方法
- 更新件数ガードと実行後確認
- 再実行できるかどうか

## 実行手順

1. 接続先が対象環境であることを確認する。
2. SupabaseのスナップショットまたはSQL内のバックアップ手順を確認する。
3. 読み取りクエリと件数ガードを確認する。
4. SQL全体を一度に実行する。途中の文だけを抜き出して実行しない。
5. 事後確認が完了するまでバックアップを保持する。

SQL Editorから実行する場合も、複数リクエストに分割せずファイル全体を実行する。トランザクションプーラー経由で一時テーブルを使う場合は、セッションをまたぐ複数文に依存せず、更新本体を単一の `DO` 文へまとめる。ファイル内で `BEGIN` / `COMMIT` を使用していても、外部APIや別スクリプトの処理までは同じトランザクションに含まれない。

DBeaverの `Cmd + Enter` は通常、カーソル位置にある1文だけを実行する。更新本体の `DO` 文と末尾の確認用 `SELECT` が分かれているファイルでは、「SQLスクリプトを実行」を使うか、実行対象全体を選択してから実行する。末尾の `SELECT` だけを実行しても更新本体は適用されない。空白行ではなくセミコロンが文の区切りになる。

## 収録SQL

| ファイル | 用途 | 注意点 |
|---|---|---|
| `20260308_delete_all_games.sql` | 試合関連データの全削除 | 破壊的。Supabaseスナップショット必須 |
| `20260527_drop_players_nationality_and_backfill_slot_category.sql` | `players.nationality` 削除と選手枠区分の暫定補完 | スキーマ変更を含む旧運用パッチ。canonical SQLへ自動統合しない |
| `20260602_backfill_player_profile_fields.sql` | 2026-06-02取得分の選手プロフィール補完 | 298選手を対象とする固定データ |
| `20260804_fix_2021_22_game_datetimes.sql` | Issue #10の303試合をgames限定で補正 | 単一DO文内で永続バックアップを作成してから更新 |
| `20260804_rollback_fix_2021_22_game_datetimes.sql` | Issue #10補正の復旧 | 上記SQLが作成したバックアップを単一DO文で復元 |
| `20260804_fix_game_team_points.sql` | Issue #11の全10,846チーム行の得点系23列を補正 | スコア・シュート式・PFT復元値を検証し、永続バックアップ後に単一DO文で更新 |
| `20260804_rollback_fix_game_team_points.sql` | Issue #11補正の復旧 | 上記SQLが保存した23列と`updated_at`を単一DO文で復元 |
