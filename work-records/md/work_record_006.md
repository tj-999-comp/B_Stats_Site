# 作業記録 006: game_team_statsの得点誤マッピング補正
作成日: 2026-08-05

## 対象

- GitHub Issue: [#11 game_team_stats.points の誤マッピングを修正する](https://github.com/tj-999-comp/B_Stats_Site/issues/11)
- 対象テーブル: `public.game_team_stats`
- 対象件数: 5,423試合、10,846チーム行
- 対象コード: `scripts/db/upsert_games.py`

## 原因

B.LEAGUE公式JSONの `HomeTeamPTR` / `AwayTeamPTR` を得点として `game_team_stats.points` へ変換していた。`TeamPTR` はフィールドゴール成功率に相当し、試合の最終得点ではない。最終得点の正本は `HomeTeamScore` / `AwayTeamScore` である。

追跡済み全74月次JSONを調査した結果、サマリーを持つ5,423試合・10,846チーム行すべてで、旧変換値と試合スコアが不一致だった。一方、`2 × fg2m + 3 × fg3m + ftm` は全10,846行で試合スコアと一致した。

## 変換スクリプトの修正

`scripts/db/upsert_games.py` を次の仕様へ変更した。

1. `HomeTeamScore` / `AwayTeamScore` を各チームの `points` に採用する。
2. 試合スコアが欠損している場合だけ、`2 × fg2m + 3 × fg3m + ftm` を採用する。
3. 試合スコアとシュート式が不一致なら、いずれのテーブルもUpsertする前に停止する。
4. dry-runと通常実行の両方で、入力スコア、シュート式、変換後 `points` を照合する。
5. 変換後チーム行の欠落、余剰、重複も監査し、不整合があれば停止する。
6. `TeamPTR` は `points` に使用せず、別カラムも追加しない。既存の `fg_pct` はFGM/FGAから計算する。

スコア欠損時のフォールバックと、スコア・シュート式および変換後pointsの不一致時に停止することは合成データでも確認した。

## 全月次JSONの検証

追跡済み全74月次JSONを明示して `python -m scripts.db.upsert_games --input <path> --dry-run` を実行した。

```text
files=74
audited_team_rows=10846
score_available_rows=10846
score_missing_rows=0
score_shot_mismatch_rows=0
transformed_score_mismatch_rows=0
transformed_shot_mismatch_rows=0
missing_transformed_rows=0
unexpected_transformed_rows=0
duplicate_transformed_rows=0
```

## live DBデータパッチ

次の運用SQLを作成し、使い捨てローカルPostgreSQLで適用、再実行防止、ロールバック、ロールバック再実行防止を確認した後、live DBへ適用した。

- `supabase/sql/20260804_fix_game_team_points.sql`
- `supabase/sql/20260804_rollback_fix_game_team_points.sql`

更新前の23列と `updated_at` は `public.data_patch_backup_20260804_issue_11_game_team_stats` に10,846行保存した。バックアップテーブルはRLSを有効にし、`anon` と `authenticated` の権限を取り消している。

補正対象は `points` と、これに依存する次の22列である。

- `ts_pct`, `off_rtg`, `def_rtg`, `net_rtg`
- `pft_pct`, `fbp_pct`, `scp_pct`, `pitp_pct`
- `pt2_points_share`, `pt3_points_share`, `ft_points_share`, `eff`
- `close_win_3pts_or_less`, `close_loss_3pts_or_less`
- `opp_ts_pct`, `opp_pt2_points_share`, `opp_pt3_points_share`, `opp_ft_points_share`
- `opp_fbp_pct`, `opp_scp_pct`, `opp_pitp_pct`, `opp_pft_pct`

PFTの元値はDBに直接保存されていないため、補正前の `pft_pct × points` から整数として復元した。更新前に `pft_rtg × 相手turnovers` からの独立した復元値と全件一致することを確認した。

## live DB適用後の全件監査

live Supabaseから `games` と `game_team_stats` を読み取り専用で全件取得し、試合単位のペアと補正対象23列を再計算して照合した。

```text
games_rows=5423
game_team_stats_rows=10846
game_team_stats_games=5423
backup_rows=10846
invalid_game_pair_games=0
invalid_pair_rows=0
orphan_stat_rows=0
invalid_base_rows=0
points_score_mismatch_rows=0
shot_formula_score_mismatch_rows=0
pft_recovery_mismatch_rows=0
derived_mismatch_rows=0
derived_field_mismatches={}
```

これにより、各試合にhome/awayの2行が存在し、次の完了条件をすべて満たすことを確認した。

- `points` と試合スコアの不一致が0件
- シュート式と試合スコアの不一致が0件
- 得点依存22列の計算不一致が0件
- 欠損試合、片側チーム行、孤立チーム行が0件

## 変更しない項目

- 追跡済みJSONの書き換え
- DBカラムの追加・削除
- `games` の更新
- `player_game_stats.points` の更新
- `TeamPTR` の新規保存

## 完了判定

変換元の修正、Upsert前監査、全74月次JSONのdry-run、バックアップ・ロールバック付きlive DB補正、得点依存22列を含む全件監査、canonical SQLと関連文書の同期が完了した。以上によりIssue #11の修正作業を完了とする。
