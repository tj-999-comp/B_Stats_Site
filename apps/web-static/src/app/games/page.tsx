'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { GameRows } from '../../components/GameRows';
import { ErrorState, LoadingState } from '../../components/LoadState';
import { SeasonSelect } from '../../components/SeasonSelect';
import { loadGames, loadSeasons } from '../../lib/stats';
import type { NamedGame } from '../../lib/stats';

function GamesContent() {
  const params = useSearchParams();
  const [seasons, setSeasons] = useState<string[]>([]);
  const [season, setSeason] = useState(params.get('season') ?? '');
  const [games, setGames] = useState<NamedGame[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSeasons().then((available) => {
      setSeasons(available);
      setSeason((current) => current || available[0] || '');
    }).catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    if (!season) return;
    setGames(null);
    setError(null);
    loadGames(season).then(setGames).catch((reason: Error) => setError(reason.message));
  }, [season]);

  return (
    <>
      <div className="page-heading"><div className="container"><p className="eyebrow">GAME CENTER</p><h1>試合一覧</h1><p>シーズンを選んで、試合結果とボックススコアを確認します。</p></div></div>
      <main className="container main-content">
        {seasons.length > 0 && <SeasonSelect seasons={seasons} value={season} onChange={setSeason} />}
        <section className="section">
          {error && <ErrorState message={error} />}
          {!error && !games && <LoadingState />}
          {games && <div className="panel"><GameRows games={games} /></div>}
        </section>
      </main>
    </>
  );
}

export default function GamesPage() {
  return <Suspense fallback={<main className="container main-content"><LoadingState /></main>}><GamesContent /></Suspense>;
}
