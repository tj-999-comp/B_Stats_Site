"""明示した旧PlayerIDと再スクレイプ済みゲームJSONを名前で照合し、候補CSVを生成する。

Usage:
    python -m scripts.dev.build_player_id_map \\
        --players scraper/data/players.json \\
        --candidate-ids OLD_ID_1 OLD_ID_2 \\
        --games scraper/data/season_*/games_*.json \\
        --output /tmp/player_alias_candidates.csv

出力CSV列:
    old_player_id            ... 明示した旧PlayerID
    player_id ... ゲームJSONで見つかった新PlayerID
    player_name_j       ... 照合に使った日本語名
    old_team_id         ... 旧IDの最終所属チーム
    new_team_id         ... 新IDの最終所属チーム（確認用）
    status              ... "ok" / "ambiguous"（同名が複数存在）/ "not_found"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from scripts.db.player_boxscore import is_player_total_boxscore


def _load_candidate_players(players_path: Path, candidate_ids: list[str]) -> list[dict]:
    """players.json から明示された旧IDだけを返す。"""
    players = json.loads(players_path.read_text(encoding='utf-8'))
    if not isinstance(players, list):
        raise RuntimeError(f'Expected list JSON: {players_path}')
    requested = {str(player_id).strip() for player_id in candidate_ids if str(player_id).strip()}
    if not requested:
        raise RuntimeError('--candidate-ids must contain at least one player_id')

    by_id = {
        str(player.get('player_id')).strip(): player
        for player in players
        if str(player.get('player_id') or '').strip()
    }
    missing = sorted(requested - set(by_id))
    if missing:
        raise RuntimeError(f'candidate player_id not found in players JSON: {missing}')
    return [by_id[player_id] for player_id in sorted(requested)]


def _collect_game_players(game_paths: list[Path]) -> dict[str, list[dict]]:
    """ゲームJSONから (player_name_j → [{player_id, last_team_id}]) のマップを構築する。
    同名の選手が複数存在する場合はリストに複数エントリが入る。
    """
    name_map: dict[str, list[dict]] = {}

    for path in game_paths:
        payload = json.loads(path.read_text(encoding='utf-8'))
        games = payload if isinstance(payload, list) else payload.get('games', [])

        for item in games:
            home_bs = item.get('home_boxscores', [])
            away_bs = item.get('away_boxscores', [])
            for bs in home_bs + away_bs:
                if not is_player_total_boxscore(bs):
                    continue
                pid = str(bs.get('PlayerID', '')).strip()
                name_j = str(bs.get('PlayerNameJ', '')).strip()
                team_id = str(bs.get('TeamID', '')).strip()
                if not pid or not name_j:
                    continue

                entries = name_map.setdefault(name_j, [])
                # 同じ player_id が既に登録済みなら skip（ゲームをまたいで重複する）
                if not any(e['player_id'] == pid for e in entries):
                    entries.append({'player_id': pid, 'team_id': team_id})

    return name_map


def build_candidates(
    candidate_players: list[dict],
    game_name_map: dict[str, list[dict]],
) -> list[dict]:
    """旧IDと新IDの照合候補リストを生成する"""
    rows = []
    for player in candidate_players:
        old_id = player['player_id']
        name_j = player.get('player_name_j', '').strip()
        old_team = player.get('last_seen_team_id', '')

        matches = game_name_map.get(name_j, [])
        # 自分自身の旧IDをゲームデータが保持している場合は除外
        matches = [m for m in matches if m['player_id'] != old_id]

        if not matches:
            rows.append({
                'old_player_id': old_id,
                'player_id': '',
                'player_name_j': name_j,
                'old_team_id': old_team,
                'new_team_id': '',
                'status': 'not_found',
            })
        elif len(matches) == 1:
            rows.append({
                'old_player_id': old_id,
                'player_id': matches[0]['player_id'],
                'player_name_j': name_j,
                'old_team_id': old_team,
                'new_team_id': matches[0]['team_id'],
                'status': 'ok',
            })
        else:
            # 同名の選手が複数いる場合は ambiguous としてすべての候補を出力
            for m in matches:
                rows.append({
                    'old_player_id': old_id,
                    'player_id': m['player_id'],
                    'player_name_j': name_j,
                    'old_team_id': old_team,
                    'new_team_id': m['team_id'],
                    'status': 'ambiguous',
                })

    return rows


def write_csv(rows: list[dict], output_path: Path) -> None:
    fieldnames = ['old_player_id', 'player_id', 'player_name_j',
                  'old_team_id', 'new_team_id', 'status']
    with output_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='明示した旧PlayerIDと再スクレイプ済みゲームJSONを照合しエイリアス候補CSVを生成する'
    )
    parser.add_argument('--players', required=True, help='players.json のパス')
    parser.add_argument(
        '--candidate-ids', required=True, nargs='+',
        help='照合対象とする旧player_id。プロフィール列からは推測しない',
    )
    parser.add_argument('--games',   required=True, nargs='+', help='ゲームJSONのパス（glob可・複数指定可）')
    parser.add_argument('--output', default='/tmp/player_alias_candidates.csv',
                        help='出力CSVパス (default: /tmp/player_alias_candidates.csv)')
    args = parser.parse_args()

    players_path = Path(args.players)
    output_path  = Path(args.output)

    # glob 展開（シェルが展開しない場合に備えて Python 側でも処理）
    game_paths: list[Path] = []
    for pattern in args.games:
        expanded = list(Path('.').glob(pattern)) if '*' in pattern else [Path(pattern)]
        game_paths.extend(expanded)

    if not game_paths:
        print('ERROR: ゲームJSONが見つかりません', file=sys.stderr)
        sys.exit(1)

    print(f'players.json: {players_path}')
    print(f'game files:   {len(game_paths)} ファイル')

    candidate_players = _load_candidate_players(players_path, args.candidate_ids)
    print(f'明示された旧ID候補: {len(candidate_players)} 人')

    game_name_map = _collect_game_players(game_paths)
    print(f'ゲームJSON から収集した選手名: {len(game_name_map)} 件')

    candidates = build_candidates(candidate_players, game_name_map)

    ok        = sum(1 for r in candidates if r['status'] == 'ok')
    ambiguous = sum(1 for r in candidates if r['status'] == 'ambiguous')
    not_found = sum(1 for r in candidates if r['status'] == 'not_found')
    print(f'照合結果: ok={ok}  ambiguous={ambiguous}  not_found={not_found}')

    write_csv(candidates, output_path)
    print(f'出力: {output_path}')
    if ambiguous:
        print(f'⚠ ambiguous が {ambiguous} 件あります。CSVを確認し player_id を手動で修正してください。')
    if not_found:
        print(f'⚠ not_found が {not_found} 件あります。引退・長期離脱等で新IDが取得できなかった選手です。')


if __name__ == '__main__':
    main()
