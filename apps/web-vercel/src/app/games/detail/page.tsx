import { Suspense } from 'react';
import { LoadingState } from '../../../components/LoadState';
import GameDetailContent from './GameDetailContent';

export default function GameDetailPage() {
  return <Suspense fallback={<main className="container main-content"><LoadingState /></main>}><GameDetailContent /></Suspense>;
}
