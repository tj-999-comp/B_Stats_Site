# データパッチ入力ファイル
作成日: 2026-08-13

このディレクトリには、スクレイピング取得物や選手マスタの正本ではなく、live DBの個別補正・目視確認・パッチSQL実行に使う入力ファイルを置く。

## 配置の使い分け

| 場所 | 役割 | 例 |
|---|---|---|
| `scraper/data/` | B.LEAGUE公式サイトから取得した追跡済み入力・履歴資産 | 月次ゲームJSON、`players.json` |
| `supabase/patches/` | DB補正のためのCSV等の入力・確認用ファイル | 欠損プロフィール一覧、手動確認結果 |
| `supabase/sql/` | live DBへ適用する一回限りの運用SQL・ロールバックSQL | `YYYYMMDD_fix_*.sql` |
| `supabase/rebuild/` | 新規DB再構築の正本SQL | `00_rebuild_all.sql` |

`supabase/patches/` のファイルを `scraper/data/` の取得物や正本JSONへ自動反映してはならない。目視確認後にDBへ反映する場合は、対象・件数・変更前後の値・復旧方法を別途記録し、必要なら `supabase/sql/` に件数ガード付きSQLを作成する。

## ファイル名

基本形は `YYYYMMDD_issueNN_<purpose>.<ext>` とする。

- `YYYYMMDD`: 作成日または作業開始日
- `issueNN`: 主なGitHub Issue番号
- `purpose`: 対象と用途を小文字snake_caseで表す
- `ext`: CSV、JSONなど入力形式の拡張子

例:

```text
20260813_issue21_missing_player_profiles.csv
```

## 現在のファイル

| ファイル | 用途 |
|---|---|
| `20260813_issue21_missing_player_profiles.csv` | Issue #21の目視確認用。#12で除外したスタッフ相当47 IDとダミー1 IDを除外し、指定プロフィール項目のいずれかが欠損する117選手を収録 |
| `20260819_issue25_player_id_candidates.csv` | Issue #25の45848〜45865周辺について、同一人物候補18組を収録。統合判断前の確認用 |
| `20260819_issue25_missing_player_profiles.csv` | Issue #25の統合後に再監査した補完対象281選手。公式取得値、提案差分、未補完理由を目視確認するための入力 |
| `20260819_issue25_missing_player_profiles_proposed.csv` | 統合後に再監査した281選手。公式値、国籍からの出生地フォールバック、チーム・選手別の手動ルールを含むDB反映用入力 |
| `20260819_issue25_missing_player_profiles_unresolved.csv` | 補完提案がない選手の確認用。2026-08-20時点では該当0件（ヘッダーのみ） |
| `20260820_issue25_unresolved_player_slot_category.csv` | Issue #25の補完提案後も`player_slot_category`だけ未確定の18選手。目視確認用 |

## Issue #21 補足事項

- `last_seen_team_id` がNULLの選手は、所属チームのマスタがまだ取り込まれていないため、今回のパッチでは補完しない。
- `player_id` 45848〜45865周辺は、同一人物が複数IDへ分割されている可能性がある。既存IDとの名寄せ・統合は [Issue #23](https://github.com/tj-999-comp/B_Stats_Site/issues/23) で別途調査する。
- `league_registered_nationality` と `birthplace`（CSV上での `birth_place` 相当）が未入力の選手は、上記のID分割の可能性に加え、一時的な「特別指定選手」として登録されたケースがあるため、今回の空欄は許容する。
- 空欄をNULLへ更新する処理は行わない。CSVの非空値でも、DBに既存値がある列は上書きしない。

DBへ反映するSQLは、`supabase/sql/` の `backup → verify → fix → rollback` 4ファイル構成で管理する。Issue #21の対応ファイルは次のとおり。

- `20260813_backup_issue_21_player_profiles.sql`
- `20260813_verify_issue_21_player_profiles.sql`
- `20260813_fix_issue_21_player_profiles.sql`
- `20260813_rollback_fix_issue_21_player_profiles.sql`
