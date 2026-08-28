export function LoadingState() {
  return <p className="loading-state" role="status">データを読み込んでいます…</p>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="error-state" role="alert"><strong>データを読み込めませんでした</strong><span>{message}</span></div>;
}
