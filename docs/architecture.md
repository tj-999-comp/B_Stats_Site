# アーキテクチャ図

詳細は [README.md](../README.md) を参照してください。

## システム全体構成

```
GitHub Actions (定期スクレイピング: 毎日深夜)
    ↓ INSERT/UPSERT
Supabase PostgreSQL (無料枠・共有DB)
    ├── REST API/GraphQL → GitHub Pages (構成1)
    └── SQL直接クエリ  → Vercel (構成2)
```

## パッケージ構成

```
bleague-stats/
├── apps/
│   ├── web-static/   # 構成1: GitHub Pages (Next.js static export)
│   └── web-vercel/   # 構成2: Vercel (Next.js SSR/ISR)
├── packages/
│   ├── shared-ui/          # 共通UIコンポーネント
│   ├── supabase-client/    # Supabase接続・型定義
│   └── eslint-config/      # 共通ESLint設定
└── scraper/          # Pythonスクレイパー
```

## データフロー

1. GitHub Actionsがスクレイパーを定期実行
2. スクレイパーがBリーグ公式サイトからデータ取得
3. SupabaseのPostgreSQLにデータを保存（UPSERT）
4. フロントエンドがSupabaseからデータ取得して表示
