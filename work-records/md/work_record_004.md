# 作業記録 004: playersのbirthplace欠損調査ログ（スレッド分割前サマリ）
作成日: 2026-06-02

## 背景
- `players` テーブルの `birthplace` が想定より未取得に見えるため、取得元サイトと実データのカバレッジを確認した。
- 以降はスレッドを分けて、`league_registered_nationality` / `birthplace` の補完調査を進める前提。

## このスレッドで確認したこと
1. 参照サイト（取得元）
- ベース: `https://www.bleague.jp`
- 選手プロフィール: `https://www.bleague.jp/roster_detail/?PlayerID=<id>`
- 主な参照コード:
  - `scripts/db/config.py` (`BASE_URL`)
  - `scripts/dev/enrich_players_profile.py` (`ROSTER_DETAIL_URL`)
  - `scripts/dev/fetch_profile_fields_parallel.py`

2. 取得ロジック
- `enrich_players_profile.py` の `extract_profile_value()` で下記順に抽出:
  - `dt/dd`
  - `th/td`
  - `li` のテキスト列
- 対象ラベル:
  - `リーグ登録国籍` -> `league_registered_nationality`
  - `出身地` -> `birthplace`

3. players.json（ローカルファイル）確認結果
- 対象: `scraper/data/players.json`（713件）
- `birthplace` 取得済み: 646
- `birthplace` 未取得: 67
- `league_registered_nationality` 取得済み: 673
- `league_registered_nationality` 未取得: 40

4. DB全体（Supabase players）確認結果
- 対象: `players` 全件（1100件）
- `birthplace IS NULL`: 474
- 結論: 今後は「DB全体でのNULL 474件」を基準に進める。

## 補足調査（欠損理由の切り分け）
- 未取得サンプルで `roster_detail` ページを直接確認したところ、
  - `リーグ登録国籍` は値あり
  - `出身地` はラベルのみで値が空
  というケースが存在。
- 例（確認IDの一部）: `33042`
  - 抽出結果: `league='アメリカ合衆国'`, `birth=None`
  - DOM上も `['出身地']` のみ（値なし）

## 本スレッドの着地
- `birthplace` 欠損は、抽出失敗だけでなく「参照元ページに値が掲載されていない」ケースが含まれる。
- 次スレッドでは、補完対象を次の2項目に絞って継続する:
  - `league_registered_nationality`
  - `birthplace`
