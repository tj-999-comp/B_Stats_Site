'use client';

import Link from 'next/link';
import { PlayerCard, RankingList, StatsTable } from '@bleague-stats/shared-ui';
import { ErrorState, LoadingState } from '../components/LoadState';
import { SeasonSelect } from '../components/SeasonSelect';
import { displayNumber, formatGameDate, loadSeasonData, loadSeasons } from '../lib/stats';
import type { SeasonData } from '../lib/stats';
import { useEffect, useState } from 'react';

export default function HomePage() {
  const [seasons, setSeasons] = useState<string[]>([]);
  const [season, setSeason] = useState('');
  const [data, setData] = useState<SeasonData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSeasons().then((available) => {
      setSeasons(available);
      setSeason((current) => current || available[0] || '');
    }).catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    if (!season) return;
    setData(null);
    setError(null);
    loadSeasonData(season).then(setData).catch((reason: Error) => setError(reason.message));
  }, [season]);

  return (
    <>
      <section className="hero">
        <div className="container">
          <p className="eyebrow">BASKETBALL DATA, SIMPLIFIED</p>
          <h1>試合の数字から、<br />シーズンの流れを読む。</h1>
          <p className="hero-copy">B.LEAGUEの試合結果、チームスタッツ、選手スタッツをひとつの画面で確認できます。</p>
          {seasons.length > 0 && <SeasonSelect seasons={seasons} value={season} onChange={setSeason} />}
        </div>
      </section>
      <main className="container main-content">
        {error && <ErrorState message={error} />}
        {!error && !data && <LoadingState />}
        {data && (
          <>
            <section className="summary-grid" aria-label="シーズン概要">
              <div className="summary-card"><span>試合数</span><strong>{data.games.length}</strong></div>
              <div className="summary-card"><span>チーム数</span><strong>{data.standings.length}</strong></div>
              <div className="summary-card"><span>選手数</span><strong>{data.playerAverages.length}</strong></div>
            </section>

            <section className="section">
              <div className="section-heading"><h2>基本ランキング</h2><span className="muted-text">{season}</span></div>
              <div className="ranking-grid">
                <div className="panel">
                  <RankingList title="チーム順位" items={data.standings.slice(0, 8).map((standing, index) => ({
                    rank: index + 1,
                    label: standing.team_name,
                    secondary: `${standing.wins}勝 ${standing.losses}敗`,
                    value: `${(standing.win_rate * 100).toFixed(1)}%`,
                  }))} />
                </div>
                <div className="panel">
                  <RankingList title="選手平均得点" items={data.playerAverages.slice(0, 8).map((player, index) => ({
                    rank: index + 1,
                    label: player.player_name,
                    secondary: player.team_name,
                    value: `${player.average_points.toFixed(1)} PPG`,
                  }))} />
                </div>
              </div>
            </section>

            <section className="section">
              <div className="section-heading"><h2>選手平均得点 TOP 6</h2></div>
              <div className="player-grid">
                {data.playerAverages.slice(0, 6).map((player, index) => <PlayerCard key={player.player_id} rank={index + 1} playerName={player.player_name} teamName={player.team_name} gamesPlayed={player.games_played} averagePoints={player.average_points} />)}
              </div>
            </section>

            <section className="section">
              <div className="section-heading"><h2>最近の試合</h2><Link className="section-link" href={`/games/?season=${encodeURIComponent(season)}`}>すべて見る →</Link></div>
              <div className="panel">
                <StatsTable
                  columns={[
                    { key: 'date', header: 'DATE', render: (game) => formatGameDate(game) },
                    { key: 'matchup', header: 'MATCHUP', render: (game) => <Link className="game-link" href={`/games/detail/?scheduleKey=${game.schedule_key}`}>{game.home_team_name} vs {game.away_team_name}</Link> },
                    { key: 'score', header: 'SCORE', align: 'right', render: (game) => `${displayNumber(game.home_team_score_total)} — ${displayNumber(game.away_team_score_total)}` },
                  ]}
                  rows={data.games.slice(0, 6)}
                  rowKey={(game) => game.schedule_key}
                />
              </div>
            </section>
          </>
        )}
      </main>
    </>
  );
}
