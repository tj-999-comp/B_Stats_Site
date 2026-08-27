import {
  getGame,
  getGameTeamStats,
  getGames,
  getPlayerGameStats,
  getPlayerGameStatsForGame,
  getPlayers,
  getSeasons,
  getTeams,
} from '@bleague-stats/supabase-client/queries';
import type {
  Game,
  GameTeamStats,
  Player,
  PlayerGameStats,
  Team,
} from '@bleague-stats/supabase-client/types';

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

function throwIfError(error: { message: string } | null) {
  if (error) {
    throw new Error(error.message);
  }
}

function toTeamMap(teams: Team[]) {
  return new Map(teams.map((team) => [team.team_id, team]));
}

function isCompleted(game: Game) {
  return game.game_ended_flg && game.home_team_score_total !== null && game.away_team_score_total !== null;
}

export async function loadSeasons() {
  const { data, error } = await getSeasons();
  throwIfError(error);
  return Array.from(new Set((data ?? []).map((row) => row.season))).sort().reverse();
}

export async function loadSeasonData(season: string): Promise<SeasonData> {
  const [gamesResult, teamsResult, playersResult] = await Promise.all([getGames(season), getTeams(), getPlayers()]);
  throwIfError(gamesResult.error);
  throwIfError(teamsResult.error);
  throwIfError(playersResult.error);

  const games = (gamesResult.data ?? []) as unknown as Game[];
  const teams = (teamsResult.data ?? []) as unknown as Team[];
  const players = (playersResult.data ?? []) as unknown as Player[];
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

  for (const row of (statsResult.data ?? []) as unknown as PlayerGameStats[]) {
    if (!row.is_playing || row.points === null || !playerMap.has(row.player_id)) {
      continue;
    }
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
  for (const team of teams) {
    records.set(team.team_id, { wins: 0, losses: 0 });
  }
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
  const teamMap = toTeamMap((teamsResult.data ?? []) as unknown as Team[]);
  return ((gamesResult.data ?? []) as unknown as Game[]).map((game) => ({
    ...game,
    home_team_name: teamMap.get(game.home_team_id)?.team_name_j ?? game.home_team_id,
    away_team_name: teamMap.get(game.away_team_id)?.team_name_j ?? game.away_team_id,
  }));
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
  if (!gameResult.data) {
    throw new Error('指定された試合が見つかりません。');
  }

  const teams = (teamsResult.data ?? []) as unknown as Team[];
  const players = (playersResult.data ?? []) as unknown as Player[];
  const teamMap = toTeamMap(teams);
  const playerMap = new Map(players.map((player) => [player.player_id, player]));
  const teamStats = (teamStatsResult.data ?? []) as unknown as GameTeamStats[];
  const playerStats = (playerStatsResult.data ?? []) as unknown as PlayerGameStats[];

  return {
    game: gameResult.data as unknown as Game,
    homeTeam: teamMap.get((gameResult.data as unknown as Game).home_team_id),
    awayTeam: teamMap.get((gameResult.data as unknown as Game).away_team_id),
    teamStats,
    players: playerStats
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
  if (game.game_date) {
    return game.game_date;
  }
  if (game.game_datetime) {
    return game.game_datetime;
  }
  if (game.game_datetime_unix) {
    return new Date(game.game_datetime_unix * 1000).toLocaleDateString('ja-JP');
  }
  return '日付不明';
}

export function displayNumber(value: number | null | undefined, digits = 0) {
  return value === null || value === undefined ? '—' : value.toFixed(digits);
}
