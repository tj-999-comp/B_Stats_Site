# 日付解決ルール（スクレイパー挙動の補足）

スクレイパーで取得するゲーム日はサイト側の表示と内部コンテキストの不整合が起きる場合があります。
このリポジトリでは以下のルールで日付の解決を行います（実装: `scraper/src/game_scraper.py`, 補正スクリプト: `scraper/scripts/fix_game_datetimes.py`）。

- `date_to_schedule_keys` は `YYYY-MM-DD` -> schedule_key のマップで、1つの `schedule_key` が複数日（例: 公開カレンダーと内部コンテキスト差）に現れることがあります。
- スクレイパーは各 `schedule_key` ごとに「候補日リスト（candidate dates）」を保持します。
- contexts（game_detail）から取得される `GameDateTime`（UNIX秒）を JST に変換した日付が候補リストに含まれる場合は、その候補日を優先して採用します。
- contexts の日付が候補に含まれない場合は、候補リストの先頭（JSON に現れる順）をフォールバック値として採用します。
- 候補が複数あり contexts の日付と一致しない場合は警告ログを出力し、手動確認できるようにします。

目的: サイト側のカレンダー表示（公開ページ）と内部 contexts の取り扱いが食い違うケースで、可能な限り contexts 側の時刻情報を尊重しつつ、スクレイプ段階での一貫性を保つことです。

## 実行手順（手早く JSON を修正する）

1. 元ファイルのバックアップを取る（必須）:

```bash
cp scraper/data/games_YYYY-mm_DDRANGE.json scraper/data/games_YYYY-mm_DDRANGE.json.bak
```

2. 補正スクリプトを実行して修正済 JSON を作る:

```bash
python3 scraper/scripts/fix_game_datetimes.py \
  scraper/data/games_YYYY-mm_DDRANGE.json \
  scraper/data/games_YYYY-mm_DDRANGE_fixed.json
```

3. （必要なら）再スクレイプして最終 JSON を得る場合は `scraper/src/game_scraper.py` の `save_date_range_games` を使います。例:

```bash
python3 - <<'PY'
from scraper.src.game_scraper import save_date_range_games
from datetime import date
save_date_range_games(date(2025,5,1), date(2025,6,30), '2024-25')
PY
```

## DB 更新（Postgres） - 例

手元の DB にある `games` テーブルを直接修正する場合の SQL 例を示します。まずは更新前の確認を行ってください:

```sql
SELECT schedule_key, game_datetime_unix, game_datetime, game_date
FROM games
WHERE schedule_key = 503903;
```

`schedule_key = 503903` を `2025-05-27`（JST 19:05 の時刻を保持したい場合、UNIX=1748340300）に更新する SQL:

```sql
UPDATE games
SET
  game_datetime_unix = 1748340300,
  game_datetime = to_char(to_timestamp(1748340300) AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI'),
  game_date = to_char(to_timestamp(1748340300) AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo', 'YYYY-MM-DD'),
  updated_at = NOW()
WHERE schedule_key = 503903;
```

注意: 直接 DB を変更する前に必ずバックアップ（スナップショット）を取得してください。

## 発生原因と運用提案

- 原因: サイト側のスケジュールトピックが同一 `schedule_key` を複数日のカレンダーに掲載しているため。どの日を「公式の開催日」とするかは外部仕様に依存します。
- 運用提案: 不一致を検知した `schedule_key` をログや専用ファイルに蓄積し、手動で確認するワークフローを推奨します。自動化が必要なら、不一致検知時に追加でサイトのカレンダー API を問い合わせる機能を実装可能です。
