import { getSupabaseClient } from './client';
import type { Game, GameTeamStats, Player, PlayerGameStats, Team } from './types';

type QueryResult<T> = { data: T; error: { message: string } | null };
type Query<T> = PromiseLike<QueryResult<T>>;

export function getSeasons(): Query<Array<{ season: string }>> {
  return getSupabaseClient().from('games').select('season').order('season', { ascending: false }) as unknown as Query<Array<{ season: string }>>;
}

export function getGames(season?: string): Query<Game[]> {
  let query = getSupabaseClient()
    .from('games')
    .select(
      'schedule_key, season, code, convention_key, convention_name_j, convention_name_e, year, setu, game_type, max_period, game_current_period, game_datetime_unix, game_datetime, game_date, stadium_cd, stadium_name_j, stadium_name_e, attendance, game_ended_flg, record_fixed_flg, boxscore_exists_flg, play_by_play_exists_flg, home_team_id, away_team_id, home_team_score_total, away_team_score_total, home_team_score_q1, home_team_score_q2, home_team_score_q3, home_team_score_q4, home_team_score_q5, away_team_score_q1, away_team_score_q2, away_team_score_q3, away_team_score_q4, away_team_score_q5, referee_id, referee_name_j, sub_referee_id_1, sub_referee_name_j_1, sub_referee_id_2, sub_referee_name_j_2, source_tab, scraped_at, updated_at',
    )
    .order('game_datetime_unix', { ascending: false });

  if (season) {
    query = query.eq('season', season);
  }

  return query as unknown as Query<Game[]>;
}

export function getTeams(): Query<Team[]> {
  return getSupabaseClient()
    .from('teams')
    .select('team_id, team_name_j, team_name_e, team_short_name_j, team_short_name_e, created_at, updated_at')
    .order('team_name_j') as unknown as Query<Team[]>;
}

export function getPlayers(): Query<Player[]> {
  return getSupabaseClient()
    .from('players')
    .select(
      'player_id, player_name_j, player_name_e, last_seen_team_id, last_seen_jersey_number, player_slot_category, league_registered_nationality, birthplace, entity_type, created_at, updated_at',
    )
    .eq('entity_type', 'player') as unknown as Query<Player[]>;
}

export function getGame(scheduleKey: number): Query<Game | null> {
  return getSupabaseClient().from('games').select('*').eq('schedule_key', scheduleKey).maybeSingle() as unknown as Query<Game | null>;
}

export function getGameTeamStats(scheduleKey: number): Query<GameTeamStats[]> {
  return getSupabaseClient().from('game_team_stats').select('*').eq('schedule_key', scheduleKey).order('is_home', { ascending: false }) as unknown as Query<GameTeamStats[]>;
}

export function getPlayerGameStats(scheduleKeys: number[]): Query<PlayerGameStats[]> {
  if (scheduleKeys.length === 0) {
    return Promise.resolve({ data: [], error: null });
  }

  return getSupabaseClient().from('player_game_stats').select('*').in('schedule_key', scheduleKeys) as unknown as Query<PlayerGameStats[]>;
}

export function getPlayerGameStatsForGame(scheduleKey: number): Query<PlayerGameStats[]> {
  return getSupabaseClient().from('player_game_stats').select('*').eq('schedule_key', scheduleKey).order('team_id') as unknown as Query<PlayerGameStats[]>;
}
