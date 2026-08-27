import Link from 'next/link';
import { StatsTable } from '@bleague-stats/shared-ui';
import { displayNumber, formatGameDate } from '../lib/stats';
import type { NamedGame } from '../lib/stats';

export function GameRows({ games }: { games: NamedGame[] }) {
  return (
    <StatsTable
      columns={[
        { key: 'date', header: 'DATE', render: (game) => formatGameDate(game) },
        { key: 'matchup', header: 'MATCHUP', render: (game) => <Link className="game-link" href={`/games/detail/?scheduleKey=${game.schedule_key}`}>{game.home_team_name} vs {game.away_team_name}</Link> },
        { key: 'score', header: 'SCORE', align: 'right', render: (game) => `${displayNumber(game.home_team_score_total)} — ${displayNumber(game.away_team_score_total)}` },
        { key: 'type', header: 'TYPE', render: (game) => game.game_type ?? '—' },
      ]}
      rows={games}
      rowKey={(game) => game.schedule_key}
      emptyMessage="このシーズンの試合データがありません。"
    />
  );
}
