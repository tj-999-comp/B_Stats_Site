-- Bリーグスタッツ 初期マイグレーション

-- 選手スタッツテーブル
CREATE TABLE IF NOT EXISTS player_stats (
    id BIGSERIAL PRIMARY KEY,
    season TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    games_played INTEGER NOT NULL DEFAULT 0,
    points NUMERIC(5, 1) NOT NULL DEFAULT 0,
    rebounds NUMERIC(5, 1) NOT NULL DEFAULT 0,
    assists NUMERIC(5, 1) NOT NULL DEFAULT 0,
    steals NUMERIC(5, 1) NOT NULL DEFAULT 0,
    blocks NUMERIC(5, 1) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (season, player_name, team_name)
);

-- チームスタッツテーブル
CREATE TABLE IF NOT EXISTS team_stats (
    id BIGSERIAL PRIMARY KEY,
    season TEXT NOT NULL,
    team_name TEXT NOT NULL,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    win_rate NUMERIC(5, 3) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (season, team_name)
);

-- 順位表テーブル
CREATE TABLE IF NOT EXISTS rankings (
    id BIGSERIAL PRIMARY KEY,
    season TEXT NOT NULL,
    rank INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    conference TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (season, conference, rank)
);

-- Row Level Security (RLS) の有効化
ALTER TABLE player_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE rankings ENABLE ROW LEVEL SECURITY;

-- 認証済みユーザーのみ読み取り可能なポリシー
CREATE POLICY "Authenticated users can read player_stats"
    ON player_stats FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can read team_stats"
    ON team_stats FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can read rankings"
    ON rankings FOR SELECT
    TO authenticated
    USING (true);

-- updated_at 自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_player_stats_updated_at
    BEFORE UPDATE ON player_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_team_stats_updated_at
    BEFORE UPDATE ON team_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_rankings_updated_at
    BEFORE UPDATE ON rankings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
