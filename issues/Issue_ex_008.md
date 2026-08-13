# Issue_ex_008: Issue #21 欠損プロフィール目視補完・DBパッチ準備
作成日: 2026-08-13

## 対象

Issue #21の目視確認用CSVをもとに、補完可能な選手プロフィールをlive DBへ反映するためのSQLを準備する。

入力ファイルは `supabase/patches/20260813_issue21_missing_player_profiles.csv` とし、スクレイピング取得物や選手マスタ正本とは分離する。

## 目視確認での補足事項

1. `last_seen_team_id` がNULLの選手は、所属チームがまだ取り込まれていないため、今回は補完しない。
2. `player_id` 45848〜45865周辺には、同一人物が複数IDへ分割された可能性がある。`player_name_j` の重複検索などを起点に、既存IDとの統合を調査する。名寄せ作業はGitHub Issue #23へ切り出した。
3. `league_registered_nationality` と `birthplace`（ユーザー記載の `birth_place` に相当）が未入力の選手は、上記のID分割の可能性に加えて、一時的に加入した「特別指定選手」としての登録である場合があるため、今回の空欄は許容する。

## 作成物

- `supabase/patches/20260813_issue21_missing_player_profiles.csv`
  - 117選手
  - #12で除外したスタッフ相当47 IDとダミー1 IDは含めない
- `supabase/sql/20260813_backup_issue_21_player_profiles.sql`
  - CSVの117行に対応する `players` 行を永続バックアップへ保存する
- `supabase/sql/20260813_verify_issue_21_player_profiles.sql`
  - fix前・fix後・rollback後の状態をSELECTのみで判定する
- `supabase/sql/20260813_fix_issue_21_player_profiles.sql`
  - CSVの117行をSQL内の一時テーブルへ読み込む
  - 対象IDの存在、バックアップ後の変更、除外IDの混入を事前確認する
  - CSVの非空値で、DB側がNULLまたは空文字の列だけ補完する
  - CSVの空欄で既存DB値をNULLへ変更しない
- `supabase/sql/20260813_rollback_fix_issue_21_player_profiles.sql`
  - fix後の状態を検証してからバックアップ時点へ復元する

実行順は `backup → verify（実行前）→ fix → verify（実行後）`。問題があれば `rollback → verify（ロールバック後）` とする。

## 現時点のCSV欠損

| 項目 | 欠損件数 | 今回の扱い |
|---|---:|---|
| `last_seen_team_id` | 8 | チームマスタ未取り込みのため保留 |
| `last_seen_jersey_number` | 1 | CSVに値がないため保留 |
| `league_registered_nationality` | 29 | ID分割・特別指定選手等のため空欄を許容 |
| `birthplace` | 108 | ID分割・特別指定選手等のため空欄を許容 |

## 適用状況

2026-08-13にbackup、verify、fix、verifyを実行した。対象117行、バックアップ117行、対象IDの欠落なしを確認した。CSVの非空値はすでにlive DBと一致しており、fillable 0件、変更差分0件、`updated_at`変更0件だったため、fixによる実更新は発生していない。実行後のverify判定は `BEFORE_APPLY_OR_AFTER_ROLLBACK` で、今回のCSV内容に関して問題はなかった。
