# Colab スクレイピング スターター

このフォルダには、Google Colab で実行できる B.LEAGUE 試合データ取得用スクレイパーが入っています。

## ファイル構成

- `requirements.txt`: Colab ランタイムで必要な依存パッケージ
- `bleague_parallel_scraper.py`: 並列スクレイピングのコア処理
- `run_scrape_colab.py`: Colab セルから呼び出す CLI エントリーポイント

## Colab セットアップ

以下のセルを上から順番に実行してください。

### 1) リポジトリを取得して、このフォルダへ移動

```python
!git clone https://github.com/<your-account>/B_Stats_Site.git
%cd /content/B_Stats_Site/Colab
```

リポジトリが private の場合は、Google Drive をマウントして既存のコピーを使ってください。

### 2) 依存パッケージをインストール

```python
!pip install -r requirements.txt
```

### 3) スクレイピング実行（単日）

```python
!python run_scrape_colab.py \
  --date 2024-10-05 \
  --season 2024-25 \
  --output-dir /content
```

### 4) スクレイピング実行（期間指定）

```python
!python run_scrape_colab.py \
  --start-date 2024-10-01 \
  --end-date 2024-10-07 \
  --season 2024-25 \
  --output-dir /content \
  --max-workers 12
```

### 5) 任意: Play-by-Play も取得

```python
!python run_scrape_colab.py \
  --date 2024-10-05 \
  --season 2024-25 \
  --output-dir /content \
  --include-play-by-play
```

## 出力

JSON は次のファイル名で保存されます。

- 単日: `games_<season>_<date>.json`
- 期間指定: `games_<season>_<start>_<end>.json`

各 JSON には次のキーが含まれます。

- `date_to_schedule_keys`
- `game_count`
- `failed_schedule_keys`
- `games`

## 並列実行

`--max-workers` で `game_detail` への並列リクエスト数を調整できます。

Colab での推奨値:

- まずは `8`
- 安定していれば `12` を試す
- 失敗が増える場合は `4` から `6` へ下げる

このスクリプトには、アクセス集中を抑えるためのランダム待機とリトライ処理も入っています。
