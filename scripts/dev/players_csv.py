"""players.json ↔ CSV 変換ユーティリティ

Usage:
    # players.json → CSV（編集用）
    python -m scraper.scripts.players_csv export \
        --json scraper/data/players.json \
        --csv  scraper/data/players.csv

    # CSV → players.json（編集後に上書き）
    python -m scraper.scripts.players_csv import \
        --csv  scraper/data/players.csv \
        --json scraper/data/players.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

# CSV に含めるフィールドの順序
CSV_FIELDS = [
    'player_id',
    'old_player_id',
    'player_name_j',
    'player_name_e',
    'nationality',
    'player_slot_category',
    'last_seen_team_id',
    'last_seen_jersey_number',
    'created_at',
    'updated_at',
]

# JSON に戻すとき null として扱う空文字フィールド
NULLABLE_FIELDS = {'nationality', 'player_slot_category', 'old_player_id',
                   'player_name_e', 'last_seen_team_id', 'last_seen_jersey_number'}


def export_to_csv(json_path: Path, csv_path: Path) -> None:
    players = json.loads(json_path.read_text(encoding='utf-8'))
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # players.json に存在する全フィールドを拾う（CSV_FIELDS にないものも末尾に追加）
    extra = []
    for p in players:
        for k in p:
            if k not in CSV_FIELDS and k not in extra:
                extra.append(k)
    fields = CSV_FIELDS + extra

    with csv_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for player in players:
            row = {k: ('' if player.get(k) is None else player.get(k, '')) for k in fields}
            writer.writerow(row)

    print(f'exported: {csv_path}  ({len(players)} 件)')


def import_from_csv(csv_path: Path, json_path: Path) -> None:
    players = []
    with csv_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            player: dict = {}
            for k, v in row.items():
                v = v.strip()
                # 空文字 → null に戻す（nullable フィールドのみ）
                if v == '' and k in NULLABLE_FIELDS:
                    player[k] = None
                else:
                    player[k] = v if v != '' else None
            players.append(player)

    json_path.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'imported: {json_path}  ({len(players)} 件)')


def main() -> None:
    parser = argparse.ArgumentParser(description='players.json ↔ CSV 変換')
    sub = parser.add_subparsers(dest='command', required=True)

    # export
    p_export = sub.add_parser('export', help='players.json → CSV')
    p_export.add_argument('--json', type=Path, default=Path('scraper/data/players.json'))
    p_export.add_argument('--csv',  type=Path, default=Path('scraper/data/players.csv'))

    # import
    p_import = sub.add_parser('import', help='CSV → players.json')
    p_import.add_argument('--csv',  type=Path, default=Path('scraper/data/players.csv'))
    p_import.add_argument('--json', type=Path, default=Path('scraper/data/players.json'))

    args = parser.parse_args()

    if args.command == 'export':
        export_to_csv(args.json, args.csv)
    else:
        import_from_csv(args.csv, args.json)


if __name__ == '__main__':
    main()
