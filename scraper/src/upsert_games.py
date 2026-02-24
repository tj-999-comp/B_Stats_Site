"""開幕週ゲームJSONを teams / games / play_by_play へUPSERTする"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .db import upsert_game_team_stats, upsert_games, upsert_play_by_play, upsert_players, upsert_player_game_stats, upsert_teams


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip() == '':
        return None
    return int(value)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip() == '':
        return None
    return float(value)


def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _select_full_game_summary(item: dict[str, Any]) -> dict[str, Any] | None:
    summaries = item.get('summaries', [])
    if not summaries:
        return None

    period_18 = [summary for summary in summaries if _to_int(summary.get('PeriodCategory')) == 18]
    if period_18:
        return period_18[0]

    return max(summaries, key=lambda summary: _to_int(summary.get('PeriodCategory')) or 0)


def _summary_side(summary: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {
        'team_id': str(summary.get(f'{prefix}TeamID')) if summary.get(f'{prefix}TeamID') is not None else None,
        'team_name_j': summary.get(f'{prefix}TeamNameJ'),
        'points': _to_int(summary.get(f'{prefix}TeamPTR')) or 0,
        'fgm': _to_int(summary.get(f'{prefix}TeamPTM')) or 0,
        'fga': _to_int(summary.get(f'{prefix}TeamPTA')) or 0,
        'fg2m': _to_int(summary.get(f'{prefix}TeamPT2M')) or 0,
        'fg2a': _to_int(summary.get(f'{prefix}TeamPT2A')) or 0,
        'fg3m': _to_int(summary.get(f'{prefix}TeamPT3M')) or 0,
        'fg3a': _to_int(summary.get(f'{prefix}TeamPT3A')) or 0,
        'ftm': _to_int(summary.get(f'{prefix}TeamFTM')) or 0,
        'fta': _to_int(summary.get(f'{prefix}TeamFTA')) or 0,
        'off_rebounds': _to_int(summary.get(f'{prefix}TeamRB_OFF')) or 0,
        'def_rebounds': _to_int(summary.get(f'{prefix}TeamRB_DEF')) or 0,
        'total_rebounds': _to_int(summary.get(f'{prefix}TeamRB_TOT')) or 0,
        'assists': _to_int(summary.get(f'{prefix}TeamAS')) or 0,
        'steals': _to_int(summary.get(f'{prefix}TeamST')) or 0,
        'blocks': _to_int(summary.get(f'{prefix}TeamBS')) or 0,
        'blocks_received': _to_int(summary.get(f'{prefix}TeamBSON')) or 0,
        'turnovers': _to_int(summary.get(f'{prefix}TeamTO')) or 0,
        'fouls': _to_int(summary.get(f'{prefix}TeamFOUL')) or 0,
        'fouls_drawn': _to_int(summary.get(f'{prefix}TeamFOULON')) or 0,
        'fast_break_points': _to_int(summary.get(f'{prefix}TeamPTFB')) or 0,
        'second_chance_points': _to_int(summary.get(f'{prefix}TeamPT2ND')) or 0,
        'points_in_paint': _to_int(summary.get(f'{prefix}TeamPT2IN')) or 0,
        'points_from_turnover': _to_int(summary.get(f'{prefix}TeamPTPFT')) or 0,
    }


def _estimate_possession(team: dict[str, Any], opp: dict[str, Any]) -> float:
    team_or = team['off_rebounds']
    opp_dr = opp['def_rebounds']
    opp_or = opp['off_rebounds']
    team_dr = team['def_rebounds']

    team_or_rate = team_or / (team_or + opp_dr) if (team_or + opp_dr) > 0 else 0.0
    opp_or_rate = opp_or / (opp_or + team_dr) if (opp_or + team_dr) > 0 else 0.0

    team_poss = team['fga'] + 0.4 * team['fta'] - 1.07 * team_or_rate * (team['fga'] - team['fgm']) + team['turnovers']
    opp_poss = opp['fga'] + 0.4 * opp['fta'] - 1.07 * opp_or_rate * (opp['fga'] - opp['fgm']) + opp['turnovers']

    return 0.5 * (team_poss + opp_poss)


def _build_game_team_stat_row(
    *,
    schedule_key: int,
    game: dict[str, Any],
    team: dict[str, Any],
    opp: dict[str, Any],
    is_home: bool,
) -> dict[str, Any]:
    points = float(team['points'])
    fgm = float(team['fgm'])
    fga = float(team['fga'])
    fg2m = float(team['fg2m'])
    fg2a = float(team['fg2a'])
    fg3m = float(team['fg3m'])
    fg3a = float(team['fg3a'])
    ftm = float(team['ftm'])
    fta = float(team['fta'])
    turnovers = float(team['turnovers'])
    assists = float(team['assists'])

    opp_points = float(opp['points'])
    opp_fgm = float(opp['fgm'])
    opp_fga = float(opp['fga'])
    opp_fg2m = float(opp['fg2m'])
    opp_fg2a = float(opp['fg2a'])
    opp_fg3m = float(opp['fg3m'])
    opp_fg3a = float(opp['fg3a'])
    opp_ftm = float(opp['ftm'])
    opp_fta = float(opp['fta'])
    opp_turnovers = float(opp['turnovers'])
    opp_assists = float(opp['assists'])

    possession = _estimate_possession(team, opp)
    opp_possession = _estimate_possession(opp, team)

    periods = _to_int(game.get('GameCurrentPeriod')) or 4
    game_minutes = 40 + max(0, periods - 4) * 5
    team_minutes = game_minutes * 5
    pace = _safe_div(40 * (possession + opp_possession), 2 * (team_minutes / 5))

    efg_pct = _safe_div(fgm + 0.5 * fg3m, fga)
    ts_pct = _safe_div(points, 2 * (fga + 0.44 * fta))
    off_rtg = _safe_div(100 * points, possession)
    def_rtg = _safe_div(100 * opp_points, possession)

    opp_efg_pct = _safe_div(opp_fgm + 0.5 * opp_fg3m, opp_fga)
    opp_ts_pct = _safe_div(opp_points, 2 * (opp_fga + 0.44 * opp_fta))

    score_diff = points - opp_points

    return {
        'schedule_key': schedule_key,
        'team_id': team['team_id'],
        'opponent_team_id': opp['team_id'],
        'is_home': is_home,
        'points': team['points'],
        'fgm': team['fgm'],
        'fga': team['fga'],
        'fg_pct': _safe_div(fgm, fga),
        'fg2m': team['fg2m'],
        'fg2a': team['fg2a'],
        'fg2_pct': _safe_div(fg2m, fg2a),
        'fg3m': team['fg3m'],
        'fg3a': team['fg3a'],
        'fg3_pct': _safe_div(fg3m, fg3a),
        'ftm': team['ftm'],
        'fta': team['fta'],
        'ft_pct': _safe_div(ftm, fta),
        'off_rebounds': team['off_rebounds'],
        'def_rebounds': team['def_rebounds'],
        'total_rebounds': team['total_rebounds'],
        'assists': team['assists'],
        'steals': team['steals'],
        'blocks': team['blocks'],
        'blocks_received': team['blocks_received'],
        'turnovers': team['turnovers'],
        'fouls': team['fouls'],
        'fouls_drawn': team['fouls_drawn'],
        'fast_break_points': team['fast_break_points'],
        'second_chance_points': team['second_chance_points'],
        'points_in_paint': team['points_in_paint'],
        'possession': possession,
        'pace': pace,
        'off_rtg': off_rtg,
        'def_rtg': def_rtg,
        'net_rtg': (off_rtg - def_rtg) if (off_rtg is not None and def_rtg is not None) else None,
        'ast_rtg': _safe_div(100 * assists, possession),
        'tov_rtg': _safe_div(100 * turnovers, possession),
        'pft_rtg': _safe_div(float(team['points_from_turnover']), max(1.0, opp_turnovers)),
        'scp_rtg': _safe_div(float(team['second_chance_points']), max(1.0, float(team['off_rebounds']))),
        'efg_pct': efg_pct,
        'ts_pct': ts_pct,
        'ast_pct': _safe_div(100 * assists, fgm),
        'tov_pct': _safe_div(100 * turnovers, fga + 0.44 * fta + turnovers),
        'ast_tov_ratio': _safe_div(assists, turnovers),
        'play_pct': _safe_div(fgm, possession),
        'ft_freq': _safe_div(float(team['fouls_drawn']), max(1.0, fga + 0.44 * fta)),
        'ft_rate': _safe_div(fta, fga),
        'orb_pct': _safe_div(100 * float(team['off_rebounds']), float(team['off_rebounds'] + opp['def_rebounds'])),
        'drb_pct': _safe_div(100 * float(team['def_rebounds']), float(team['def_rebounds'] + opp['off_rebounds'])),
        'pft_pct': _safe_div(float(team['points_from_turnover']), points),
        'fbp_pct': _safe_div(float(team['fast_break_points']), points),
        'scp_pct': _safe_div(float(team['second_chance_points']), points),
        'pitp_pct': _safe_div(float(team['points_in_paint']), points),
        'pt2_attempt_pct': _safe_div(fg2a, fga + 0.44 * fta),
        'pt3_attempt_pct': _safe_div(fg3a, fga + 0.44 * fta),
        'pt2_points_share': _safe_div(2 * fg2m, points),
        'pt3_points_share': _safe_div(3 * fg3m, points),
        'ft_points_share': _safe_div(ftm, points),
        'shot_chances': fga + 0.44 * fta + turnovers,
        'eff': points + float(team['total_rebounds']) + assists + float(team['steals']) + float(team['blocks']) - (fga - fgm) - (fta - ftm) - turnovers,
        'close_win_3pts_or_less': 1 if (score_diff > 0 and score_diff <= 3) else 0,
        'close_loss_3pts_or_less': 1 if (score_diff < 0 and abs(score_diff) <= 3) else 0,
        'opp_possession': opp_possession,
        'opp_efg_pct': opp_efg_pct,
        'opp_ts_pct': opp_ts_pct,
        'opp_fg2_pct': _safe_div(opp_fg2m, opp_fg2a),
        'opp_fg3_pct': _safe_div(opp_fg3m, opp_fg3a),
        'opp_pt2_attempt_pct': _safe_div(opp_fg2a, opp_fga + 0.44 * opp_fta),
        'opp_pt3_attempt_pct': _safe_div(opp_fg3a, opp_fga + 0.44 * opp_fta),
        'opp_pt2_points_share': _safe_div(2 * opp_fg2m, opp_points),
        'opp_pt3_points_share': _safe_div(3 * opp_fg3m, opp_points),
        'opp_ft_points_share': _safe_div(opp_ftm, opp_points),
        'opp_ast_pct': _safe_div(100 * opp_assists, opp_fgm),
        'opp_ast_tov_ratio': _safe_div(opp_assists, opp_turnovers),
        'opp_ast_rtg': _safe_div(100 * opp_assists, opp_possession),
        'opp_tov_pct': _safe_div(100 * opp_turnovers, opp_fga + 0.44 * opp_fta + opp_turnovers),
        'opp_orb_pct': _safe_div(100 * float(opp['off_rebounds']), float(opp['off_rebounds'] + team['def_rebounds'])),
        'opp_drb_pct': _safe_div(100 * float(opp['def_rebounds']), float(opp['def_rebounds'] + team['off_rebounds'])),
        'opp_shot_chances': opp_fga + 0.44 * opp_fta + opp_turnovers,
        'opp_fbp_pct': _safe_div(float(opp['fast_break_points']), opp_points),
        'opp_scp_pct': _safe_div(float(opp['second_chance_points']), opp_points),
        'opp_scp_rtg': _safe_div(float(opp['second_chance_points']), max(1.0, float(opp['off_rebounds']))),
        'opp_pitp_pct': _safe_div(float(opp['points_in_paint']), opp_points),
        'opp_pft_pct': _safe_div(float(opp['points_from_turnover']), opp_points),
        'opp_pft_rtg': _safe_div(float(opp['points_from_turnover']), max(1.0, turnovers)),
    }


def _extract_game_team_stats(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in payload.get('games', []):
        summary = _select_full_game_summary(item)
        if not summary:
            continue

        game = item.get('game', {})
        schedule_key = _to_int(game.get('ScheduleKey') or item.get('schedule_key'))
        if schedule_key is None:
            continue

        home = _summary_side(summary, 'Home')
        away = _summary_side(summary, 'Away')
        if home['team_id'] is None or away['team_id'] is None:
            continue

        rows.append(
            _build_game_team_stat_row(
                schedule_key=schedule_key,
                game=game,
                team=home,
                opp=away,
                is_home=True,
            )
        )
        rows.append(
            _build_game_team_stat_row(
                schedule_key=schedule_key,
                game=game,
                team=away,
                opp=home,
                is_home=False,
            )
        )

    return rows


def _latest_opening_week_json(base_dir: Path) -> Path:
    candidates = sorted(base_dir.glob('games_*_opening_week.json'))
    if not candidates:
        raise FileNotFoundError(f'No opening-week JSON found in: {base_dir}')
    return candidates[-1]


def _extract_teams(payload: dict[str, Any]) -> list[dict[str, Any]]:
    team_map: dict[str, dict[str, Any]] = {}

    for item in payload.get('games', []):
        game = item.get('game', {})
        home_id = game.get('HomeTeamID')
        away_id = game.get('AwayTeamID')

        if home_id:
            team_map[str(home_id)] = {
                'team_id': str(home_id),
                'team_name_j': game.get('HomeTeamNameJ') or '',
                'team_name_e': game.get('HomeTeamNameE'),
                'team_short_name_j': game.get('HomeTeamShortNameJ'),
                'team_short_name_e': game.get('HomeTeamShortNameE'),
            }

        if away_id:
            team_map[str(away_id)] = {
                'team_id': str(away_id),
                'team_name_j': game.get('AwayTeamNameJ') or '',
                'team_name_e': game.get('AwayTeamNameE'),
                'team_short_name_j': game.get('AwayTeamShortNameJ'),
                'team_short_name_e': game.get('AwayTeamShortNameE'),
            }

    return list(team_map.values())


def _extract_games(payload: dict[str, Any]) -> list[dict[str, Any]]:
    season = payload['season']
    rows: list[dict[str, Any]] = []

    for item in payload.get('games', []):
        game = item.get('game', {})
        schedule_key = game.get('ScheduleKey') or item.get('schedule_key')
        if schedule_key is None:
            continue

        rows.append(
            {
                'schedule_key': _to_int(schedule_key),
                'season': season,
                'code': _to_int(game.get('Code')),
                'convention_key': game.get('ConventionKey'),
                'convention_name_j': game.get('ConventionNameJ'),
                'convention_name_e': game.get('ConventionNameE'),
                'year': _to_int(game.get('Year')),
                'setu': game.get('Setu'),
                'max_period': _to_int(game.get('MaxPeriod')),
                'game_current_period': _to_int(game.get('GameCurrentPeriod')),
                'game_datetime_unix': _to_int(game.get('GameDateTime')),
                'stadium_cd': game.get('StadiumCD'),
                'stadium_name_j': game.get('StadiumNameJ'),
                'stadium_name_e': game.get('StadiumNameE'),
                'attendance': _to_int(game.get('Attendance')),
                'game_ended_flg': bool(game.get('GameEndedFlg')),
                'record_fixed_flg': bool(game.get('RecordFixedFlg')),
                'boxscore_exists_flg': bool(game.get('BoxscoreExistsFlg')),
                'play_by_play_exists_flg': bool(game.get('PlayByPlayExistsFlg')),
                'home_team_id': str(game.get('HomeTeamID')) if game.get('HomeTeamID') is not None else None,
                'away_team_id': str(game.get('AwayTeamID')) if game.get('AwayTeamID') is not None else None,
                'home_team_score_q1': _to_int(game.get('HomeTeamScore01')),
                'home_team_score_q2': _to_int(game.get('HomeTeamScore02')),
                'home_team_score_q3': _to_int(game.get('HomeTeamScore03')),
                'home_team_score_q4': _to_int(game.get('HomeTeamScore04')),
                'home_team_score_q5': _to_int(game.get('HomeTeamScore05')),
                'home_team_score_total': _to_int(game.get('HomeTeamScore')),
                'away_team_score_q1': _to_int(game.get('AwayTeamScore01')),
                'away_team_score_q2': _to_int(game.get('AwayTeamScore02')),
                'away_team_score_q3': _to_int(game.get('AwayTeamScore03')),
                'away_team_score_q4': _to_int(game.get('AwayTeamScore04')),
                'away_team_score_q5': _to_int(game.get('AwayTeamScore05')),
                'away_team_score_total': _to_int(game.get('AwayTeamScore')),
                'referee_id': _to_int(game.get('RefereeID')),
                'referee_name_j': game.get('RefereeNameJ'),
                'sub_referee_id_1': _to_int(game.get('SubRefereeID1')),
                'sub_referee_name_j_1': game.get('SubRefereeNameJ1'),
                'sub_referee_id_2': _to_int(game.get('SubRefereeID2')),
                'sub_referee_name_j_2': game.get('SubRefereeNameJ2'),
                'source_tab': _to_int(item.get('source_tab')),
            }
        )

    return rows


def _extract_play_by_play(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in payload.get('games', []):
        schedule_key = _to_int(item.get('schedule_key'))
        if schedule_key is None:
            game = item.get('game', {})
            schedule_key = _to_int(game.get('ScheduleKey'))
        if schedule_key is None:
            continue

        for play in item.get('play_by_plays', []):
            sequence_no = _to_int(play.get('No'))
            if sequence_no is None:
                continue

            rows.append(
                {
                    'schedule_key': schedule_key,
                    'sequence_no': sequence_no,
                    'code': _to_int(play.get('Code')),
                    'period': _to_int(play.get('Period')),
                    'rest_time': play.get('RestTime') or '',
                    'score': play.get('Score') or '',
                    'action_cd1': _to_int(play.get('ActionCD1')),
                    'action_cd2': _to_int(play.get('ActionCD2')),
                    'action_cd3': _to_int(play.get('ActionCD3')),
                    'area_cd': _to_int(play.get('AreaCD')),
                    'team_id': str(play.get('TeamID')) if play.get('TeamID') is not None else None,
                    'team_name_j': play.get('TeamNameJ'),
                    'player_id': str(play.get('PlayerID1')) if play.get('PlayerID1') is not None else None,
                    'player_no': play.get('PlayerNo1'),
                    'player_name_j': play.get('PlayerNameJ1') or '',
                    'home_away': _to_int(play.get('HomeAway')),
                    'side': play.get('Side'),
                    'success': _to_int(play.get('Success')),
                    'x': _to_float(play.get('X')),
                    'y': _to_float(play.get('Y')),
                    'play_text': play.get('PlayText') or '',
                    'period_end_row_flg': bool(play.get('PeriodEndRowFlg')),
                    'game_end_row_flg': bool(play.get('GameEndRowFlg')),
                    'record_datetime_raw': play.get('RecordDateTime') or '',
                    'record_edit_datetime_raw': play.get('RecordEditDateTime'),
                }
            )

    return rows


def _extract_players(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract unique players with their most recent team and jersey number"""
    player_map: dict[str, dict[str, Any]] = {}

    for item in payload.get('games', []):
        home_boxscores = item.get('home_boxscores', [])
        away_boxscores = item.get('away_boxscores', [])

        for boxscore in home_boxscores + away_boxscores:
            # Filter for full game totals only (PeriodCategory=18)
            if boxscore.get('PeriodCategory') != 18:
                continue

            player_id = str(boxscore.get('PlayerID'))
            if not player_id:
                continue

            team_id = str(boxscore.get('TeamID'))
            jersey_number = str(boxscore.get('PlayerNo', ''))
            player_name_j = boxscore.get('PlayerNameJ', '')
            player_name_e = boxscore.get('PlayerNameE', '')

            player_map[player_id] = {
                'player_id': player_id,
                'player_name_j': player_name_j,
                'player_name_e': player_name_e,
                'last_seen_team_id': team_id,
                'last_seen_jersey_number': jersey_number,
            }

    return list(player_map.values())


def _extract_player_game_stats(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract player game statistics from BoxScores (PeriodCategory=18 only)"""
    rows: list[dict[str, Any]] = []

    for item in payload.get('games', []):
        schedule_key = _to_int(item.get('schedule_key'))
        if schedule_key is None:
            game = item.get('game', {})
            schedule_key = _to_int(game.get('ScheduleKey'))
        if schedule_key is None:
            continue

        home_boxscores = item.get('home_boxscores', [])
        away_boxscores = item.get('away_boxscores', [])

        for boxscore in home_boxscores + away_boxscores:
            # Filter for full game totals only (PeriodCategory=18)
            if boxscore.get('PeriodCategory') != 18:
                continue

            player_id = str(boxscore.get('PlayerID'))
            if not player_id:
                continue

            team_id = str(boxscore.get('TeamID'))
            jersey_number = str(boxscore.get('PlayerNo', ''))

            # Calculate percentages
            fg2m = _to_int(boxscore.get('PT2M')) or 0
            fg2a = _to_int(boxscore.get('PT2A')) or 0
            fg3m = _to_int(boxscore.get('PT3M')) or 0
            fg3a = _to_int(boxscore.get('PT3A')) or 0
            ftm = _to_int(boxscore.get('FTM')) or 0
            fta = _to_int(boxscore.get('FTA')) or 0

            fgm = fg2m + fg3m
            fga = fg2a + fg3a
            fg_pct = round(fgm / fga, 4) if fga > 0 else None
            fg2_pct = round(fg2m / fg2a, 4) if fg2a > 0 else None
            fg3_pct = round(fg3m / fg3a, 4) if fg3a > 0 else None
            ft_pct = round(ftm / fta, 4) if fta > 0 else None

            rows.append(
                {
                    'schedule_key': schedule_key,
                    'player_id': player_id,
                    'team_id': team_id,
                    'jersey_number': jersey_number,
                    'is_starter': bool(boxscore.get('StartingFlg')),
                    'is_playing': bool(boxscore.get('PlayingFlg')),
                    'play_time': boxscore.get('PlayTime'),
                    'points': _to_int(boxscore.get('Point')),
                    'fgm': fgm,
                    'fga': fga,
                    'fg_pct': fg_pct,
                    'fg2m': fg2m,
                    'fg2a': fg2a,
                    'fg2_pct': fg2_pct,
                    'fg3m': fg3m,
                    'fg3a': fg3a,
                    'fg3_pct': fg3_pct,
                    'ftm': ftm,
                    'fta': fta,
                    'ft_pct': ft_pct,
                    'off_rebounds': _to_int(boxscore.get('RB_OFF')),
                    'def_rebounds': _to_int(boxscore.get('RB_DEF')),
                    'total_rebounds': _to_int(boxscore.get('RB_TOT')),
                    'assists': _to_int(boxscore.get('AS')),
                    'turnovers': _to_int(boxscore.get('TO')),
                    'steals': _to_int(boxscore.get('ST')),
                    'blocks': _to_int(boxscore.get('BS')),
                    'blocks_received': _to_int(boxscore.get('BSON')),
                    'fouls': _to_int(boxscore.get('FOUL')),
                    'fouls_drawn': _to_int(boxscore.get('FOULON')),
                    'fast_break_points': _to_int(boxscore.get('PTFB')),
                    'points_in_paint': _to_int(boxscore.get('PT2IN')),
                    'second_chance_points': _to_int(boxscore.get('PT2ND')),
                    'efficiency': _to_int(boxscore.get('EFF')),
                    'plus_minus': _to_int(boxscore.get('PLUSMINUS')),
                    'ast_to_ratio': _to_float(boxscore.get('AST_TO')),
                    'efg_pct': _to_float(boxscore.get('EFG')),
                    'ts_pct': _to_float(boxscore.get('TS')),
                    'usg_pct': _to_float(boxscore.get('USG')),
                }
            )

    return rows


def run(input_path: Path, dry_run: bool = False, with_play_by_play: bool = False) -> None:
    payload = json.loads(input_path.read_text(encoding='utf-8'))
    teams = _extract_teams(payload)
    games = _extract_games(payload)
    game_team_stats = _extract_game_team_stats(payload)
    players = _extract_players(payload)
    player_game_stats = _extract_player_game_stats(payload)
    play_by_play = _extract_play_by_play(payload) if with_play_by_play else []

    print(f'input={input_path}')
    print(
        f'teams={len(teams)} games={len(games)} '
        f'game_team_stats={len(game_team_stats)} '
        f'players={len(players)} player_game_stats={len(player_game_stats)} '
        f'play_by_play={len(play_by_play)}'
    )
    print(f'with_play_by_play={with_play_by_play}')

    if dry_run:
        print('dry-run mode: skip upsert')
        return

    upsert_teams(teams)
    upsert_games(games)
    upsert_game_team_stats(game_team_stats)
    upsert_players(players)
    upsert_player_game_stats(player_game_stats)
    if with_play_by_play:
        upsert_play_by_play(play_by_play)
    print('upsert completed')


def main() -> None:
    parser = argparse.ArgumentParser(description='UPSERT opening-week game JSON to Supabase')
    parser.add_argument('--input', type=str, default='', help='Path to games_***_opening_week.json')
    parser.add_argument('--dry-run', action='store_true', help='Validate transform without DB upsert')
    parser.add_argument(
        '--with-play-by-play',
        action='store_true',
        help='Also upsert play_by_play table (default: disabled)',
    )
    args = parser.parse_args()

    data_dir = Path(__file__).resolve().parent.parent / 'data'
    input_path = Path(args.input) if args.input else _latest_opening_week_json(data_dir)
    run(
        input_path=input_path,
        dry_run=args.dry_run,
        with_play_by_play=args.with_play_by_play,
    )


if __name__ == '__main__':
    main()
