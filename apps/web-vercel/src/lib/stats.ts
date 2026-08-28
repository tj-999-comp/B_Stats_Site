import { createClient } from '@supabase/supabase-js';

type Table<Row> = { Row: Row; Insert: Partial<Row>; Update: Partial<Row>; Relationships: [] };

export type Game = {
  schedule_key: number;
  season: string;
  game_type: string | null;
  game_datetime_unix: number;
  game_datetime: string | null;
  game_date: string | null;
  game_ended_flg: boolean;
  home_team_id: string;
  away_team_id: string;
  home_team_score_total: number | null;
  away_team_score_total: number | null;
};

export type Team = {
  team_id: string;
  team_name_j: string;
};

export type Player = {
  player_id: string;
  player_name_j: string;
  entity_type: 'player' | 'staff' | 'placeholder' | 'unresolved';
};

export type GameTeamStats = {
  schedule_key: number;
  team_id: string;
  points: number | null;
  fgm: number | null;
  fga: number | null;
  total_rebounds: number | null;
  assists: number | null;
  turnovers: number | null;
};

export type PlayerGameStats = {
  schedule_key: number;
  player_id: string;
  team_id: string;
  is_playing: boolean;
  points: number | null;
  total_rebounds: number | null;
  assists: number | null;
  plus_minus: number | null;
};

type Database = {
  public: {
    Tables: {
      games: Table<Game>;
      teams: Table<Team>;
      players: Table<Player>;
      game_team_stats: Table<GameTeamStats>;
      player_game_stats: Table<PlayerGameStats>;
    };
  };
};

let client: ReturnType<typeof createClient<Database>> | undefined;

function getClient() {
  if (client) return client;

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!supabaseUrl || !supabasePublishableKey) {
    throw new Error('Supabase public connection is not configured.');
  }

  client = createClient<Database>(supabaseUrl, supabasePublishableKey);
  return client;
}

type QueryResult<T> = { data: T | null; error: { message: string } | null };

function query<T>(value: PromiseLike<QueryResult<T>>) {
  return value;
}

function throwIfError(error: { message: string } | null) {
  if (error) throw new Error(error.message);
}

export type NamedGame = Game & {
  home_team_name: string;
  away_team_name: string;
};

export type TeamStanding = {
  team_id: string;
  team_name: string;
  wins: number;
  losses: number;
  games: number;
  win_rate: number;
};

export type PlayerAverage = {
  player_id: string;
  player_name: string;
  team_name: string;
  games_played: number;
  total_points: number;
  average_points: number;
};

export type SeasonData = {
  games: NamedGame[];
  standings: TeamStanding[];
  playerAverages: PlayerAverage[];
};

export type GameDetail = {
  game: Game;
  homeTeam: Team | undefined;
  awayTeam: Team | undefined;
  teamStats: GameTeamStats[];
  players: Array<PlayerGameStats & { player_name: string; team_name: string }>;
};

function toTeamMap(teams: Team[]) {
  return new Map(teams.map((team) => [team.team_id, team]));
}

function isCompleted(game: Game) {
  return game.game_ended_flg && game.home_team_score_total !== null && game.away_team_score_total !== null;
}

export async function loadSeasons() {
  const result = await query(getClient().from('games').select('season').order('season', { ascending: false }) as unknown as PromiseLike<QueryResult<Array<{ season: string }>>>);
  throwIfError(result.error);
  return Array.from(new Set((result.data ?? []).map((row) => row.season))).sort().reverse();
}

async function getGames(season?: string) {
  let request = getClient().from('games').select('*').order('game_datetime_unix', { ascending: false });
  if (season) request = request.eq('season', season);
  return query(request as unknown as PromiseLike<QueryResult<Game[]>>);
}

async function getTeams() {
  return query(getClient().from('teams').select('*').order('team_name_j') as unknown as PromiseLike<QueryResult<Team[]>>);
}

async function getPlayers() {
  return query(getClient().from('players').select('*').eq('entity_type', 'player') as unknown as PromiseLike<QueryResult<Player[]>>);
}

async function getPlayerGameStats(scheduleKeys: number[]) {
  if (scheduleKeys.length === 0) return { data: [], error: null } as QueryResult<PlayerGameStats[]>;
  return query(getClient().from('player_game_stats').select('*').in('schedule_key', scheduleKeys) as unknown as PromiseLike<QueryResult<PlayerGameStats[]>>);
}

export async function loadSeasonData(season: string): Promise<SeasonData> {
  const [gamesResult, teamsResult, playersResult] = await Promise.all([getGames(season), getTeams(), getPlayers()]);
  throwIfError(gamesResult.error);
  throwIfError(teamsResult.error);
  throwIfError(playersResult.error);

  const games = gamesResult.data ?? [];
  const teams = teamsResult.data ?? [];
  const players = playersResult.data ?? [];
  const teamMap = toTeamMap(teams);
  const namedGames = games.map((game) => ({
    ...game,
    home_team_name: teamMap.get(game.home_team_id)?.team_name_j ?? game.home_team_id,
    away_team_name: teamMap.get(game.away_team_id)?.team_name_j ?? game.away_team_id,
  }));

  const statsResult = await getPlayerGameStats(games.map((game) => game.schedule_key));
  throwIfError(statsResult.error);
  const playerMap = new Map(players.map((player) => [player.player_id, player]));
  const aggregate = new Map<string, { team_id: string; games: number; points: number }>();

  for (const row of statsResult.data ?? []) {
    if (!row.is_playing || row.points === null || !playerMap.has(row.player_id)) continue;
    const current = aggregate.get(row.player_id) ?? { team_id: row.team_id, games: 0, points: 0 };
    current.games += 1;
    current.points += row.points;
    aggregate.set(row.player_id, current);
  }

  const playerAverages = Array.from(aggregate.entries())
    .map(([playerId, value]) => ({
      player_id: playerId,
      player_name: playerMap.get(playerId)?.player_name_j ?? playerId,
      team_name: teamMap.get(value.team_id)?.team_name_j ?? value.team_id,
      games_played: value.games,
      total_points: value.points,
      average_points: value.points / value.games,
    }))
    .sort((a, b) => b.average_points - a.average_points || b.games_played - a.games_played || a.player_name.localeCompare(b.player_name, 'ja'));

  const records = new Map<string, { wins: number; losses: number }>();
  for (const team of teams) records.set(team.team_id, { wins: 0, losses: 0 });
  for (const game of games.filter(isCompleted)) {
    const home = records.get(game.home_team_id) ?? { wins: 0, losses: 0 };
    const away = records.get(game.away_team_id) ?? { wins: 0, losses: 0 };
    if (game.home_team_score_total! > game.away_team_score_total!) {
      home.wins += 1;
      away.losses += 1;
    } else if (game.home_team_score_total! < game.away_team_score_total!) {
      home.losses += 1;
      away.wins += 1;
    }
    records.set(game.home_team_id, home);
    records.set(game.away_team_id, away);
  }

  const standings = Array.from(records.entries())
    .map(([teamId, record]) => ({
      team_id: teamId,
      team_name: teamMap.get(teamId)?.team_name_j ?? teamId,
      wins: record.wins,
      losses: record.losses,
      games: record.wins + record.losses,
      win_rate: record.wins + record.losses > 0 ? record.wins / (record.wins + record.losses) : 0,
    }))
    .filter((standing) => standing.games > 0)
    .sort((a, b) => b.wins - a.wins || b.win_rate - a.win_rate || a.team_name.localeCompare(b.team_name, 'ja'));

  return { games: namedGames, standings, playerAverages };
}

export async function loadGames(season: string) {
  const [gamesResult, teamsResult] = await Promise.all([getGames(season), getTeams()]);
  throwIfError(gamesResult.error);
  throwIfError(teamsResult.error);
  const teamMap = toTeamMap(teamsResult.data ?? []);
  return (gamesResult.data ?? []).map((game) => ({
    ...game,
    home_team_name: teamMap.get(game.home_team_id)?.team_name_j ?? game.home_team_id,
    away_team_name: teamMap.get(game.away_team_id)?.team_name_j ?? game.away_team_id,
  }));
}

async function getGame(scheduleKey: number) {
  return query(getClient().from('games').select('*').eq('schedule_key', scheduleKey).maybeSingle() as unknown as PromiseLike<QueryResult<Game>>);
}

async function getGameTeamStats(scheduleKey: number) {
  return query(getClient().from('game_team_stats').select('*').eq('schedule_key', scheduleKey).order('is_home', { ascending: false }) as unknown as PromiseLike<QueryResult<GameTeamStats[]>>);
}

async function getPlayerGameStatsForGame(scheduleKey: number) {
  return query(getClient().from('player_game_stats').select('*').eq('schedule_key', scheduleKey).order('team_id') as unknown as PromiseLike<QueryResult<PlayerGameStats[]>>);
}

export async function loadGameDetail(scheduleKey: number): Promise<GameDetail> {
  const [gameResult, teamStatsResult, playerStatsResult, teamsResult, playersResult] = await Promise.all([
    getGame(scheduleKey),
    getGameTeamStats(scheduleKey),
    getPlayerGameStatsForGame(scheduleKey),
    getTeams(),
    getPlayers(),
  ]);
  throwIfError(gameResult.error);
  throwIfError(teamStatsResult.error);
  throwIfError(playerStatsResult.error);
  throwIfError(teamsResult.error);
  throwIfError(playersResult.error);
  if (!gameResult.data) throw new Error('指定された試合が見つかりません。');

  const teamMap = toTeamMap(teamsResult.data ?? []);
  const playerMap = new Map((playersResult.data ?? []).map((player) => [player.player_id, player]));
  return {
    game: gameResult.data,
    homeTeam: teamMap.get(gameResult.data.home_team_id),
    awayTeam: teamMap.get(gameResult.data.away_team_id),
    teamStats: teamStatsResult.data ?? [],
    players: (playerStatsResult.data ?? [])
      .filter((row) => playerMap.has(row.player_id))
      .map((row) => ({
        ...row,
        player_name: playerMap.get(row.player_id)?.player_name_j ?? row.player_id,
        team_name: teamMap.get(row.team_id)?.team_name_j ?? row.team_id,
      }))
      .sort((a, b) => a.team_id.localeCompare(b.team_id) || (b.points ?? 0) - (a.points ?? 0)),
  };
}

export function formatGameDate(game: Pick<Game, 'game_date' | 'game_datetime' | 'game_datetime_unix'>) {
  if (game.game_date) return game.game_date;
  if (game.game_datetime) return game.game_datetime;
  if (game.game_datetime_unix) return new Date(game.game_datetime_unix * 1000).toLocaleDateString('ja-JP');
  return '日付不明';
}

export function displayNumber(value: number | null | undefined, digits = 0) {
  return value === null || value === undefined ? '—' : value.toFixed(digits);
}
