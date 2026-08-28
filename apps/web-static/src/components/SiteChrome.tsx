'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const navigationItems = [
  { label: '概要', href: '/#featured' },
  { label: '試合', href: '/games/' },
  { label: '順位', href: '/#rankings' },
  { label: '選手', href: '/#players' },
  { label: 'サイトについて', href: '/#about' },
];

export function SiteChrome({ children }: Readonly<{ children: React.ReactNode }>) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    if (!isMenuOpen) return undefined;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsMenuOpen(false);
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isMenuOpen]);

  const closeMenu = () => setIsMenuOpen(false);

  return (
    <>
      <header className="site-header">
        <div className="container header-inner">
          <Link className="brand" href="/" onClick={closeMenu} aria-label="B.LEAGUE STATS 概要へ">
            <span className="brand-mark" aria-hidden="true">B</span>
            <span>B <em>STATS</em></span>
          </Link>
          <nav className="site-nav desktop-nav" aria-label="メインナビゲーション">
            {navigationItems.slice(0, 4).map((item) => <Link key={item.href} href={item.href}>{item.label}</Link>)}
          </nav>
          <button
            type="button"
            className="menu-button"
            aria-expanded={isMenuOpen}
            aria-controls="mobile-navigation"
            aria-label={isMenuOpen ? 'メニューを閉じる' : 'メニューを開く'}
            onClick={() => setIsMenuOpen((open) => !open)}
          >
            <span aria-hidden="true"><span /><span /><span /></span>
            <b>{isMenuOpen ? 'CLOSE' : 'MENU'}</b>
          </button>
        </div>
        {isMenuOpen && <button type="button" className="menu-scrim" aria-label="メニューを閉じる" onClick={closeMenu} />}
        <nav id="mobile-navigation" className="mobile-menu" aria-label="メインナビゲーション" hidden={!isMenuOpen}>
          {navigationItems.map((item) => <Link key={item.href} href={item.href} onClick={closeMenu}>{item.label}</Link>)}
          <span className="mobile-menu-note">非公式の第三者ファンサイト</span>
        </nav>
      </header>
      {children}
      <footer className="site-footer">
        <div className="container footer-inner">
          <span>B STATS / 非公式ファンサイト</span>
          <span>公開データをもとにした統計ビューア</span>
        </div>
      </footer>
    </>
  );
}
