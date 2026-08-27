'use client';

import Link from 'next/link';
import { StatsTable } from '@bleague-stats/shared-ui';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ErrorState, LoadingState } from '../../../components/LoadState';
import { displayNumber, formatGameDate, loadGameDetail } from '../../../lib/stats';
import type { GameDetail } from '../../../lib/stats';

export default function GameDetailContent() {
  const params = useSearchParams();
  const scheduleKey = Number(params.get('scheduleKey'));
  const [data, setData] = useState<GameDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isSafeInteger(scheduleKey) || scheduleKey <= 0) {
      setError('試合番号が指定されていません。');
      return;
    }
    loadGameDetail(scheduleKey).then(setData).catch((reason: Error) => setError(reason.message));
  }, [scheduleKey]);

  return (
    <>
      <div className="page-heading"><div className="container"><Link className="section-link" href="/games/">← 試合一覧に戻る</Link><p className="eyebrow" style={{ marginTop: 24 }}>GAME DETAIL</p><h1>試合詳細</h1></div></div>
      <main className="container main-content">
        {error && <ErrorState message={error} />}
        {!error && !data && <LoadingState />}
        {data && <>
          <section className="panel detail-score">
            <div className="detail-team"><strong>{data.homeTeam?.team_name_j ?? data.game.home_team_id}</strong><span>HOME</span></div>
            <div className="detail-scoreline"><span>{displayNumber(data.game.home_team_score_total)} — {displayNumber(data.game.away_team_score_total)}</span><small>{formatGameDate(data.game)}</small></div>
            <div className="detail-team"><strong>{data.awayTeam?.team_name_j ?? data.game.away_team_id}</strong><span>AWAY</span></div>
          </section>
          <section className="section detail-grid">
            {data.teamStats.map((stats) => <div className="panel" key={stats.team_id}><div className="section-heading"><h2>{stats.team_id === data.game.home_team_id ? data.homeTeam?.team_name_j : data.awayTeam?.team_name_j}</h2></div><StatsTable columns={[
              { key: 'points', header: 'PTS', align: 'right', render: (row) => displayNumber(row.points) },
              { key: 'fg', header: 'FG', align: 'right', render: (row) => `${displayNumber(row.fgm)}/${displayNumber(row.fga)}` },
              { key: 'rebounds', header: 'REB', align: 'right', render: (row) => displayNumber(row.total_rebounds) },
              { key: 'assists', header: 'AST', align: 'right', render: (row) => displayNumber(row.assists) },
              { key: 'turnovers', header: 'TO', align: 'right', render: (row) => displayNumber(row.turnovers) },
            ]} rows={[stats]} rowKey={(row) => row.team_id} /></div>)}
          </section>
          <section className="section"><div className="section-heading"><h2>選手スタッツ</h2></div><div className="panel"><StatsTable columns={[
            { key: 'player', header: 'PLAYER', render: (row) => row.player_name },
            { key: 'team', header: 'TEAM', render: (row) => row.team_name },
            { key: 'points', header: 'PTS', align: 'right', render: (row) => displayNumber(row.points) },
            { key: 'rebounds', header: 'REB', align: 'right', render: (row) => displayNumber(row.total_rebounds) },
            { key: 'assists', header: 'AST', align: 'right', render: (row) => displayNumber(row.assists) },
            { key: 'plus-minus', header: '+/-', align: 'right', render: (row) => displayNumber(row.plus_minus) },
          ]} rows={data.players} rowKey={(row) => `${row.team_id}-${row.player_id}`} emptyMessage="選手スタッツがありません。" /></div></section>
        </>}
      </main>
    </>
  );
}
