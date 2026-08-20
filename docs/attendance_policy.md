# games.attendance の意味と欠損調査
作成日: 2026-08-20

## 定義

`games.attendance` は、公式の試合単位データで発表された観客数を表す。値の扱いは次のとおりとする。

- 正の整数: 公式に発表された当該試合の観客数。
- `0`: 公式に当該試合が無観客で実施されたと確認できる場合だけ設定する。
- `NULL`: 公式に当該試合の観客数が掲載されていない、またはイベント全体・開催日全体の人数しか確認できず、当該試合へ一意に割り当てられない場合。

イベント全体、開催日全体、アリーナの延べ人数は、個別試合の `attendance` へ代入しない。中止・未実施の試合は観客数0とは扱わず、試合行の状態と別に扱う。

## Issue #14 の調査結果

対象14件を、追跡済み正本JSON、`scraper/logs/game_detail_fetch_log.json`、B.LEAGUE公式試合詳細ページで照合した。2026-08-20の読み取り結果では、14件すべてが次の状態だった。

- 正本JSONに `game` が存在し、`error` はない。
- `source_tab` は `4`。
- 正本JSONの `Game.Attendance` は `null`。
- 公式試合詳細ページの `Game.Attendance` も `null`で、画面上の人数欄も空。
- 取得失敗ログの `failed_games` / `failed_schedule_keys` に対象キーはない。
- 得点と試合終了フラグがあり、無効試合・中止を示す状態ではない。

| schedule_key | 試合日 | 対戦 | 正本JSON | 公式詳細 |
|---:|---|---|---|---|
| 6421 | 2021-04-25 | SR渋谷 - 北海道 | `season_2020-2021/games_2020-21_2021-04-01_2021-04-30.json` | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6421) |
| 6419 | 2021-04-25 | A東京 - 秋田 | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6419) |
| 6360 | 2021-04-28 | 大阪 - 横浜BC | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6360) |
| 6450 | 2021-05-01 | 大阪 - 滋賀 | `season_2020-2021/games_2020-21_2021-05-01_2021-05-31.json` | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6450) |
| 6451 | 2021-05-02 | 大阪 - 滋賀 | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6451) |
| 6369 | 2021-05-05 | A東京 - 横浜BC | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6369) |
| 6938 | 2021-05-15 | 大阪 - 川崎 | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6938) |
| 6939 | 2021-05-16 | 大阪 - 川崎 | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=6939) |
| 7720 | 2022-03-12 | 三河 - 滋賀 | `season_2021-2022/games_2021-22_2022-03-01_2022-03-31.json` | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=7720) |
| 7721 | 2022-03-13 | 三河 - 滋賀 | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=7721) |
| 501174 | 2023-01-14 | B.LEAGUE U18 WEST - EAST | `season_2022-2023/games_2022-23_2023-01-01_2023-01-31.json` | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=501174) |
| 502494 | 2024-01-13 | RISING STARS - ASIA ALL-STARS | `season_2023-2024/games_2023-24_2024-01-01_2024-01-31.json` | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=502494) |
| 502495 | 2024-01-14 | U18 JADE - HELIOS | 同上 | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=502495) |
| 503881 | 2025-01-19 | U18 JADE - HELIOS | `season_2024-2025/games_2024-25_2025-01-01_2025-01-31.json` | [公式](https://www.bleague.jp/game_detail/?ScheduleKey=503881) |

## 個別試合へ流用しなかった人数

公式発表には、個別試合の人数ではなくイベントまたは開催日単位の人数があるケースがある。

- `501174`: 2023年水戸大会の公式発表はメインイベントの入場者数3,146名であり、U18試合の人数ではない。
- `502494` / `502495`: 2024年沖縄大会の公式発表はDAY2 6,379名、DAY3 7,357名のアリーナ入場者数であり、各試合の人数ではない。

したがって、これらを含む14件はすべて「公式未掲載」と分類し、`0`への変更も正の値への補完も行わず、`NULL`を維持する。取得漏れではないため、スクレイパーの修正も不要である。

## 変更・適用方針

今回の調査ではDB更新および正本JSONの変更は発生しない。今後、公式が個別試合の観客数を公開した場合は、変更前の対象行を保存したうえで、別途 `backup`、`verify`、`fix`、`rollback` の4種SQLを用意してからユーザーが適用する。
