# Bリーグスタッツサイト 2構成比較アーキテクチャ

## 構成概要

スクレイピングしたBリーグのスタッツデータを2つの異なる構成でWebサイト化し、静的サイトとサーバーサイドレンダリングの違いを検証する。個人利用のため、認証機能を実装してアクセス制限をかける。

---

## 構成1: GitHub Pages（静的サイト + クライアント側クエリ）

### アーキテクチャ
```
GitHub Actions (定期スクレイピング)
    ↓ INSERT/UPSERT
Supabase PostgreSQL (無料枠・共有DB)
    ↕ REST API/GraphQL
GitHub Pages (Next.js静的サイト: output: 'export')
    ↕ 静的ファイル配信
ユーザー (ブラウザ)
    - 認証チェック（Supabase Auth）
    - クライアント側でフィルタリング・ソート
    - Supabase APIを直接叩く
```

### 特徴
- ✓ 完全無料（GitHub Pages + Supabase無料枠）
- ✓ サーバー管理不要
- ✓ クライアント側でクエリ処理
- ✓ データ更新は自動（GitHub Actions）
- ✓ フロント再デプロイ不要
- ✓ Supabase Authで認証実装可能

### メリット
- 完全無料
- サーバーレス
- シンプルな構成
- CDN配信で高速

### デメリット
- 初回表示が遅い可能性
- 大量データだとクライアント処理が重い
- 静的サイトなので認証はクライアント側のみ（バイパス可能性あり）

### 認証方式
- **Supabase Authentication**を使用
  - Email + Password認証
  - 多要素認証（MFA）対応可能
  - Row Level Security (RLS)でDB側でもアクセス制限

---

## 構成2: Vercel（SSR/ISR + サーバーサイドクエリ）

### アーキテクチャ
```
GitHub Actions (定期スクレイピング)
    ↓ INSERT/UPSERT
Supabase PostgreSQL (無料枠・共有DB)
    ↕ SQL直接クエリ
Vercel Hobby Plan (Next.js App Router: SSR/ISR)
    - Middleware で認証チェック
    - Server Componentsでサーバー側クエリ
    ↕ SSR/ISR HTML配信
ユーザー (ブラウザ)
    - サーバー側で認証済みページを受け取る
    - HTMLとして処理済みページを受け取る
```

### 特徴
- ✓ 無料（Vercel Hobby + Supabase無料枠）
- ✓ サーバーサイドでクエリ実行
- ✓ Middlewareでサーバー側認証（より安全）
- ✓ ISRで効率的キャッシュ
- ✓ Server Components活用可能

### メリット
- 高速な初回表示
- サーバー側で複雑なクエリ可能
- ユーザー体験が良い
- Middlewareでサーバー側認証（セキュアな制限）

### デメリット
- Vercelの無料枠制限（月間100GBトラフィック、関数実行時間制限）
- やや複雑な構成

### 認証方式
- **Supabase Authentication + Next.js Middleware**
  - Middlewareで全ページを認証保護
  - 未認証ユーザーは自動的にログインページへリダイレクト
  - 多要素認証（MFA）対応可能
  - セッション管理はSupabase側で自動処理

---

## 共通部分

### データベース
- **Supabase PostgreSQL（無料枠）を両構成で共有**
  - 1つのDBインスタンスに両方のサイトからアクセス
  - Row Level Security (RLS)で認証済みユーザーのみデータアクセス可能に設定

### スクレイピング
- **GitHub Actions**: 定期スクレイピング（毎日深夜など）
- スクレイピングスクリプトは1つ（共有DBに投入）

### 認証システム
- **Supabase Authentication**を使用
  - Email + Password認証
  - **多要素認証（MFA）**: TOTPアプリ（Google Authenticator等）による2段階認証
  - 自分専用のアカウントのみ作成し、新規登録を無効化

---

## 実装の進め方

### Phase 1: スクレイピング＋PostgreSQLセットアップ
1. Supabaseプロジェクト作成
2. テーブル設計＋Row Level Security (RLS)設定
3. GitHub Actionsでスクレイパー実装
4. スクレイピング → DB投入の自動化

### Phase 2: 認証システムのセットアップ
1. Supabase Authenticationの設定
2. 自分用のアカウント作成
3. 多要素認証（MFA）の有効化
4. 新規登録の無効化（既存ユーザーのみアクセス可能に）

### Phase 3: 構成1（GitHub Pages）実装
1. Next.js（`output: 'export'`）でフロント構築
2. Supabase Auth SDKを統合
3. 認証チェック機能の実装（クライアント側）
4. Supabase REST APIを叩く実装
5. クライアント側でフィルタリング・ランキング生成
6. GitHub Pagesへデプロイ

### Phase 4: 構成2（Vercel）実装
1. Next.js App Routerで同じUIを再構築
2. Middlewareでサーバー側認証実装
3. Server ComponentsでPostgreSQLクエリ
4. SSR/ISRの実装
5. Vercelへデプロイ

### Phase 5: 比較・検証
1. パフォーマンス測定（Lighthouse等）
2. 初回表示速度の比較
3. 認証の安全性比較
4. 運用コスト・複雑さの比較

---

## ドキュメント

- [アーキテクチャ図](docs/architecture.md)
- [セットアップガイド](docs/setup.md)
- [デプロイガイド](docs/deployment.md)
- [テーブル定義書（Supabase 現在値）](docs/table_definition.md)
- [DB設計ブラッシュアップ（改名・移籍対応）](docs/db_design_brushup_identity_history.md)
- [Migration適用ガイド（20260224）](docs/migration_20260224_apply_guide.md)
- [スクレイパーREADME](scraper/README.md)
