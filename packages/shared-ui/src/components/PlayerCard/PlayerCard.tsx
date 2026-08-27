type PlayerCardProps = {
  rank: number;
  playerName: string;
  teamName: string;
  gamesPlayed: number;
  averagePoints: number;
};

export function PlayerCard({ rank, playerName, teamName, gamesPlayed, averagePoints }: PlayerCardProps) {
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
