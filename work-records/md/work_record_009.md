# 作業記録 009: 未投入試合データ投入後の選手重複整理・プロフィール補完フロー
作成日: 2026-08-13

## 背景

2026年5月末までの試合データには、まだDBへ追加していない範囲が残っている。先に試合データを投入して選手・チーム・所属履歴の母集団を最新化し、その後にplayer_idの重複とプロフィール欠損を整理する。

## GitHub Issue

- 親Issue [#24](https://github.com/tj-999-comp/B_Stats_Site/issues/24): 2026年5月末までの未投入試合データをスクレイピング・投入する
- 子Issue [#25](https://github.com/tj-999-comp/B_Stats_Site/issues/25): 試合データ投入後のplayer_id重複整理とプロフィール欠損補完

Issue #25はIssue #24の投入後検証が完了してから開始する。

## 実施フロー

### 1. 未投入試合データの取得・投入（Issue #24）

1. 2026-05-31（JST）までを対象に、DBの `schedule_key` と `scraper/data/` の追跡済みファイルを照合する。
2. 未取得分を公式サイトからスクレイピングし、取得済み未投入分と合わせて対象を確定する。
3. 失敗キーをリトライし、dry-run、得点監査、件数を確認する。
4. 古い試合から順に、通常のUpsertフローでDBへ投入する。
5. `games`、`teams`、`game_team_stats`、`players`、`player_game_stats` の件数、重複、参照整合性、未投入・失敗キーを検証する。

### 2. player_id整理とプロフィール補完（Issue #25）

1. Issue #24完了後のlive DBと追跡済みゲームJSONを再監査する。
2. player_name、旧ID、所属、出場履歴、公式プロフィールを根拠に重複候補を確認する。
3. 同一人物と確定したIDだけを統合し、関連テーブル・履歴・試合成績の重複や欠落を検証する。
4. 統合後に選手・スタッフ相当を再分類し、欠損プロフィール一覧を再生成する。
5. 目視確認で補完値を確定し、補完可能な項目だけを `supabase/patches/` に保存する。
6. DBへ反映する場合は `backup → verify（実行前）→ fix → verify（実行後）` の4ファイル構成にする。問題があれば `rollback → verify` を実行する。

## 欠損の扱い

- `last_seen_team_id` は、所属チームがまだ取り込まれていない場合は無理に補完しない。
- `league_registered_nationality` と `birthplace` は、ID統合の保留、特別指定選手など根拠が不足する場合は空欄を許容する。
- 推測値で補完せず、既存の非空値を上書きしない。
- スタッフ相当・ダミーIDは補完対象から除外し、除外理由を記録する。

## 関連Issue

- [#12](https://github.com/tj-999-comp/B_Stats_Site/issues/12): 選手プロフィールの欠損を補完する
- [#21](https://github.com/tj-999-comp/B_Stats_Site/issues/21): 残存選手プロフィール欠損を調査・補完する
- [#22](https://github.com/tj-999-comp/B_Stats_Site/issues/22): スタッフ相当判定フラグ
- [#23](https://github.com/tj-999-comp/B_Stats_Site/issues/23): 45848〜45865周辺の分割player_id調査・統合
