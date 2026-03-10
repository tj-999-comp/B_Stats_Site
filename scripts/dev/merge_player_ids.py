"""ID統合スクリプト: 確認済みCSVを元に旧PlayerIDを新PlayerIDへ統合する。

## 前提
- supabase/migrations/20260308_player_id_aliases.sql 適用済みであること
- supabase/migrations/20260308b_rename_player_id_map.sql 適用済みであること
  （player_id_map テーブル・ON UPDATE CASCADE FKが存在する状態）

## 実行手順
1. build_player_id_map.py で候補CSVを生成・確認（status=ok の行のみ残す）
2. このスクリプトでドライランして内容を確認する
3. --yes で本番実行

Usage:
    # ドライラン（ファイル・DBを変更しない）
    python -m scraper.scripts.merge_player_ids \\
        --csv scraper/data/player_id_map.csv

    # 本番実行
    python -m scraper.scripts.merge_player_ids \\
        --csv scraper/data/player_id_map.csv \\
        --players scraper/data/players.json \\
        --yes

## 処理フロー
  1. players.json の old_player_id を player_id（新ID）に書き換えて保存
  2. Supabase を更新

  [A] player_id が players に未存在:
      → UPDATE players SET player_id=新 WHERE player_id=旧
        (ON UPDATE CASCADE で player_game_stats / player_name_history / player_affiliations に連鎖)
      → INSERT INTO player_id_map

  [B] player_id が players に既存（再スクレイプ済み）:
      → player_game_stats の旧ID行を新IDへ UPDATE
      → player_name_history / player_affiliations の旧ID行を DELETE
      → DELETE FROM players WHERE player_id=旧
      → INSERT INTO player_id_map
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from scripts.db.db import get_client


def _fetch_existing_player_ids(client, ids: list[str]) -> set[str]:
    res = client.table('players').select('player_id').in_('player_id', ids).execute()
    return {row['player_id'] for row in (res.data or [])}


def _update_players_json(players_path: Path, id_pairs: list[tuple[str, str]], dry_run: bool) -> None:
    """players.json の old_player_id を player_id（新ID）に書き換え、old_player_id フィールドを追加して保存する。"""
    players = json.loads(players_path.read_text(encoding='utf-8'))
    id_map = {old_id: new_id for old_id, new_id in id_pairs}
    updated = 0
    for player in players:
        old_id = player.get('player_id', '')
        if old_id in id_map:
            player['old_player_id'] = old_id
            player['player_id'] = id_map[old_id]
            updated += 1
    print(f'players.json: {updated} 件のIDを更新（old_player_id フィールドを追加）')
    if not dry_run:
        players_path.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'written: {players_path}')


def _merge_pair(
    client,
    old_player_id: str,
    player_id: str,
    player_name_j: str,
    existing_ids: set[str],
    dry_run: bool,
) -> None:
    player_id_exists = player_id in existing_ids

    if not player_id_exists:
        # --- ケースA: 新IDがまだ存在しない ---
        print(f'  [A] UPDATE players {old_player_id!r} → {player_id!r}  ({player_name_j})')
        if not dry_run:
            client.table('players').update({'player_id': player_id}).eq('player_id', old_player_id).execute()
    else:
        # --- ケースB: 新IDが既に存在（再スクレイプ済み）---
        print(f'  [B] merge {old_player_id!r} → {player_id!r}  ({player_name_j})')

        print(f'      UPDATE player_game_stats player_id={old_player_id!r} → {player_id!r}')
        if not dry_run:
            client.table('player_game_stats').update({'player_id': player_id}).eq('player_id', old_player_id).execute()

        # player_name_history / player_affiliations の旧ID行を削除
        # （新IDのレコードはトリガーにより既に作成済み）
        print(f'      DELETE player_name_history WHERE player_id={old_player_id!r}')
        if not dry_run:
            client.table('player_name_history').delete().eq('player_id', old_player_id).execute()

        print(f'      DELETE player_affiliations WHERE player_id={old_player_id!r}')
        if not dry_run:
            client.table('player_affiliations').delete().eq('player_id', old_player_id).execute()

        print(f'      DELETE players WHERE player_id={old_player_id!r}')
        if not dry_run:
            client.table('players').delete().eq('player_id', old_player_id).execute()

    # player_id_map に記録
    print(f'      INSERT player_id_map ({old_player_id!r} → {player_id!r})')
    if not dry_run:
        client.table('player_id_map').upsert({
            'old_player_id': old_player_id,
            'player_id': player_id,
            'note': f'merged: {player_name_j}',
        }, on_conflict='old_player_id').execute()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='確認済みCSVを元に旧PlayerIDを新PlayerIDへ統合する'
    )
    parser.add_argument('--csv', default='scraper/data/player_alias_candidates.csv', help='player_id_map CSVのパス（status=ok 行のみ含むこと）')
    parser.add_argument(
        '--players',
        type=Path,
        default=Path('scraper/data/players.json'),
        help='players.json のパス (default: scraper/data/players.json)',
    )
    parser.add_argument('--yes', action='store_true', help='実際にファイル・DBを更新する（省略時はドライラン）')
    parser.add_argument('--skip-db', action='store_true', help='players.json のみ更新し Supabase 更新はスキップする')
    args = parser.parse_args()

    dry_run = not args.yes
    if dry_run:
        print('=== DRY RUN（--yes なしで実行中。ファイル・DBは変更されません） ===')

    csv_path = Path(args.csv)
    rows = []
    with csv_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get('status', 'ok').strip()
            # 旧列名（alias_id / canonical_player_id）との後方互換対応
            old_player_id = (row.get('old_player_id') or row.get('alias_id') or '').strip()
            player_id     = (row.get('player_id') or row.get('canonical_player_id') or '').strip()
            if not old_player_id or not player_id:
                print(f'SKIP: old_player_id or player_id が空 → {row}', file=sys.stderr)
                continue
            if old_player_id == player_id:
                print(f'SKIP: old_player_id と player_id が同一（自己参照）→ {old_player_id!r}')
                continue
            if status != 'ok':
                print(f'SKIP: status={status!r}  {old_player_id} → {player_id}')
                continue
            rows.append((old_player_id, player_id, row.get('player_name_j', '')))

    print(f'処理対象: {len(rows)} ペア')

    # --- 1. players.json を更新 ---
    _update_players_json(args.players, [(r[0], r[1]) for r in rows], dry_run)

    # --- 2. Supabase を更新（--skip-db で省略可）---
    if args.skip_db:
        print('--skip-db: Supabase 更新をスキップ')
        print('\n=== players.json 更新完了 ===')
        return

    client = get_client()
    all_ids = list({pid for pair in rows for pid in pair[:2]})
    existing_ids = _fetch_existing_player_ids(client, all_ids)

    for old_player_id, player_id, player_name_j in rows:
        if old_player_id not in existing_ids:
            print(f'SKIP: old_player_id={old_player_id!r} は players テーブルに存在しません（既に統合済み?）')
            continue
        try:
            _merge_pair(client, old_player_id, player_id, player_name_j, existing_ids, dry_run)
        except Exception as e:
            print(f'ERROR: {old_player_id!r} → {player_id!r}: {e}', file=sys.stderr)

    if dry_run:
        print('\n=== DRY RUN 完了。--yes を付けて再実行すると上記の変更が適用されます ===')
    else:
        print('\n=== 統合完了 ===')


if __name__ == '__main__':
    main()
