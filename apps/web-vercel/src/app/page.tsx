'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { PlayerCard, RankingList, StatsTable } from '../components/StatsPrimitives';
import { ErrorState, LoadingState } from '../components/LoadState';
import { SeasonSelect } from '../components/SeasonSelect';
import { displayNumber, formatGameDate, loadSeasonData, loadSeasons } from '../lib/stats';
import type { SeasonData } from '../lib/stats';

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

  const featuredGame = data?.games.find((game) => game.game_ended_flg && game.home_team_score_total !== null && game.away_team_score_total !== null) ?? data?.games[0];
  const topScorer = data?.playerAverages[0];

  return (
    <>
      <section className="hero"><div className="container hero-inner"><div className="hero-copy-block">
        <p className="eyebrow">B STATS / FOR B.LEAGUE FANS</p>
        <h1>B STATS</h1>
        <p className="hero-copy">B.LEAGUEの公開データをもとにした、非公式の第三者ファン統計ビューア。</p>
        <div className="hero-actions">{seasons.length > 0 && <SeasonSelect seasons={seasons} value={season} onChange={setSeason} />}<a className="text-link text-link-light" href="#featured">今季を見る ↓</a></div>
      </div></div></section>
      <main className="container main-content">
        {error && <ErrorState message={error} />}
        {!error && !data && <LoadingState />}
        {data && <>
          <section className="featured-section" id="featured" aria-labelledby="featured-heading"><div className="section-heading section-heading-light"><div><p className="eyebrow">FEATURED / 今見る</p><h2 id="featured-heading">最新確定試合</h2></div><span className="section-index">01 / 04</span></div><div className="featured-grid">
            <article className="featured-card"><div className="featured-label">LATEST VERIFIED GAME</div>{featuredGame ? <><div className="featured-matchup"><span>{featuredGame.home_team_name}</span><b>VS</b><span>{featuredGame.away_team_name}</span></div><div className="featured-score"><strong>{displayNumber(featuredGame.home_team_score_total)}</strong><span>—</span><strong>{displayNumber(featuredGame.away_team_score_total)}</strong></div><div className="featured-meta"><span>{formatGameDate(featuredGame)}</span><Link className="text-link text-link-light" href={`/games/detail/?scheduleKey=${featuredGame.schedule_key}`}>試合詳細 →</Link></div></> : <p className="empty-state">注目の試合がありません。</p>}</article>
            <div className="featured-note"><p className="eyebrow">A QUICK READ</p><p>まずは最新の1試合から。スコアの裏側にあるチームと選手の数字へ進めます。</p>{topScorer && <div className="featured-stat"><span>平均得点上位（当サイト集計）</span><strong>{topScorer.player_name}</strong><b>{topScorer.average_points.toFixed(1)} <small>PPG</small></b></div>}</div>
          </div></section>
          <section className="section" id="rankings"><div className="section-heading"><div><p className="eyebrow">RANKINGS / 順位を見る</p><h2>シーズンの現在地</h2></div><span className="muted-text">{season}</span></div><div className="ranking-grid"><div className="panel"><RankingList title="TEAM / 勝敗順" items={data.standings.slice(0, 5).map((standing, index) => ({ rank: index + 1, label: standing.team_name, secondary: `${standing.wins}勝 ${standing.losses}敗`, value: `${(standing.win_rate * 100).toFixed(1)}%` }))} /></div><div className="panel"><RankingList title="PLAYER / 平均得点" items={data.playerAverages.slice(0, 5).map((player, index) => ({ rank: index + 1, label: player.player_name, secondary: player.team_name, value: `${player.average_points.toFixed(1)} PPG` }))} /></div></div></section>
          <section className="section" id="players"><div className="section-heading"><div><p className="eyebrow">PLAYERS / 選手を知る</p><h2>数字で見つける選手</h2></div><span className="section-index dark-index">03 / 04</span></div><div className="player-grid">{data.playerAverages.slice(0, 3).map((player, index) => <PlayerCard key={player.player_id} rank={index + 1} playerName={player.player_name} teamName={player.team_name} gamesPlayed={player.games_played} averagePoints={player.average_points} />)}</div></section>
          <section className="section games-section" id="games"><div className="section-heading"><div><p className="eyebrow">GAMES / 試合を追う</p><h2>最近の試合</h2></div><Link className="section-link" href={`/games/?season=${encodeURIComponent(season)}`}>すべて見る →</Link></div><div className="panel"><StatsTable columns={[{ key: 'date', header: 'DATE', render: (game) => formatGameDate(game) }, { key: 'matchup', header: 'MATCHUP', render: (game) => <Link className="game-link" href={`/games/detail/?scheduleKey=${game.schedule_key}`}>{game.home_team_name} vs {game.away_team_name}</Link> }, { key: 'score', header: 'SCORE', align: 'right', render: (game) => `${displayNumber(game.home_team_score_total)} — ${displayNumber(game.away_team_score_total)}` }]} rows={data.games.slice(0, 6)} rowKey={(game) => game.schedule_key} /></div></section>
          <section className="archive-note" id="about" aria-label="このサイトについて"><p className="eyebrow">ABOUT THIS SITE</p><p>B STATSは、B.LEAGUE公式公開情報をもとにした第三者ファンサイトです。公式情報・観戦体験を補助する統計ビューアとして、集計方法と更新時点を明示して運営します。順位・ランキングは当サイト集計です。</p><span>PUBLIC DATA / {season}</span></section>
        </>}
      </main>
    </>
  );
}
