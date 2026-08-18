# 作業記録 010: 作業記録の呼称・配置・表示ルール再編
作成日: 2026-08-13

## 目的

GitHub Issueとリポジトリ内の調査・実行記録の呼称が混在していたため、役割、名称、保存場所、HTML表示のルールを分離する。

## 決定事項

- `Issue` はGitHub Issueだけを指す。
- リポジトリ内の調査、実行結果、判断経緯は `作業記録` と呼ぶ。
- 旧 `issues/` は `work-records/` へ変更する。
- 作業記録Markdownは `work-records/md/work_record_###.md` に置く。
- 閲覧用HTMLはサブディレクトリを作らず、`work-records/` 直下に置く。
- `work-records/` 直下のMarkdownは `README.md` と `design.md` だけとする。
- HTMLは `work-records/design.md` を原則として守る。
- GitHub Issue状況は独立した一覧ファイルにせず、関連する作業記録へ保存する。HTMLがある場合は、その作業記録HTMLの末尾へ追加する。

## GitHub側の整理

- GitHub Issue #24 → #25の親子登録を確認した。
- GitHub Issue #22・#23を#12の正式な子Issueとして登録した。
- #12配下が#21（完了）、#22・#23（open）の3件であることを確認した。

## 作成・更新物

- `work-records/README.md`: 呼称、配置、命名、Issue状況、HTMLの運用ルール
- `work-records/design.md`: 作業記録HTMLのデザイン原則
- `work-records/md/work_record_008.md`: 2026-08-13時点のGitHub Issue状況を実施記録の末尾へ統合
- `work-records/work_record_008.html`: 上記の閲覧用HTML
- `scripts/dev/validate_work_record_filenames.py`: 作業記録の配置・命名検証
- `.github/workflows/validate-work-record-filenames.yml`: CI検証

## 検証

- `work-records/` 直下のMarkdownが`README.md`と`design.md`だけであることを確認した。
- 作業記録の配置、ファイル名、見出し番号、HTMLとMarkdownの対応を検証スクリプトで確認した。
- `work_record_008.html`を1280、900、640、320px幅で確認し、横overflow、console error、page errorがないことを確認した。
- 320px実寸で見出し44px、本文16px、Issue行12件を確認した。

## GitHub Issue状況（2026-08-13時点の現在値）

確認日: 2026-08-13（JST）

GitHub APIで `tj-999-comp/B_Stats_Site` のIssueを確認した。Pull Requestは対象外とした。未完了Issueは12件だった。

### 親子関係

```text
#24（未完了・親Issue）
└── #25（未完了・子Issue）

#12（完了・親Issue）
├── #21（完了・子Issue）
├── #22（未完了・子Issue）
└── #23（未完了・子Issue）
```

`#22` と `#23` は `#25` から参照する関連Issueであり、`#24` の子Issueではない。

### 優先順位順の未完了一覧

優先順位はGitHub上のラベルではなく、Issue間の依存関係と作業への影響範囲をもとにした作業順の提案である。

| 順位 | 優先度 | GitHub Issue | 状態 | 関係・着手条件 |
|---:|---|---|---|---|
| 1 | P0 | [#24 2026年5月末までの未投入試合データをスクレイピング・投入する](https://github.com/tj-999-comp/B_Stats_Site/issues/24) | 未完了 | 親Issue。新規: 2026-08-13。#25をブロック |
| 2 | P1 | [#25 試合データ投入後のplayer_id重複整理とプロフィール欠損補完](https://github.com/tj-999-comp/B_Stats_Site/issues/25) | 未完了 | #24の子Issue。新規: 2026-08-13。#24完了後 |
| 3 | P1 | [#23 45848〜45865周辺の分割player_idを調査・統合する](https://github.com/tj-999-comp/B_Stats_Site/issues/23) | 未完了 | #12の子Issue。#25と関連 |
| 4 | P1 | [#22 スタッフ相当判定フラグを追加してプロフィール欠損一覧から除外する](https://github.com/tj-999-comp/B_Stats_Site/issues/22) | 未完了 | #12の子Issue。#25と関連 |
| 5 | P2 | [#16 live DB・再構築SQL・テーブル定義のスキーマ差異を解消する](https://github.com/tj-999-comp/B_Stats_Site/issues/16) | 未完了 | 独立 |
| 6 | P2 | [#18 空のplayer_id_mapと旧ID名寄せ経路を検証する](https://github.com/tj-999-comp/B_Stats_Site/issues/18) | 未完了 | #23と関連 |
| 7 | P2 | [#13 player_slot_categoryの値を正規化する](https://github.com/tj-999-comp/B_Stats_Site/issues/13) | 未完了 | #25完了後が適切 |
| 8 | P2 | [#14 attendance欠損14試合を調査・補完する](https://github.com/tj-999-comp/B_Stats_Site/issues/14) | 未完了 | 独立 |
| 9 | P3 | [#15 過年度のplus_minus・背番号欠損を調査する](https://github.com/tj-999-comp/B_Stats_Site/issues/15) | 未完了 | 独立 |
| 10 | P3 | [#17 play_by_play未投入と存在フラグの整合性を整理する](https://github.com/tj-999-comp/B_Stats_Site/issues/17) | 未完了 | 独立 |
| 11 | P3 | [#7 試合のスクレイピングデータ精査](https://github.com/tj-999-comp/B_Stats_Site/issues/7) | 未完了 | #24と範囲が重なる |
| 12 | P3 | [#9 課題解決の原案を立てる](https://github.com/tj-999-comp/B_Stats_Site/issues/9) | 未完了 | 探索テーマ |
