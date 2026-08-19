# 作業記録 014: Issue #29 公開前検証と自動公開フローの整理
作成日: 2026-08-20

## 概要

GitHub Issue #29に対応し、作業記録を自動公開へつなげる前段として、001〜013のmetadata、生成元validator、HTML再生成check、CI検証を整備した。あわせて、生成元の`B_Stats_Site`と公開側の`sandbox-pages`が分担する実際の公開フローを作業記録として整理した。

## 目的

作業記録を`main`へ反映したとき、公開要求の前に命名、metadata、HTML再現性、依存ファイル、HTML・CSS・URL安全性を自動検証できるようにする。最終的な公開処理は生成元が直接行わず、`sandbox-pages`側が固定commitを受け入れてGitHub Pagesへ反映する構成とする。

## 対象

- 番号付き作業記録: `work_record_001`〜`work_record_013`
- 生成元リポジトリ: `tj-999-comp/B_Stats_Site`
- 公開リポジトリ: `tj-999-comp/sandbox-pages`
- 公開方式: `source_html`
- project_id: `B_Stats_Site`

## 実施事項

- `work-records/metadata/work_record_001.yml`〜`work_record_013.yml`をschema version 1で追加した。
- metadataに`title`、`date`、`project_id`、`tags`、`publish`を記録した。
- `scripts/dev/validate_work_record_source.py`を追加し、Markdown・metadata・HTMLの同一basename、metadataの型と値、日付・タイトル一致を検証するようにした。
- 同validatorで、HTML要素・属性、URL scheme、相対パス、HTMLから参照するローカルファイル、CSSの外部参照・実行構文を検証するようにした。
- `README.md`、`design.md`、`work_record.css`をsource_htmlのsupport fileとして確認するようにした。
- `phase_1_tasks.html`と`scraping_db_automation.html`を番号付き公開対象から除外するfixtureを追加した。
- `.github/workflows/validate-work-record-filenames.yml`へ、converterの再生成check、source validator、fixture検証を追加した。
- `work-records/README.md`へmetadata形式、公開候補commitの確認方針、自動公開時の責務分担を追記した。

## 実際の公開フロー

```text
B_Stats_Siteで作業記録を変更
  ↓
mainへPush
  ↓
B側CIで命名・metadata・HTML再生成・安全性を検証
  ↓（成功した場合だけ）
publish: true のbasename、project_id、source SHAを抽出
  ↓
sandbox-pagesへworkflow_dispatchで公開要求
  ↓
sandbox-pagesが指定commit SHAを取得して再検証
  ↓（受入成功した場合だけ）
projects/B_Stats_Siteへ反映
  ↓
provenance manifestを記録
  ↓
GitHub Pagesへdeploy
```

生成元側は公開リポジトリをcheckout、編集、commit、pushしない。`B_Stats_Site`側の公開要求workflowは手動起動を復旧経路として残し、手動E2E確認後に`main`更新時の自動要求へ移行する。

## Issueとの関係

- #28の親ディレクトリREADMEリンク修正は完了済みである。
- #29は今回の検証基盤とmetadata追加の対象である。
- #30は`B_Stats_Site`側の手動公開要求workflowを追加する次工程である。
- #31は実作業記録1件を使った手動E2E確認である。
- #32は#31と公開側の受入確認が安定した後に、`main`更新時の自動公開要求を有効化する工程である。

## 検証

- `.venv311/bin/python scripts/dev/validate_work_record_source.py` が成功した。
- `.venv311/bin/python scripts/dev/validate_work_record_source.py --check-fixtures` が成功した。
- `.venv311/bin/python -m scripts.dev.convert_work_records_to_html --check` が成功した。
- `.venv311/bin/python scripts/dev/validate_work_record_filenames.py` が成功した。
- `.venv311/bin/python -m compileall -q scripts/dev` が成功した。
- `git diff --check` が成功した。

## 完了判定

Issue #29の対象範囲を001〜013へ拡張し、metadata、生成元validator、HTML再生成check、support file依存、安全性検証、補助HTMLの除外fixture、CI連携、公開候補commitの運用記録を追加した。自動公開そのものと公開側の受入workflowは、#30以降の別工程として残っている。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは14件だった。#28は2026-08-19に完了している。

### 親子関係

```text
#7（未完了・親Issue）
└── #8（完了・子Issue）
#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（未完了・子Issue）
└── #23（未完了・子Issue）
#24（完了・親Issue）
└── #25（完了・子Issue）
```

GitHubのsub-issues APIで登録された親子関係を記載した。親子登録のないIssueは、優先順位一覧の関係・着手条件に記載する。

### 優先順位順の未完了一覧

優先順位は `github_issue_status_policy.json` の運用設定を使い、設定のないIssueは既定値P3として記載する。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P1 | [#22](https://github.com/tj-999-comp/B_Stats_Site/issues/22) [DB] スタッフ相当判定フラグを追加してプロフィール欠損一覧から除外する | 未完了 | #12の子Issue。#25と関連 |
| 2 | P1 | [#23](https://github.com/tj-999-comp/B_Stats_Site/issues/23) [DB] 45848〜45865周辺の分割player_idを調査・統合する | 未完了 | #12の子Issue。#25と関連 |
| 3 | P2 | [#13](https://github.com/tj-999-comp/B_Stats_Site/issues/13) [DB] player_slot_category の値を正規化する | 未完了 | #25完了後が適切 |
| 4 | P2 | [#14](https://github.com/tj-999-comp/B_Stats_Site/issues/14) [DB] attendance 欠損14試合を調査・補完する | 未完了 | 独立 |
| 5 | P2 | [#16](https://github.com/tj-999-comp/B_Stats_Site/issues/16) [DB] live DB・再構築SQL・テーブル定義のスキーマ差異を解消する | 未完了 | 独立 |
| 6 | P2 | [#18](https://github.com/tj-999-comp/B_Stats_Site/issues/18) [DB] 空の player_id_map と旧ID名寄せ経路を検証する | 未完了 | #23と関連 |
| 7 | P3 | [#7](https://github.com/tj-999-comp/B_Stats_Site/issues/7) 試合のスクレイピングデータ精査 | 未完了 | #24と範囲が重なる |
| 8 | P3 | [#9](https://github.com/tj-999-comp/B_Stats_Site/issues/9) 課題解決の原案を立てる | 未完了 | 探索テーマ |
| 9 | P3 | [#15](https://github.com/tj-999-comp/B_Stats_Site/issues/15) [DB] 過年度の plus_minus・背番号欠損を調査する | 未完了 | 独立 |
| 10 | P3 | [#17](https://github.com/tj-999-comp/B_Stats_Site/issues/17) [DB] play_by_play未投入と存在フラグの整合性を整理する | 未完了 | 独立 |
| 11 | P3 | [#29](https://github.com/tj-999-comp/B_Stats_Site/issues/29) [Work records] 001〜010のmetadataと生成元validator・CIを追加する | 未完了 | 独立。優先度未設定 |
| 12 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 13 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 14 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
