"""補完候補の取得JSONを既存の月次ゲームJSONへ安全にマージするCLI。"""

from __future__ import annotations

import argparse
import calendar
import copy
import json
import logging
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.scraping.scrape_candidate_dates import load_candidate_dates


DEFAULT_CANDIDATE_INPUT = Path('scraper/data/game_supplement_candidates.csv')
DEFAULT_SCRAPED_DIR = Path('scraper/data/issue45_candidate_scrapes')
DEFAULT_DATA_ROOT = Path('scraper/data')
DEFAULT_REPORT = Path('/tmp/issue45_candidate_merge_report.json')
DEFAULT_BACKUP_DIR = Path('/tmp/issue45_existing_json_backup')
JST = timezone(timedelta(hours=9))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TEAM_ALIASES = {
    'A東京': 'アルバルク東京',
    '千葉': '千葉ジェッツ',
    '北海道': 'レバンガ北海道',
    '秋田': '秋田ノーザンハピネッツ',
    '栃木': '栃木ブレックス',
    '川崎': '川崎ブレイブサンダース',
    '三遠': '三遠ネオフェニックス',
    '富山': '富山グラウジーズ',
    '大阪': '大阪エヴェッサ',
    '京都': '京都ハンナリーズ',
    '滋賀': '滋賀レイクス',
    '滋賀レイクスターズ': '滋賀レイクス',
    '横浜': '横浜ビー・コルセアーズ',
    '横浜BC': '横浜ビー・コルセアーズ',
    'SR渋谷': 'サンロッカーズ渋谷',
    '渋谷': 'サンロッカーズ渋谷',
    '三河': 'シーホース三河',
    '名古屋D': '名古屋ダイヤモンドドルフィンズ',
    '名古屋': '名古屋ダイヤモンドドルフィンズ',
    '琉球': '琉球ゴールデンキングス',
    '島根': '島根スサノオマジック',
    '群馬': '群馬クレインサンダーズ',
    '仙台': '仙台89ERS',
    '広島': '広島ドラゴンフライズ',
    '佐賀': '佐賀バルーナーズ',
    '長崎': '長崎ヴェルカ',
    '越谷': '越谷アルファーズ',
}


def _text(value: Any) -> str:
    return '' if value is None else str(value).strip()


def _canonical_team_name(value: Any) -> str:
    name = _text(value)
    return TEAM_ALIASES.get(name, name)


def _team_pair_from_candidate(row: dict[str, str]) -> tuple[str, str]:
    return tuple(sorted((_text(row.get('home_team_id')), _text(row.get('away_team_id')))))


def _team_pair_from_game(game: dict[str, Any]) -> tuple[str, str] | None:
    home = _text(game.get('HomeTeamID'))
    away = _text(game.get('AwayTeamID'))
    if home and away:
        return tuple(sorted((home, away)))
    return None


def _team_names_match(row: dict[str, str], game: dict[str, Any]) -> bool:
    expected = {
        _canonical_team_name(row.get('home_team_name_j')),
        _canonical_team_name(row.get('away_team_name_j')),
    }
    actual = {
        _canonical_team_name(game.get('HomeTeamNameJ')),
        _canonical_team_name(game.get('AwayTeamNameJ')),
    }
    return expected == actual


def _schedule_key(item: dict[str, Any]) -> int | None:
    value = item.get('schedule_key')
    if value is None and isinstance(item.get('game'), dict):
        value = item['game'].get('ScheduleKey')
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _timestamp_date_jst(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value), tz=JST).date().isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _source_date_matches(game: dict[str, Any], candidate_date: str) -> bool:
    return candidate_date in {
        _timestamp_date_jst(game.get('GameDateTime')),
        _timestamp_date_jst(game.get('GameStartTime')),
    }


def _datetime_correction(
    game: dict[str, Any],
    candidate_date: date,
) -> dict[str, Any] | None:
    """GameStartTimeと候補日が一致する年ずれGameDateTimeだけを補正する。"""
    original_value = game.get('GameDateTime')
    original_date = _timestamp_date_jst(original_value)
    expected_date = candidate_date.isoformat()
    if original_date == expected_date:
        return None
    if _timestamp_date_jst(game.get('GameStartTime')) != expected_date:
        return None
    try:
        original = datetime.fromtimestamp(int(original_value), tz=JST)
    except (TypeError, ValueError, OSError, OverflowError):
        return None
    corrected = datetime(
        candidate_date.year,
        candidate_date.month,
        candidate_date.day,
        original.hour,
        original.minute,
        original.second,
        tzinfo=JST,
    )
    return {
        'old_value': str(original_value),
        'old_date_jst': original_date,
        'new_value': str(int(corrected.timestamp())),
        'new_date_jst': expected_date,
        'reason': 'GameStartTimeのJST日付と候補日が一致するため、GameDateTimeの年月日だけを補正',
    }


def _season_folder(season: str) -> str:
    start_year = int(season.split('-', maxsplit=1)[0])
    return f'season_{start_year}-{start_year + 1}'


def _month_range(target_date: date) -> tuple[date, date]:
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return (
        date(target_date.year, target_date.month, 1),
        date(target_date.year, target_date.month, last_day),
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError(f'JSONのトップレベルがobjectではありません: {path}')
    return payload


def _planned_target_json(
    *,
    data_root: Path,
    season: str,
    target_date: date,
) -> tuple[Path, bool]:
    folder = data_root / _season_folder(season)
    if not folder.is_dir():
        raise FileNotFoundError(f'シーズンディレクトリがありません: {folder}')
    for path in sorted(folder.glob(f'games_{season}_*.json')):
        try:
            payload = _load_json(path)
            start = date.fromisoformat(str(payload['start_date']))
            end = date.fromisoformat(str(payload['end_date']))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if payload.get('season') == season and start <= target_date <= end:
            return path, True
    month_start, month_end = _month_range(target_date)
    return (
        folder / f'games_{season}_{month_start.isoformat()}_{month_end.isoformat()}.json',
        False,
    )


def _source_payloads(scraped_dir: Path) -> dict[Path, dict[str, Any]]:
    payloads: dict[Path, dict[str, Any]] = {}
    for path in sorted(scraped_dir.glob('games_*.json')):
        payloads[path] = _load_json(path)
    if not payloads:
        raise FileNotFoundError(f'取得JSONがありません: {scraped_dir}')
    return payloads


def _card_match_method(row: dict[str, str], item: dict[str, Any]) -> str | None:
    game = item.get('game')
    if not isinstance(game, dict) or not game:
        return None
    if _team_pair_from_game(game) == _team_pair_from_candidate(row):
        return 'team_id'
    if _team_names_match(row, game):
        return 'team_name_alias'
    return None


def _find_source_game(
    *,
    row: dict[str, str],
    candidate_date: str,
    source_payloads: dict[Path, dict[str, Any]],
    preferred_path: Path,
) -> tuple[Path | None, dict[str, Any] | None, str, list[int]]:
    ordered_paths = [
        path for path in [preferred_path, *source_payloads]
        if path in source_payloads
    ]
    seen_paths: set[Path] = set()
    matches: list[tuple[Path, dict[str, Any], str]] = []
    for path in ordered_paths:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        games = source_payloads[path].get('games', [])
        if not isinstance(games, list):
            continue
        for item in games:
            if not isinstance(item, dict):
                continue
            method = _card_match_method(row, item)
            game = item.get('game')
            if method and isinstance(game, dict) and _source_date_matches(game, candidate_date):
                matches.append((path, item, method))

    if len(matches) == 1:
        return matches[0][0], matches[0][1], matches[0][2], []
    keys = [
        key for key in (_schedule_key(item) for _, item, _ in matches)
        if key is not None
    ]
    return None, None, 'ambiguous' if matches else 'not_found', keys


def _detail_status(item: dict[str, Any]) -> str:
    if item.get('source_tab') == 'fallback_html':
        return 'fallback_html'
    if not item.get('summaries') or not item.get('home_boxscores') or not item.get('away_boxscores'):
        return 'minimal'
    return 'full'


def build_merge_plan(
    *,
    candidate_input: Path,
    scraped_dir: Path,
    data_root: Path,
    create_missing_monthly: bool,
) -> dict[str, Any]:
    groups = load_candidate_dates(candidate_input)
    payloads = _source_payloads(scraped_dir)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    selected_keys: set[int] = set()

    for group in groups:
        season = str(group['season'])
        target_date = date.fromisoformat(str(group['date']))
        preferred_path = scraped_dir / f'games_{season}_{target_date.isoformat()}.json'
        try:
            target_path, target_exists = _planned_target_json(
                data_root=data_root,
                season=season,
                target_date=target_date,
            )
        except FileNotFoundError as exc:
            errors.append(str(exc))
            continue

        for row in group['candidates']:
            source_path, item, match_method, ambiguous_keys = _find_source_game(
                row=row,
                candidate_date=target_date.isoformat(),
                source_payloads=payloads,
                preferred_path=preferred_path,
            )
            record: dict[str, Any] = {
                'season': season,
                'candidate_date': target_date.isoformat(),
                'home_team_id': row.get('home_team_id', ''),
                'away_team_id': row.get('away_team_id', ''),
                'home_team_name_j': row.get('home_team_name_j', ''),
                'away_team_name_j': row.get('away_team_name_j', ''),
                'target_json': str(target_path),
                'target_exists': target_exists,
                'match_method': match_method,
                'ambiguous_schedule_keys': ambiguous_keys,
            }
            if item is None or source_path is None:
                record['status'] = 'error'
                errors.append(
                    f"候補カードを取得JSONから特定できません: {season} {target_date} "
                    f"{row.get('home_team_name_j')} vs {row.get('away_team_name_j')} ({match_method})"
                )
                records.append(record)
                continue

            key = _schedule_key(item)
            game = item.get('game')
            if not isinstance(game, dict):
                record['status'] = 'error'
                errors.append(f'gameがobjectではありません: {source_path}')
                records.append(record)
                continue
            correction = _datetime_correction(game, target_date)
            actual_date = _timestamp_date_jst(game.get('GameDateTime'))
            valid_date = actual_date == target_date.isoformat() or correction is not None
            record.update({
                'status': 'matched',
                'source_json': str(source_path),
                'schedule_key': key,
                'actual_date_jst': actual_date,
                'source_tab': item.get('source_tab'),
                'detail_status': _detail_status(item),
                'summaries_count': len(item.get('summaries', [])),
                'home_boxscores_count': len(item.get('home_boxscores', [])),
                'away_boxscores_count': len(item.get('away_boxscores', [])),
                'game_datetime_correction': correction,
            })
            if key is None:
                record['status'] = 'error'
                errors.append(f'schedule_keyがありません: {source_path}')
            elif key in selected_keys:
                record['status'] = 'error'
                errors.append(f'schedule_keyが候補間で重複しています: {key}')
            else:
                selected_keys.add(key)
            if not valid_date:
                record['status'] = 'error'
                errors.append(
                    f'JST日付が候補と不一致: schedule_key={key} '
                    f'候補={target_date} 実データ={actual_date}'
                )
            if not target_exists and not create_missing_monthly:
                record['status'] = 'error'
                errors.append(f'既存月次JSONがありません: {season} {target_date}')
            records.append(record)

    matched = [record for record in records if record.get('status') == 'matched']
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'candidate_input': str(candidate_input),
        'scraped_dir': str(scraped_dir),
        'candidate_count': sum(len(group['candidates']) for group in groups),
        'matched_count': len(matched),
        'full_detail_count': sum(record['detail_status'] == 'full' for record in matched),
        'fallback_or_minimal_count': sum(record['detail_status'] != 'full' for record in matched),
        'new_monthly_target_count': len({
            record['target_json'] for record in matched if not record['target_exists']
        }),
        'datetime_correction_count': sum(
            record['game_datetime_correction'] is not None for record in matched
        ),
        'error_count': len(errors),
        'errors': errors,
        'records': records,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _new_monthly_payload(season: str, target_date: date) -> dict[str, Any]:
    start_date, end_date = _month_range(target_date)
    return {
        'season': season,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'date_to_schedule_keys': {},
        'game_count': 0,
        'games': [],
    }


def _is_incomplete(item: dict[str, Any]) -> bool:
    return (
        bool(item.get('error'))
        or not isinstance(item.get('game'), dict)
        or not item.get('game')
    )


def _source_item(record: dict[str, Any], cache: dict[Path, dict[str, Any]]) -> dict[str, Any]:
    source_path = Path(str(record['source_json']))
    payload = cache.setdefault(source_path, _load_json(source_path))
    key = int(record['schedule_key'])
    for item in payload.get('games', []):
        if isinstance(item, dict) and _schedule_key(item) == key:
            selected = copy.deepcopy(item)
            correction = record.get('game_datetime_correction')
            if correction:
                selected['game']['GameDateTime'] = correction['new_value']
            return selected
    raise KeyError(f'schedule_key={key}が取得JSONにありません: {source_path}')


def apply_merge_plan(
    *,
    plan: dict[str, Any],
    backup_dir: Path,
    allow_fallback: bool,
    create_missing_monthly: bool,
) -> dict[str, Any]:
    if plan['error_count']:
        raise RuntimeError('マージ計画にエラーがあるため適用できません')
    if plan['fallback_or_minimal_count'] and not allow_fallback:
        raise RuntimeError('--allow-fallbackを指定してください')
    if plan['new_monthly_target_count'] and not create_missing_monthly:
        raise RuntimeError('--create-missing-monthlyを指定してください')

    records = [record for record in plan['records'] if record['status'] == 'matched']
    by_target: dict[Path, list[dict[str, Any]]] = {}
    for record in records:
        by_target.setdefault(Path(str(record['target_json'])), []).append(record)

    if backup_dir.exists() and any(backup_dir.iterdir()):
        raise FileExistsError(f'バックアップ先が空ではありません: {backup_dir}')
    backup_dir.mkdir(parents=True, exist_ok=True)
    source_cache: dict[Path, dict[str, Any]] = {}
    result: dict[str, Any] = {
        'targets': [],
        'added_count': 0,
        'replaced_incomplete_count': 0,
        'already_present_count': 0,
        'created_monthly_count': 0,
    }

    for target_path, target_records in sorted(by_target.items(), key=lambda item: str(item[0])):
        target_exists = target_path.exists()
        if target_exists:
            target_payload = _load_json(target_path)
            backup_path = backup_dir / target_path.parent.name / target_path.name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, backup_path)
        else:
            first = target_records[0]
            target_payload = _new_monthly_payload(
                str(first['season']),
                date.fromisoformat(str(first['candidate_date'])),
            )
            result['created_monthly_count'] += 1

        games = target_payload.setdefault('games', [])
        if not isinstance(games, list):
            raise ValueError(f'gamesが配列ではありません: {target_path}')
        existing_indices = {
            key: index
            for index, item in enumerate(games)
            if isinstance(item, dict)
            for key in [_schedule_key(item)]
            if key is not None
        }
        added = 0
        replaced_incomplete = 0
        already_present = 0

        for record in target_records:
            key = int(record['schedule_key'])
            incoming = _source_item(record, source_cache)
            if key not in existing_indices:
                games.append(incoming)
                existing_indices[key] = len(games) - 1
                added += 1
            elif _is_incomplete(games[existing_indices[key]]):
                games[existing_indices[key]] = incoming
                replaced_incomplete += 1
            else:
                already_present += 1

            date_map = target_payload.setdefault('date_to_schedule_keys', {})
            if not isinstance(date_map, dict):
                raise ValueError(f'date_to_schedule_keysがobjectではありません: {target_path}')
            keys = date_map.setdefault(str(record['candidate_date']), [])
            if not isinstance(keys, list):
                raise ValueError(f'日付別schedule_keyが配列ではありません: {target_path}')
            if key not in keys:
                keys.append(key)

        target_payload['game_count'] = len(games)
        target_payload['generated_at'] = datetime.now(timezone.utc).isoformat()
        temporary_path = target_path.with_suffix('.json.issue45_tmp')
        _write_json(temporary_path, target_payload)
        temporary_path.replace(target_path)
        target_result = {
            'target_json': str(target_path),
            'created_monthly': not target_exists,
            'added_count': added,
            'replaced_incomplete_count': replaced_incomplete,
            'already_present_count': already_present,
        }
        result['targets'].append(target_result)
        result['added_count'] += added
        result['replaced_incomplete_count'] += replaced_incomplete
        result['already_present_count'] += already_present
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='補完候補ゲームを既存JSONへマージする')
    parser.add_argument('--candidate-input', type=Path, default=DEFAULT_CANDIDATE_INPUT)
    parser.add_argument('--scraped-dir', type=Path, default=DEFAULT_SCRAPED_DIR)
    parser.add_argument('--data-root', type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    parser.add_argument('--apply', action='store_true', help='検証済み計画を既存JSONへ適用する')
    parser.add_argument('--allow-fallback', action='store_true', help='公式Box Scoreなしのfallback_htmlを許可する')
    parser.add_argument('--create-missing-monthly', action='store_true', help='存在しない月次JSONを標準名で新規作成する')
    parser.add_argument('--backup-dir', type=Path, default=DEFAULT_BACKUP_DIR)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    plan = build_merge_plan(
        candidate_input=args.candidate_input,
        scraped_dir=args.scraped_dir,
        data_root=args.data_root,
        create_missing_monthly=args.create_missing_monthly,
    )
    _write_json(args.report, plan)
    logger.info(
        '候補=%d matched=%d full_detail=%d fallback_or_minimal=%d new_monthly=%d datetime_corrections=%d errors=%d report=%s',
        plan['candidate_count'],
        plan['matched_count'],
        plan['full_detail_count'],
        plan['fallback_or_minimal_count'],
        plan['new_monthly_target_count'],
        plan['datetime_correction_count'],
        plan['error_count'],
        args.report,
    )
    if plan['error_count']:
        raise SystemExit(1)
    if not args.apply:
        return
    result = apply_merge_plan(
        plan=plan,
        backup_dir=args.backup_dir,
        allow_fallback=args.allow_fallback,
        create_missing_monthly=args.create_missing_monthly,
    )
    plan['apply_result'] = result
    _write_json(args.report, plan)
    logger.info(
        'マージ完了: added=%d replaced_incomplete=%d already_present=%d created_monthly=%d',
        result['added_count'],
        result['replaced_incomplete_count'],
        result['already_present_count'],
        result['created_monthly_count'],
    )


if __name__ == '__main__':
    main()
