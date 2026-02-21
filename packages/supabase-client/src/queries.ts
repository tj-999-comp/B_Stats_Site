import { supabase } from './client';

export async function getPlayerStats(season?: string) {
  let query = supabase
    .from('player_stats')
    .select('*')
    .order('points', { ascending: false });

  if (season) {
    query = query.eq('season', season);
  }

  return query;
}

export async function getTeamStats(season?: string) {
  let query = supabase
    .from('team_stats')
    .select('*')
    .order('wins', { ascending: false });

  if (season) {
    query = query.eq('season', season);
  }

  return query;
}

export async function getRankings(season?: string) {
  let query = supabase
    .from('rankings')
    .select('*')
    .order('rank', { ascending: true });

  if (season) {
    query = query.eq('season', season);
  }

  return query;
}
