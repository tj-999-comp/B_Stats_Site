import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'B.LEAGUE Stats',
  description: 'B.LEAGUEの試合・チーム・選手スタッツ',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body>
        <header className="site-header">
          <div className="container header-inner">
            <Link className="brand" href="/">
              <span className="brand-mark">B</span>
              <span>B.LEAGUE <em>STATS</em></span>
            </Link>
            <nav className="site-nav" aria-label="メインナビゲーション">
              <Link href="/">概要</Link>
              <Link href="/games/">試合一覧</Link>
            </nav>
          </div>
        </header>
        {children}
        <footer className="site-footer">
          <div className="container footer-inner">
            <span>B.LEAGUE STATS</span>
            <span>公開データをもとにした統計ビューア</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
