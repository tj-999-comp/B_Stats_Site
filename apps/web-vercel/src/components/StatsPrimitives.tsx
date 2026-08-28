import type { ReactNode } from 'react';

export type StatsColumn<T> = {
  key: string;
  header: string;
  align?: 'left' | 'right';
  render: (row: T) => ReactNode;
};

export function StatsTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = 'データがありません。',
}: {
  columns: StatsColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string | number;
  emptyMessage?: string;
}) {
  return (
    <div className="stats-table-wrap">
      <table className="stats-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.align === 'right' ? 'is-right' : undefined} scope="col">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="empty-cell" colSpan={columns.length}>{emptyMessage}</td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr key={rowKey(row, index)}>
                {columns.map((column) => (
                  <td key={column.key} className={column.align === 'right' ? 'is-right' : undefined}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export function PlayerCard({
  rank,
  playerName,
  teamName,
  gamesPlayed,
  averagePoints,
}: {
  rank: number;
  playerName: string;
  teamName: string;
  gamesPlayed: number;
  averagePoints: number;
}) {
  return (
    <article className="player-card">
      <span className="player-card-rank">{rank}</span>
      <div>
        <strong>{playerName}</strong>
        <span className="muted-text">{teamName} · {gamesPlayed}試合</span>
      </div>
      <strong className="player-card-value">{averagePoints.toFixed(1)}<small> PPG</small></strong>
    </article>
  );
}

export type RankingItem = {
  rank: number;
  label: string;
  secondary?: string;
  value: ReactNode;
};

export function RankingList({
  title,
  items,
  emptyMessage = 'データがありません。',
}: {
  title: string;
  items: RankingItem[];
  emptyMessage?: string;
}) {
  return (
    <section className="ranking-list" aria-labelledby={`${title}-heading`}>
      <div className="section-heading compact-heading">
        <h3 id={`${title}-heading`}>{title}</h3>
      </div>
      {items.length === 0 ? <p className="empty-state">{emptyMessage}</p> : (
        <ol>
          {items.map((item) => (
            <li key={`${item.rank}-${item.label}`}>
              <span className="ranking-number">{item.rank}</span>
              <span className="ranking-label"><strong>{item.label}</strong>{item.secondary && <small>{item.secondary}</small>}</span>
              <strong className="ranking-value">{item.value}</strong>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
