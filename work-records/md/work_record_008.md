# 作業記録 008: GitHub Issue #21 欠損プロフィール目視補完・DBパッチ準備
作成日: 2026-08-13

## 対象

GitHub Issue #21の目視確認用CSVをもとに、補完可能な選手プロフィールをlive DBへ反映するためのSQLを準備する。

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

## GitHub Issue状況

確認日: 2026-08-13（JST）

対象: `tj-999-comp/B_Stats_Site` のopen GitHub Issue 12件

### 優先順位の考え方

- `P0`: 現在のデータ基盤を最新化し、後続作業を解放する最優先項目。
- `P1`: P0完了後に着手する同一ワークストリーム、またはその中核となる項目。
- `P2`: データ品質・再構築性を改善する重要項目。P0/P1と独立して進められる。
- `P3`: 仕様整理、過年度調査、探索的なテーマ。上位の整合性対応後に進める。

優先順位はGitHub上のラベルではなく、2026-08-13時点の依存関係と影響範囲をもとにした作業順の提案である。

### 親子・関連構造

```text
#24 [NEW] 未投入試合データの取得・投入                         P0
└── #25 [NEW] 投入後のplayer_id整理・プロフィール補完          P1 / #24待ち
    ├── 関連: #23 分割player_idの調査・統合                    P1
    └── 関連: #22 スタッフ相当判定フラグ                       P1

#12 選手プロフィール欠損補完                                  完了した親
├── #21 残存プロフィール欠損                                  完了した子
├── #22 スタッフ相当判定フラグ                                 P1
└── #23 分割player_idの調査・統合                              P1

#7  全シーズンのスクレイピングデータ精査                       P3
└── 関連: #24 が2026年5月末までの未投入範囲を具体化
```

`#24 → #25` と `#12 → #21 / #22 / #23` はGitHub上で正式に登録された親子関係である。`#22` と `#23` は `#25` から参照する関連Issueでもある。

### 優先順位順一覧

| 順位 | 優先度 | GitHub Issue | 関係・着手条件 |
|---:|---|---|---|
| 1 | P0 | [#24 2026年5月末までの未投入試合データをスクレイピング・投入する](https://github.com/tj-999-comp/B_Stats_Site/issues/24) **NEW 2026-08-13** | 親。#25をブロック |
| 2 | P1 | [#25 試合データ投入後のplayer_id重複整理とプロフィール欠損補完](https://github.com/tj-999-comp/B_Stats_Site/issues/25) **NEW 2026-08-13** | #24の子。#24完了後 |
| 3 | P1 | [#23 45848〜45865周辺の分割player_idを調査・統合する](https://github.com/tj-999-comp/B_Stats_Site/issues/23) | #12の子。#25と関連 |
| 4 | P1 | [#22 スタッフ相当判定フラグを追加する](https://github.com/tj-999-comp/B_Stats_Site/issues/22) | #12の子。#25と関連 |
| 5 | P2 | [#16 live DB・再構築SQL・テーブル定義の差異を解消する](https://github.com/tj-999-comp/B_Stats_Site/issues/16) | 独立 |
| 6 | P2 | [#18 空のplayer_id_mapと旧ID名寄せ経路を検証する](https://github.com/tj-999-comp/B_Stats_Site/issues/18) | #23と強く関連 |
| 7 | P2 | [#13 player_slot_categoryの値を正規化する](https://github.com/tj-999-comp/B_Stats_Site/issues/13) | #25後が安全 |
| 8 | P2 | [#14 attendance欠損14試合を調査・補完する](https://github.com/tj-999-comp/B_Stats_Site/issues/14) | 独立 |
| 9 | P3 | [#15 過年度のplus_minus・背番号欠損を調査する](https://github.com/tj-999-comp/B_Stats_Site/issues/15) | 独立 |
| 10 | P3 | [#17 play_by_play未投入と存在フラグの整合性を整理する](https://github.com/tj-999-comp/B_Stats_Site/issues/17) | 独立 |
| 11 | P3 | [#7 試合のスクレイピングデータ精査](https://github.com/tj-999-comp/B_Stats_Site/issues/7) | #24と範囲が重なる |
| 12 | P3 | [#9 課題解決の原案を立てる](https://github.com/tj-999-comp/B_Stats_Site/issues/9) | 探索テーマ |

### 推奨する進行順

1. #24で未投入対象を確定し、取得・dry-run・投入・検証を完了する。
2. #24完了後に#25を開始し、#23のID整理と#22の分類結果を取り込む。
3. #25完了後に#13を進め、選手カテゴリの正規値を固定する。
4. 並行可能な基盤整備として#16、限定的な品質改善として#14を進める。
