# Colab スクレイピング スターター

このフォルダには、Google Colab で実行できる B.LEAGUE 試合データ取得用スクレイパーが入っています。

## ファイル構成

- `requirements.txt`: Colab ランタイムで必要な依存パッケージ
- `bleague_parallel_scraper.py`: 並列スクレイピングのコア処理
- `run_scrape_colab.py`: Colab セルから呼び出す CLI エントリーポイント

## Colab セットアップ

以下のセルを上から順番に実行してください。

### 1) Google Driveをマウントして、リポジトリルートへ移動

```python
from google.colab import drive
drive.mount('/content/drive')
%cd /content/drive/MyDrive/git-tj999/B_Stats_Site
```

Google Drive上に配置済みのリポジトリを使用します。GitHubからのCloneは行いません。

### 2) 依存パッケージをインストール

```python
!pip install -r Colab/requirements.txt
```

### 3) スクレイピング実行（単日）

```python
!python Colab/run_scrape_colab.py \
  --date 2024-10-05 \
  --season 2024-25 \
  --league B1 \
  --output-dir /content/drive/MyDrive/git-tj999/B_Stats_Site/scraper/data
```

### 4) スクレイピング実行（期間指定）

```python
!python Colab/run_scrape_colab.py \
  --start-date 2024-10-01 \
  --end-date 2024-10-07 \
  --season 2024-25 \
  --league B1 \
  --output-dir /content/drive/MyDrive/git-tj999/B_Stats_Site/scraper/data \
  --max-workers 12
```

### 5) 任意: Play-by-Play も取得

```python
!python Colab/run_scrape_colab.py \
  --date 2024-10-05 \
  --season 2024-25 \
  --league B1 \
  --output-dir /content/drive/MyDrive/git-tj999/B_Stats_Site/scraper/data \
  --include-play-by-play
```

## 出力

JSON は次のファイル名で保存されます。

- B1単日: `games_<season>_<date>.json`（既存形式を維持）
- B1期間指定: `games_<season>_<start>_<end>.json`（既存形式を維持）
- B2/B3単日: `games_<league>_<season>_<date>.json`
- B2/B3期間指定: `games_<league>_<season>_<start>_<end>.json`

リーグを指定する場合は、`--league B1`、`--league B2`、`--league B3` のいずれかを指定します。省略時はB1です。

例:

```python
!python Colab/run_scrape_colab.py \
  --date 2018-10-06 \
  --season 2018-19 \
  --league B2 \
  --output-dir /content/drive/MyDrive/git-tj999/B_Stats_Site/scraper/data
```

各 JSON には次のキーが含まれます。

- `date_to_schedule_keys`
- `league`
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
