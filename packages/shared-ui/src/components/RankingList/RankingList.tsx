import type { ReactNode } from 'react';

export type RankingItem = {
  rank: number;
  label: string;
  secondary?: string;
  value: ReactNode;
};

type RankingListProps = {
  title: string;
  items: RankingItem[];
  emptyMessage?: string;
};

export function RankingList({ title, items, emptyMessage = 'データがありません。' }: RankingListProps) {
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
