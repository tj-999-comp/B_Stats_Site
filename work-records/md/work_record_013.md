# 作業記録 013: Issue #28 作業記録HTMLのヘッダーリンク整理
作成日: 2026-08-20

## 目的

GitHub Issue #28に対応し、公開先によって意味が変わる親ディレクトリREADMEリンクを作業記録HTMLから除去する。ヘッダーリンクは不要とする要件へ変更し、番号付きHTMLと補助HTMLを同じconverterから決定的に生成できる状態にする。

## 実施事項

- `scripts/dev/convert_work_records_to_html.py` のヘッダーを、リンクなしのブランド名表示へ変更した。
- `--check` を追加し、Markdownからの再生成結果と既存HTMLを比較できるようにした。check時はHTMLを書き換えない。
- `--numbered-only` を追加し、補助文書を除外して番号付き作業記録だけを再生成・確認できるようにした。
- 番号付き作業記録 `work_record_001`〜`012` を再生成した。今回の追加差分は `001`〜`011` の11件で、`012` は既存の試験修正と一致した。
- 補助Markdownの出力名を固定し、`phase_1_tasks.md` を `work_record_extra_01.html`、`scraping_db_automation.md` を `work_record_extra_02.html` とした。
- 旧補助HTMLを新しい名前へ置き換え、converterとvalidatorの対応を同期した。

## 成果物

- `scripts/dev/convert_work_records_to_html.py`
- `scripts/dev/validate_work_record_filenames.py`
- `work-records/README.md`
- `work-records/work_record_001.html`〜`work-records/work_record_013.html`
- `work-records/work_record_extra_01.html`
- `work-records/work_record_extra_02.html`

## 検証

- `.venv311/bin/python -m scripts.dev.convert_work_records_to_html --check` が成功した。
- `.venv311/bin/python -m scripts.dev.convert_work_records_to_html --numbered-only --check` が成功した。
- `.venv311/bin/python scripts/dev/validate_work_record_filenames.py` が成功した。
- converterとvalidatorをPython 3.11で構文確認した。
- `git diff --check` が成功した。
- 番号付きHTMLと補助HTMLのヘッダーにリンクがなく、親ディレクトリREADME参照が残っていないことを確認した。
- PC表示、320px表示、ローカルリンク、console errorについて、ユーザー確認で問題がないことを確認した。

## 完了判定

Issue #28の要件変更後の完了条件を満たした。作業記録本文、basename、既存の番号付き公開URLは変更していない。補助HTMLは `work_record_extra_01.html`、`work_record_extra_02.html` へ整理した。

## GitHub Issue状況（2026-08-20時点の現在値）

確認日: 2026-08-20（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは15件だった。

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
| 11 | P3 | [#28](https://github.com/tj-999-comp/B_Stats_Site/issues/28) [Work records] 親ディレクトリREADMEリンクをproject内リンクへ修正する | 未完了 | 独立。優先度未設定 |
| 12 | P3 | [#29](https://github.com/tj-999-comp/B_Stats_Site/issues/29) [Work records] 001〜010のmetadataと生成元validator・CIを追加する | 未完了 | 独立。優先度未設定 |
| 13 | P3 | [#30](https://github.com/tj-999-comp/B_Stats_Site/issues/30) [Actions] 手動公開要求workflowとdispatch権限を設定する | 未完了 | 独立。優先度未設定 |
| 14 | P3 | [#31](https://github.com/tj-999-comp/B_Stats_Site/issues/31) [E2E] 新規作業記録1件を手動publish要求する | 未完了 | 独立。優先度未設定 |
| 15 | P3 | [#32](https://github.com/tj-999-comp/B_Stats_Site/issues/32) [Automation] main更新時の公開要求triggerを有効化する | 未完了 | 独立。優先度未設定 |
