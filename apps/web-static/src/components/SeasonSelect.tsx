'use client';

type SeasonSelectProps = {
  seasons: string[];
  value: string;
  onChange: (season: string) => void;
};

export function SeasonSelect({ seasons, value, onChange }: SeasonSelectProps) {
  return (
    <div className="season-control">
      <label htmlFor="season-select">シーズン</label>
      <select id="season-select" className="season-select" value={value} onChange={(event) => onChange(event.target.value)}>
        {seasons.map((season) => <option key={season} value={season}>{season}</option>)}
      </select>
    </div>
  );
}
