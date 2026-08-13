# Issue_ex_007: GitHub Issue #12 players監査・差分補完基盤
作成日: 2026-08-05

## 対象

GitHub Issue #12「[DB] 選手プロフィールの欠損を補完する」のうち、
次の2点を対象とした。

1. live DBの全件取得、差分のみの更新、選手別監査レポートを安全に実行できる基盤を作る。
2. live `players` を別ファイルへ出力し、正本 `scraper/data/players.json` との差分をレビューする。

live DBへの更新と正本JSONの更新はこの段階では行わない。

## 実装

- `scripts/db/db.py`
  - `player_id` の安定順と `range` ページングで、PostgRESTの1,000件上限を超えて全件取得するようにした。
- `scripts/dev/audit_players_snapshot.py`
  - live全件を別JSONへ保存する。
  - liveのみ、localのみ、重複ID、項目別欠損、共通IDの値差分、localから補完可能なlive欠損を選手単位で出力する。
- `scripts/dev/fill_missing_player_profile_fields.py`
  - 指定なしではlive DBを更新しない。
  - `--apply` 指定時だけ、取得できた欠損列の差分を更新する。
  - 監査後の同時更新を検出できるよう `updated_at` を更新条件に含める。
  - 選手別に公式取得成功、公式空欄、404、通信失敗、提案差分、反映結果を記録する。
- `scripts/dev/fetch_profile_fields_parallel.py`
  - 429、5xx、接続例外に指数バックオフ付きの再試行を追加した。

## live差分監査結果

2026-08-05に次の読み取り専用コマンドを実行した。

```bash
python -m scripts.dev.audit_players_snapshot \
  --local-input scraper/data/players.json \
  --snapshot-output /tmp/b_stats_issue12_players_live_20260805.json \
  --report /tmp/b_stats_issue12_players_audit_20260805.json
```

### IDと重複

| 項目 | 件数 |
|---|---:|
| live行数 / ユニークID | 1,100 |
| local行数 | 713 |
| localユニークID | 693 |
| 共通ID | 693 |
| liveのみ | 407 |
| localのみ | 0 |
| local重複ID / 余分行 | 20 / 20 |

### live欠損の内訳

| 項目 | live欠損 | liveのみ407 ID内の欠損 |
|---|---:|---:|
| `player_name_e` | 30 | 30 |
| `birthplace` | 156 | 89 |
| `league_registered_nationality` | 34 | 28 |
| `player_slot_category` | 216 | 216 |
| `last_seen_team_id` | 8 | 0 |
| `last_seen_jersey_number` | 49 | 46 |

### 共通693 IDの値差分

- `player_name_j`、`player_name_e`、`birthplace`、`player_slot_category`、`last_seen_jersey_number` は、
  現行UPSERTと同じlocal配列の後勝ちで比較すると差分なし。
- `league_registered_nationality` は34件で差分があり、すべてliveに値がありlocalが欠損している。
- `last_seen_team_id` は8件で、localがすべて `2486`、liveがNULL。
  過去のUPSERTで `teams` にないIDをNULLへ正規化した結果と一致する。
- liveの `last_seen_jersey_number` 欠損のうち、localの重複行から値を得られるのは
  `player_id=8651`の `55` 1件だけである。
- `player_name_e` と `last_seen_jersey_number` がともに欠損する行は30件。
  削除条件には使わず、選手外行のレビュー候補としてのみ報告する。

liveスナップショットの列に `nationality` は存在しなかった。
そのため、現行 `players.json` 全列の無条件UPSERTは実行しない。

## 3件プレビュー

`--apply` なし、`--limit 3 --workers 1` で取得・差分生成を確認した。

| player_id | 結果 | 提案 |
|---|---|---|
| `10256` | 公式取得成功、出身地は公式空欄 | なし |
| `10265` | 既存の登録国籍・出身地から導出可能 | `player_slot_category=外国籍選手` |
| `10267` | 公式プロフィール404 | なし |

集計は `proposed_rows=1`、`applied_rows=0`、`apply_errors=0` で、
live DBの更新は発生していない。

## 未実施と次の判断

- live DBの更新、正本JSONの上書き、削除は未実施。
- `last_seen_team_id` はプロフィール値ではなく、対象大会と最新試合の定義を確定してから再計算する。

## 選手・スタッフ分類

追跡済みの月次ゲームJSON 74ファイルに含まれる `PeriodCategory == 18` の
130,342行を走査した。次のいずれかを満たす行だけを実選手行とした。

- 背番号がある
- `PlayingFlg` がtrue
- `StartingFlg` がtrue
- `PlayTime` が正の `MM:SS`

この条件で126,282行を選手として採用し、4,060行をスタッフ相当として除外した。
同じIDが採用側と除外側の両方に出るケースは0件だった。

live 1,100 IDの分類は次のとおり。

| 分類 | 件数 | 方針 |
|---|---:|---|
| 選手 | 968 | 保持 |
| スタッフ相当 | 47 | 補完・今後の投入から除外 |
| ダミーID | 1 | `999999999`。除外 |
| 追跡済み試合に未出現 | 84 | 自動除外せず保持 |

未出現84 IDのうち83 IDは現行正本にも存在し、比較的新しいシーズンの選手を含む。
したがって「追跡済み月次ファイルにない」こと自体は削除根拠にしなかった。
除外48 IDのうち現行正本にあるのはスタッフ相当 `45873` とダミー `999999999` の2 IDだった。

live DBも読み取り専用で依存行数を確認した。

| テーブル・参照 | 対象行数 |
|---|---:|
| `players` | 48 |
| `player_game_stats` | 4,060 |
| `player_name_history` | 59 |
| `player_affiliations` | 70 |
| `player_id_map.player_id` | 0 |
| `player_id_map.old_player_id` | 0 |

`player_game_stats` の4,060行は月次JSONでスタッフ相当と判定した4,060行と一致する。
canonical FKは同テーブルから `players` への削除を制限するため、反映時は子行を先に
バックアップ・削除し、その後に48 master行を削除する必要がある。

投入時の再混入を防ぐため、`scripts/db/player_boxscore.py` に同じ判定を共通化し、
`players` と `player_game_stats` の両抽出、およびID名寄せ候補収集で使用するようにした。

## 全対象プロフィール監査

分類後の1,052 IDを対象とし、liveスナップショットと初回取得結果のキャッシュを使って
`--apply` なしで全件監査した。

| 結果 | 件数 |
|---|---:|
| 監査対象 | 280 |
| 既存プロフィールから安全に区分導出 | 165 |
| 公式プロフィールから差分提案 | 1 |
| 公式404 | 75 |
| 公式項目が空欄 | 33 |
| 導出可能な変更なし | 6 |
| 提案行合計 | 166 |
| DB反映 | 0 |

公式プロフィールから値を提案できた1件は `player_id=43470` で、
`league_registered_nationality=ユース育成特別枠`、`birthplace=鹿児島県`、
`player_slot_category=日本人選手` だった。

`リーグ登録国籍=帰化` の3件は、日本人選手・外国籍選手のどちらにも自動分類しないよう
判定を修正した。提案反映後も `player_slot_category` は35件、`birthplace` は108件、
`league_registered_nationality` は29件が未解消であり、推測による補完は行わない。

## 正本候補とスキーマ整合

liveスキーマには `players.nationality` がなく、2026-05-27の運用SQLでも同列を削除していた。
このlive実態を現行仕様と判断し、投入コード、補助スクリプト、canonical rebuild SQL、
テーブル定義から同列を除外した。`league_registered_nationality`、`birthplace`、
`player_slot_category` は引き続き保持する。liveへのDDL適用は行っていない。

監査済みliveを基準に、除外48 IDを外し、提案166件だけを重ねたレビュー用正本候補を
次へ生成した。現行 `scraper/data/players.json` は上書きしていない。

```text
/tmp/b_stats_issue12_players_canonical_candidate_20260805.json
/tmp/b_stats_issue12_players_canonical_candidate_report_20260805.json
```

候補は1,052行・重複0 IDで、現行正本に対して候補のみ361 ID、正本のみ2 ID
（除外対象の `45873`、`999999999`）だった。候補の残存欠損は、英名0、出身地108、
リーグ登録国籍29、選手区分35、最終所属8、最終背番号1である。

## 残作業

- 正本候補1,052行と除外48 IDをレビューし、`scraper/data/players.json` の置換可否を決める。
- live DBへは、`player_game_stats` 4,060行と `players` 48行の除外、および補完166件を別操作として、バックアップ・件数ガード・復旧方法を用意してから反映する。
- `last_seen_team_id` 8件と `last_seen_jersey_number` 1件はプロフィール補完から分離して扱う。
- 帰化3件を含む未確定区分35件は、公式の選手区分を確認できる別根拠が得られるまで保留する。

## 反映SQL・ロールバックSQL

2026-08-11に、liveへ適用するSQL一式を作成した。その後、バックアップ、事前検証、本番反映、反映後検証まで完了した。

- `supabase/sql/20260811_backup_issue_12_players.sql`
  - プロフィール166行、削除対象players48行、`player_game_stats` 4,060行、名前履歴59行、所属履歴70行を永続バックアップする。
- `supabase/sql/20260811_verify_issue_12_players.sql`
  - 変更予定の項目別件数と、現在状態が反映前・反映後・想定外のいずれかを読み取り確認する。
- `supabase/sql/20260811_fix_issue_12_players.sql`
  - `updated_at` の楽観的ガード付きでプロフィール166件を補完し、関連行を先に削除してからplayers48行を削除する。
- `supabase/sql/20260811_rollback_fix_issue_12_players.sql`
  - 上記バックアップ表から対象行を復元し、トリガーが生成する履歴・所属行もバックアップ状態へ戻す。

実行順はバックアップSQL → 検証SQL（変更内訳と反映前状態） → 反映SQL → 検証SQL（反映後状態）。問題があればロールバックSQLを実行し、検証SQLで復元状態を確認する。

安全に確定できなかった残存欠損は、GitHub Issue [#21](https://github.com/tj-999-comp/B_Stats_Site/issues/21) を Issue #12 の子Issueとして作成し、対応を保留・移管した。
