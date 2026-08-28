import type { Metadata } from 'next';
import './globals.css';
import { SiteChrome } from '../components/SiteChrome';

export const metadata: Metadata = {
  title: 'B STATS | B.LEAGUE 非公式ファン統計',
  description: 'B.LEAGUEの公開データをもとにした、非公式の第三者ファン統計ビューア',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body><SiteChrome>{children}</SiteChrome></body>
    </html>
  );
}
