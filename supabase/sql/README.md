# データパッチSQL運用
作成日: 2026-08-04

このディレクトリには、live DBへ一回限りで適用するデータ補正・バックフィル・削除などの運用SQLを置く。現行スキーマの正本ではなく、新規DBの再構築には `supabase/rebuild/00_rebuild_all.sql` を使う。

CSVやJSONなどSQLの入力・目視確認用ファイルは `supabase/patches/` に置く。スクレイピング取得物・正本JSONは `scraper/data/` に置き、DB補正用ファイルと混在させない。配置規則は [`supabase/patches/README.md`](../patches/README.md) を参照する。

## ファイル名

基本形は `YYYYMMDD_<action>_<target>.sql` とする。

- `YYYYMMDD`: 作成日または実施判断日
- `action`: `fix`、`backfill`、`delete`、`drop` などの小文字snake_case
- `target`: 対象テーブルやデータ範囲を短く表す小文字snake_case
- ロールバックSQLは `YYYYMMDD_rollback_<action>_<target>.sql` とする
- 同日に実行順が必要な場合だけ、日付直後に `_01_`、`_02_` を付ける

## 標準の4ファイル構成

live DBのデータを更新するパッチは、原則として同じ日付・Issue・対象名で次の4ファイルを作成する。

| ファイル | 役割 |
|---|---|
| `YYYYMMDD_backup_issueNN_<target>.sql` | 対象行を永続バックアップへ保存する。対象件数と再実行をガードする |
| `YYYYMMDD_fix_issueNN_<target>.sql` | 実際のINSERT/UPDATE/DELETEを行う。backup表、対象件数、反映前状態を検証してから実行する |
| `YYYYMMDD_rollback_fix_issueNN_<target>.sql` | backup表から変更前へ戻す。適用後の状態を検証し、想定外の変更があれば停止する |
| `YYYYMMDD_verify_issueNN_<target>.sql` | liveテーブルを変更せず、backupを基準に実行前・実行後・ロールバック後の状態を判定する |

標準の実行順は `backup → verify（実行前）→ fix → verify（実行後）` とする。問題が見つかった場合だけ `rollback → verify（ロールバック後）` を実行する。`verify` はSELECTとセッション内一時表の作成・投入だけを許可し、永続テーブルの更新・削除を行わない。

4ファイル構成を採用しない読み取り専用調査や再構築SQLは例外とし、対象ファイルの先頭コメントに理由を記載する。バックアップ表は適用後の検証とロールバックが完了するまで削除しない。

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
| `20260811_backup_issue_12_players.sql` | Issue #12のプロフィール対象166行と削除対象48選手・関連行の永続バックアップ | 想定件数を検証してから5つのバックアップ表を作成。反映SQLより先に実行 |
| `20260811_verify_issue_12_players.sql` | Issue #12の反映前・反映後検証 | 変更予定の項目別件数と現在状態（反映前／反映後／想定外）を読み取り確認。バックアップSQL後に実行 |
| `20260811_fix_issue_12_players.sql` | Issue #12のプロフィール166件補完とスタッフ相当48選手・関連行の削除 | backup表、`updated_at`、対象件数、`player_id_map`参照を検証して単一DO文で更新 |
| `20260811_rollback_fix_issue_12_players.sql` | Issue #12反映の復旧 | backup表からプロフィール、players、stats、名前履歴、所属履歴を件数検証付きで復元 |
| `20260813_backup_issue_21_player_profiles.sql` | Issue #21の目視確認済みCSV117行に対応するplayers行の永続バックアップ | 対象117行と#12除外ID不在を検証してからバックアップ表を作成 |
| `20260813_verify_issue_21_player_profiles.sql` | Issue #21の反映前・反映後・ロールバック後検証 | backup表を基準に変更予定件数と現在状態をSELECTのみで判定 |
| `20260813_fix_issue_21_player_profiles.sql` | Issue #21のプロフィール欠損補完 | backup表、対象件数、反映前状態を検証し、CSVの非空値で空欄だけを更新 |
| `20260813_rollback_fix_issue_21_player_profiles.sql` | Issue #21のプロフィール補完の復旧 | 期待する適用後状態を確認してからbackup表の値へ復元 |
| `20260819_backup_issue25_player_id_merge.sql` | Issue #25の45848〜45865周辺18組の旧・現行IDと関連行を永続バックアップ | 対象ID、名前、既存IDマップ、試合成績の衝突を確認してからバックアップ |
| `20260819_verify_issue25_player_id_merge.sql` | Issue #25の実行前・実行後・ロールバック後検証 | SELECTと一時表のみ。`PRE_FIX`、`POST_FIX`、`ROLLED_BACK_OR_PRE_FIX`、`UNEXPECTED_STATE`を返す |
| `20260819_fix_issue25_player_id_merge.sql` | Issue #25の18組のplayer_id統合 | 旧IDの試合成績を現行IDへ移し、旧IDの履歴・所属・players行を削除して`player_id_map`へ記録 |
| `20260819_rollback_fix_issue25_player_id_merge.sql` | Issue #25のID統合の復旧 | backup表から対象36選手と関連行を変更前へ復元 |
| `20260820_backup_issue25_player_profiles.sql` | Issue #25の統合後プロフィール補完281人のバックアップと反映用パッチ表を作成 | 実行前に対象281行を固定。`player_slot_category`の標準表記も保持 |
| `20260820_verify_issue25_player_profiles.sql` | Issue #25のプロフィール補完の実行前・実行後・復旧後検証 | backup表を基準に国籍・出生地・選手区分の差分をSELECTのみで確認 |
| `20260820_fix_issue25_player_profiles.sql` | Issue #25の国籍・出生地補完と`player_slot_category`統一 | 国籍・出生地は空欄のみ補完し、選手区分は3表記へ更新 |
| `20260820_rollback_fix_issue25_player_profiles.sql` | Issue #25のプロフィール補完の復旧 | backup表から対象281行の変更対象列を復元 |
