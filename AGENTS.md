# Codex 作業ガイド
作成日: 2026-08-03

## 適用範囲

- このファイルはリポジトリ全体に適用する。下位ディレクトリに別の `AGENTS.md` が追加された場合は、そちらの指示を優先する。
- コマンドは、特記がない限りリポジトリルートから実行する。特に Python は `python -m scripts...` の形式を使い、`scraper/` へ移動したまま実行しない。
- 作業開始時と終了時に `git status --short` を確認する。既存の変更・未追跡ファイルはユーザーの作業として保持し、依頼に無関係な整形、削除、上書きをしない。

## プロジェクトの現在像

B.LEAGUE 公式サイトから試合情報を取得し、JSON に保存して Supabase PostgreSQL へ投入する統計サイト用リポジトリである。pnpm/Turborepo のモノレポ内に、GitHub Pages 向け静的 Next.js と Vercel 向け SSR Next.js の2構成を置いている。

現在の実装の中心は Python スクレイパー、JSON 変換・UPSERT、Supabase SQL である。`apps/web-static` は static export の雛形、`apps/web-vercel` は認証 middleware 以外ほぼ雛形で、`packages/shared-ui` のコンポーネントも未実装である。README にある構想を実装済みの機能として扱わないこと。

主なデータフローは次のとおり。

1. `scripts/scraping/` がスケジュール API と game detail HTML を取得する。
2. 取得結果と失敗情報を `scraper/data/`、`scraper/logs/` に保存する。
3. `scripts/db/upsert_games.py` が外部 JSON の PascalCase フィールドを現行 DB の snake_case 行へ変換する。
4. `scripts/db/db.py` が Supabase へチャンク単位で UPSERT する。
5. 2つの Next.js 構成が同じ Supabase を参照する想定である。

## まず参照するファイル

| 対象 | 正本・入口 |
|---|---|
| 全体像 | `README.md`, `docs/architecture.md` |
| ローカル環境 | `docs/setup.md`, `scraper/README.md` |
| スクレイピングと投入順 | `docs/flow.md`, `docs/date_resolution.md`, `scripts/scraping/`, `scripts/db/` |
| 現行 DB 再構築 | `supabase/rebuild/README.md`, `supabase/rebuild/00_rebuild_all.sql`, 分割版 `01`〜`07` |
| DB 定義のスナップショット | `docs/table_definition.md` |
| CI・デプロイの実挙動 | `.github/workflows/*.yml` |
| 変更経緯 | `docs/changelog.md`, `work-records/md/work_record_*.md` |
| Colab 版 | `Colab/README.md`, `Colab/bleague_parallel_scraper.py` |

説明と実装が食い違う場合、実行時の挙動は現在のコードと Workflow、再構築の意図は `supabase/rebuild/README.md` と現行 SQL を優先する。`docs/table_definition.md` は 2026-03-10 時点の live DB スナップショット、`docs/changelog.md` と `work-records/` は履歴資料であり、現在値を保証しない。食い違いを発見したら推測で埋めず、変更対象に関係する文書も合わせて更新するか、未解消の差異として報告する。

## ツールチェーンと初期セットアップ

基準バージョンは CI に合わせて Node.js 20.19 以上の20系、pnpm 9、Python 3.11 以上とする。`package.json` の Node 指定は広いが、現行 lockfile の ESLint 10 系は Node 20.19 以上を要求する。既存のローカル環境を再利用する前にバージョンを確認し、Python 3.11 未満の `.venv` は再利用せず、3.11 以上の環境を別途用意する。

```bash
node --version
pnpm --version

pnpm install --frozen-lockfile

# version manager などで Python 3.11+ を選択してから実行
python --version
python -m venv .venv
source .venv/bin/activate
python -m pip install -r scraper/requirements.txt
```

- 通常の Python 実装には `scraper/requirements.txt` を使う。ルート `requirements.txt` は現在同内容で、`Colab/requirements.txt` は Colab 版専用である。
- `pnpm-lock.yaml` を依存変更なしに書き換えない。依存変更時は該当 `package.json` と lockfile を同じ差分に含める。
- ローカル DB 接続が必要な場合だけ `scraper/.env.example` を元に `scraper/.env` を用意する。スクレイパー／DB用の実装上の変数名は `SUPABASE_URL` と複数形の `SUPABASE_SECRET_KEYS` である。
- Web の公開接続情報は各アプリの `.env.local` に `NEXT_PUBLIC_SUPABASE_URL` と `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` を置く。
- `.env`、`.env.local`、`memo.md` は秘密情報を含み得るローカルファイルである。内容を表示、ログ出力、回答への転載、コミットをしない。

## ディレクトリ別の編集方針

### Python とスクレイパー

- 既存の型注釈、`pathlib.Path`、snake_case、内部 helper の `_` 接頭辞、`argparse` CLI に合わせる。JSON は UTF-8、必要な場合は既存どおり `ensure_ascii=False, indent=2` を使う。
- 外部レスポンスの PascalCase キーを取得層で安易に改名しない。DB への snake_case 変換は `scripts/db/upsert_games.py` に集約する。
- `schedule_key` は整数／`BIGINT`、`team_id` と `player_id` は文字列／`TEXT` という契約を保つ。選手の試合通算行は `PeriodCategory == 18` に加え、背番号、出場フラグ、先発フラグ、正の出場時間のいずれかを持つ行だけを採用し、同カテゴリに混入するスタッフ行を除外する。
- HTTP timeout、各処理の既存 pacing、5xx・接続エラー時のリトライとログ記録を削らない。通常版の game-detail ループは1〜3秒待機するが、schedule API、プロフィール補完、Colab 版には別の間隔・並列度がある。アクセス量を増やす変更は小さい対象で確認する。
- 日付は JST で解決する。`games.year` は暦年ではなくシーズン開始年で、10〜12月は当年、1〜5月は前年とする。同じ `schedule_key` の候補日と contexts 日時の解決規則は `docs/date_resolution.md` を守り、単純な先勝ちに戻さない。
- `player_id_map` による旧 ID から現 ID への名寄せと、履歴トリガーの時系列を壊さない。複数月を投入するときは古い試合から順に扱う。
- 通常運用では `play_by_play` を取得・投入しない。`--include-play-by-play` / `--with-play-by-play` は明示された作業でだけ使う。
- 通常版の取得仕様を変えた場合は、独立実装の `Colab/bleague_parallel_scraper.py` に同じ修正が必要か確認する。

### Web と共有パッケージ

- TypeScript は各 `tsconfig.json` の `strict: true` を維持する。コンポーネントは PascalCase と named export という既存形に合わせる。
- 共通 UI は `packages/shared-ui`、共有可能な Supabase 処理は `packages/supabase-client` に置き、両アプリへの複製を避ける。利用前に各アプリへ `workspace:*` 依存を追加し、`NEXT_PUBLIC_*` を使う browser client と、cookie を扱う `@supabase/ssr` の server client を分離する。現行 `client.ts` を SSR 認証へそのまま流用しない。
- `web-static` では `output: 'export'`、`trailingSlash: true`、未最適化画像という GitHub Pages 制約を維持し、サーバー専用 API を持ち込まない。
- `web-vercel` は SSR/ISR と middleware 認証を前提にする。ただし現行 SQL に現行テーブル向け RLS policy は確認できないため、README の認証構想だけを根拠に安全性を断定しない。
- `packages/supabase-client/src/types.ts` と `queries.ts` は旧 `player_stats` / `team_stats` / `rankings` を参照しており、現行スキーマとは未同期である。新規フロント実装では流用前に現行 SQL と照合する。

### Supabase SQL

- 新規 DB の標準再構築入口は `supabase/rebuild/00_rebuild_all.sql` である。`supabase/migrations/20260221_init.sql` と `supabase/seed.sql` は旧3テーブル構成なので、現行再構築には使わない。
- 再構築 SQL を変更するときは、該当する分割版 `01`〜`07` と統合版 `00_rebuild_all.sql` を同期する。`08_full_schema_with_events.sql` は `play_by_play` を含む旧・未同期案で、現行の players、履歴、games 追加列を欠く。単独で現行構成として使わず、必要なら `00` との差分を解消してから利用する。
- スキーマ、トリガー、投入仕様を変えたら、必要に応じて `supabase/rebuild/README.md`、`docs/table_definition.md`、`docs/flow.md`、`docs/changelog.md` を同じ変更で整合させる。
- `scripts/generate_table_definition_live.mjs` は live Supabase、秘密鍵、ネットワークを使い `docs/table_definition.md` を上書きする。明示依頼と接続先確認なしに実行しない。
- `supabase/patches/` はDB補正用のCSV・JSONなど、目視確認・パッチ入力ファイルの置き場である。スクレイピング取得物や正本JSONを置かない。配置・命名は `supabase/patches/README.md` に従う。
- `supabase/sql/` は一回限りまたは破壊的なデータパッチ・運用 SQL の集約先であり、現行スキーマの正本とはみなさない。新規ファイルは `supabase/sql/README.md` の `YYYYMMDD_<action>_<target>.sql` 命名に従う。
- live DBのデータパッチは、原則として `backup`、`verify`、`fix`、`rollback` の4ファイルを同じIssue・対象名で作成する。実行順は `backup → verify（前）→ fix → verify（後）`、問題時は `rollback → verify（後）` とし、例外はSQL先頭コメントと `supabase/sql/README.md` に理由を残す。

### データ、ログ、文書

- `scraper/data/` は約1.1GBの追跡済み入力・履歴資産である。全体の一括整形、改行変換、削除、再生成をしない。検索や差分確認でも原則除外し、対象シーズン・月を絞る。
- 選手マスタの正本は `scraper/data/players.json` で、`players.csv` は編集・確認用の派生物である。CSV からの import やプロフィール補完は正本 JSON を上書きする点に注意する。
- スクレイパーは既存の同名 JSON と追跡済みログを上書きし得る。検証用出力は可能なら `/tmp` または別名を使い、意図したデータ差分だけを残す。
- 新規 Markdown はタイトル直下に `作成日: YYYY-MM-DD` を入れる。
- `Issue` はGitHub Issueだけを指す。リポジトリ内の調査、実行結果、判断経緯は「作業記録」と呼び、`ローカルIssue` や `Issueログ` という呼称は使わない。
- 作業記録は `work-records/md/work_record_###.md` の3桁ゼロ埋めとし、既存最大番号を確認して採番する。`work-records/` 直下のMarkdownは `README.md` と `design.md` だけにする。
- GitHub Issueの状況、優先順位、親子関係は独立した一覧ファイルにせず、関連する番号付き作業記録へ保存する。HTMLがある場合は、その作業記録HTMLの末尾へ追加する。
- 作業記録のHTMLは `work-records/` 直下へ `work_record_###.html` として置き、作成・編集時は `work-records/design.md` を原則として守る。

## 副作用のある操作

次の操作は通常の検証として実行しない。ユーザーが対象、接続先、実行を明示した場合に限り、対象確認、dry-run、バックアップまたは復旧方法を先に用意する。

Supabase の UPSERT、削除、ID統合は複数リクエストで進み、処理全体を包むトランザクションではない。途中失敗でも成功済みチャンクが残り得るため、実行単位ごとの件数照合、再実行可能性、部分反映からの復旧を先に確認する。

- 外部サイトへのスクレイピングと `--retry-failed --merge-into`。後者は指定 JSON を直接上書きする。
- `python -m scripts.db.upsert_games` の `--dry-run` なし実行。
- `scripts/dev/upsert_players_json.py`、プロフィール補完の `--upsert`、その他 Supabase 更新スクリプト。
- `scripts/dev/enrich_players_profile.py` の既定出力。`--upsert` がなくても入力 JSON を上書きするため、試行時は小さい `--limit` と別 `--output` を使う。
- `scripts/dev/fetch_profile_fields_parallel.py` の既定出力。外部 HTTP にアクセスし、`--output` 省略時は入力の `players.json` を上書きする。
- `scripts/dev/delete_games_by_date.py`、`scripts/dev/merge_player_ids.py --yes`、`supabase/sql/20260308_delete_all_games.sql`。
- rebuild/migration SQL の live DB 適用、`migrate.yml`・`scrape.yml` の dispatch、Pages/Vercel の本番デプロイ。
- `main` への push。`apps/web-static/**` または `packages/**` は Pages、`apps/web-vercel/**` または `packages/**` は Vercel の本番デプロイを起動し、`packages/**` は両方を起動する。

変換だけを確認する場合は入力を必ず明示する。入力省略時の探索先と現在の月次ファイル配置が一致しないため、既定入力に依存しない。なお `--dry-run` は DB の `player_id_map` を取得しないため、ローカル変換と件数の確認用であり、本番時の旧IDから現IDへの読み替えまでは再現しない。

```bash
python -m scripts.db.upsert_games \
  --input scraper/data/season_YYYY-YYYY/games_SEASON_START_END.json \
  --dry-run
```

## 既知のドリフトと注意点

- `.github/workflows/scrape.yml` と `migrate.yml` は現在 `workflow_dispatch` のみである。「毎日自動実行」とする一部ドキュメントより Workflow を優先する。さらに現行 scrape Workflow は引数なし CLI が help を表示して取得せず、後段の入力省略 UPSERT も `season_*` 配下の月次 JSON を見つけられず失敗し得るため、正常なスクレイプ運用として信頼しない。
- `docs/flow.md` や古い docstring の `scraper/scripts/...`、`scraper/src/...` は旧パスである。現在の実体は主に `scripts/scraping/`、`scripts/db/`、`scripts/dev/` にある。
- `docs/setup.md` の `SUPABASE_SECRET_KEY`（単数）は実装と不一致で、Python と Workflow は `SUPABASE_SECRET_KEYS`（複数）を使う。
- `SUPABASE_DB_PASSSWORD` は誤字に見えるが、現行 `migrate.yml` が実際に参照する Secret 名である。変更するときは Workflow と登録済み Secret を同時に移行する。
- `docs/table_definition.md` と live DB、canonical rebuild SQL は同一とは限らない。live 接続をせずに DB の現在状態を断定しない。
- 2026-08-05 の live DB 確認で `players.nationality` が存在しないことを確認済み。選手プロフィールは `player_slot_category`、`league_registered_nationality`、`birthplace` を使い、`nationality` を再導入しない。

## 検証

現時点では pytest、Jest/Vitest、format、独立した typecheck の正式なテストスイートはない。変更範囲に応じて、存在する最小の確認を行い、未実施項目と理由を報告する。

```bash
# 全変更共通
git diff --check
git status --short

# Python の構文確認
PYTHONPYCACHEPREFIX=/tmp/b_stats_pycache python -m compileall -q scripts Colab

# 作業記録の配置・ファイル名を触った場合
python scripts/dev/validate_work_record_filenames.py

# Web を触った場合（依存導入後）
pnpm --filter web-static build
pnpm --filter web-vercel build

# 共有パッケージを触った場合（正式な typecheck script は未整備）
pnpm --filter @bleague-stats/shared-ui exec tsc --noEmit
pnpm --filter @bleague-stats/supabase-client exec tsc --noEmit

# lint wiring は未完成のため best effort
pnpm lint
```

- DB 行変換を変更した場合は、対象を絞った追跡済み月次 JSON を明示して `--dry-run` を追加する。
- フロントは雛形で、ESLint の依存・共有設定の接続も未完成である。build/lint の既存不備による失敗は、依頼と無関係に広げて修正せず、実行コマンドと原因を報告する。
- SQL は静的レビューに加え、実行が依頼範囲なら disposable/local プロジェクトで適用順と完了判定を確認する。live DB を検証先にしない。
- 挙動、スキーマ、Workflow、運用手順を変えた場合は、関連ドキュメントと新規ドキュメントの日付規則まで確認して完了とする。
