-- Lightweight schema draft (teams + games only)
-- play_by_play table is intentionally excluded.

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    team_name_j TEXT NOT NULL,
    team_name_e TEXT,
    team_short_name_j TEXT,
    team_short_name_e TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS games (
    schedule_key BIGINT PRIMARY KEY,
    season TEXT NOT NULL,
    code INTEGER NOT NULL,
    convention_key TEXT NOT NULL,
    convention_name_j TEXT NOT NULL,
    convention_name_e TEXT,
    year INTEGER NOT NULL,
    setu TEXT,
    max_period SMALLINT NOT NULL,
    game_current_period SMALLINT,
    game_datetime_unix BIGINT NOT NULL,
    stadium_cd TEXT,
    stadium_name_j TEXT,
    stadium_name_e TEXT,
    attendance INTEGER,
    game_ended_flg BOOLEAN NOT NULL DEFAULT FALSE,
    record_fixed_flg BOOLEAN NOT NULL DEFAULT FALSE,
    boxscore_exists_flg BOOLEAN NOT NULL DEFAULT FALSE,
    play_by_play_exists_flg BOOLEAN NOT NULL DEFAULT FALSE,
    home_team_id TEXT NOT NULL REFERENCES teams(team_id),
    away_team_id TEXT NOT NULL REFERENCES teams(team_id),
    home_team_score_q1 SMALLINT,
    home_team_score_q2 SMALLINT,
    home_team_score_q3 SMALLINT,
    home_team_score_q4 SMALLINT,
    home_team_score_q5 SMALLINT,
    home_team_score_total SMALLINT,
    away_team_score_q1 SMALLINT,
    away_team_score_q2 SMALLINT,
    away_team_score_q3 SMALLINT,
    away_team_score_q4 SMALLINT,
    away_team_score_q5 SMALLINT,
    away_team_score_total SMALLINT,
    referee_id BIGINT,
    referee_name_j TEXT,
    sub_referee_id_1 BIGINT,
    sub_referee_name_j_1 TEXT,
    sub_referee_id_2 BIGINT,
    sub_referee_name_j_2 TEXT,
    source_tab SMALLINT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (home_team_id <> away_team_id)
);

CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
CREATE INDEX IF NOT EXISTS idx_games_game_datetime_unix ON games(game_datetime_unix);
CREATE INDEX IF NOT EXISTS idx_games_home_team_id ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team_id ON games(away_team_id);

-- Game-level team stats (columns based on B.League Analytics stats pages)
-- Sources:
-- - https://bleagueanalytics.net/スタッツ/stats
-- - https://bleagueanalytics.net/スタッツ/stats/2
-- Formula reference:
-- - https://www.basketball-reference.com/about/glossary.html
CREATE TABLE IF NOT EXISTS game_team_stats (
    schedule_key BIGINT NOT NULL REFERENCES games(schedule_key) ON DELETE CASCADE,
    team_id TEXT NOT NULL REFERENCES teams(team_id),
    opponent_team_id TEXT REFERENCES teams(team_id),
    is_home BOOLEAN NOT NULL,

    -- basic box-like stats
    points INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fg_pct NUMERIC(8, 4),
    fg2m INTEGER,
    fg2a INTEGER,
    fg2_pct NUMERIC(8, 4),
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct NUMERIC(8, 4),
    ftm INTEGER,
    fta INTEGER,
    ft_pct NUMERIC(8, 4),
    off_rebounds INTEGER,
    def_rebounds INTEGER,
    total_rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    blocks_received INTEGER,
    turnovers INTEGER,
    fouls INTEGER,
    fouls_drawn INTEGER,
    dunks INTEGER,
    fast_break_points INTEGER,
    second_chance_points INTEGER,
    points_in_paint INTEGER,

    -- possession / pace / ratings
    possession NUMERIC(10, 4),
    pace NUMERIC(10, 4),
    off_rtg NUMERIC(10, 4),
    def_rtg NUMERIC(10, 4),
    net_rtg NUMERIC(10, 4),
    ast_rtg NUMERIC(10, 4),
    tov_rtg NUMERIC(10, 4),
    pft_rtg NUMERIC(10, 4),
    scp_rtg NUMERIC(10, 4),

    -- efficiency / ratio stats
    efg_pct NUMERIC(8, 4),
    ts_pct NUMERIC(8, 4),
    ast_pct NUMERIC(8, 4),
    tov_pct NUMERIC(8, 4),
    ast_tov_ratio NUMERIC(10, 4),
    play_pct NUMERIC(8, 4),
    ft_d_pct NUMERIC(8, 4),
    ft_freq NUMERIC(8, 4),
    ft_rate NUMERIC(8, 4),
    orb_pct NUMERIC(8, 4),
    drb_pct NUMERIC(8, 4),
    pft_pct NUMERIC(8, 4),
    fbp_pct NUMERIC(8, 4),
    scp_pct NUMERIC(8, 4),
    pitp_pct NUMERIC(8, 4),
    perimeter_pts_pct NUMERIC(8, 4),
    pt2_attempt_pct NUMERIC(8, 4),
    pt3_attempt_pct NUMERIC(8, 4),
    pt2_points_share NUMERIC(8, 4),
    pt3_points_share NUMERIC(8, 4),
    ft_points_share NUMERIC(8, 4),
    live_tov_pct NUMERIC(8, 4),
    dead_tov_pct NUMERIC(8, 4),
    live_tov_share NUMERIC(8, 4),
    dead_tov_share NUMERIC(8, 4),
    shot_chances NUMERIC(10, 4),
    off_success_count NUMERIC(10, 4),
    or_chances NUMERIC(10, 4),
    dr_chances NUMERIC(10, 4),
    tom NUMERIC(10, 4),
    eff NUMERIC(10, 4),
    vps NUMERIC(10, 4),

    -- contextual splits / extras from stats glossary
    home_efg_pct NUMERIC(8, 4),
    away_efg_pct NUMERIC(8, 4),
    home_ts_pct NUMERIC(8, 4),
    away_ts_pct NUMERIC(8, 4),
    home_off_rtg NUMERIC(10, 4),
    away_off_rtg NUMERIC(10, 4),
    close_win_3pts_or_less INTEGER,
    close_loss_3pts_or_less INTEGER,
    pythagorean_win_pct NUMERIC(8, 4),

    -- opponent metrics (from /stats/2)
    opp_possession NUMERIC(10, 4),
    opp_efg_pct NUMERIC(8, 4),
    opp_ts_pct NUMERIC(8, 4),
    opp_fg2_pct NUMERIC(8, 4),
    opp_fg3_pct NUMERIC(8, 4),
    opp_pt2_attempt_pct NUMERIC(8, 4),
    opp_pt3_attempt_pct NUMERIC(8, 4),
    opp_pt2_points_share NUMERIC(8, 4),
    opp_pt3_points_share NUMERIC(8, 4),
    opp_ft_points_share NUMERIC(8, 4),
    opp_ast_pct NUMERIC(8, 4),
    opp_ast_tov_ratio NUMERIC(10, 4),
    opp_ast_rtg NUMERIC(10, 4),
    opp_tov_pct NUMERIC(8, 4),
    opp_orb_pct NUMERIC(8, 4),
    opp_drb_pct NUMERIC(8, 4),
    opp_shot_chances NUMERIC(10, 4),
    opp_success_count NUMERIC(10, 4),
    opp_ft_d_pct NUMERIC(8, 4),
    opp_ft_rate NUMERIC(8, 4),
    opp_fbp_pct NUMERIC(8, 4),
    opp_scp_pct NUMERIC(8, 4),
    opp_scp_rtg NUMERIC(10, 4),
    opp_pitp_pct NUMERIC(8, 4),
    opp_perimeter_pts_pct NUMERIC(8, 4),
    opp_pft_pct NUMERIC(8, 4),
    opp_pft_rtg NUMERIC(10, 4),
    opp_vps NUMERIC(10, 4),
    home_opp_efg_pct NUMERIC(8, 4),
    away_opp_efg_pct NUMERIC(8, 4),
    home_opp_ts_pct NUMERIC(8, 4),
    away_opp_ts_pct NUMERIC(8, 4),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (schedule_key, team_id)
);

CREATE INDEX IF NOT EXISTS idx_game_team_stats_team_id ON game_team_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_game_team_stats_opp_team_id ON game_team_stats(opponent_team_id);

-- Players master table
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    player_name_j TEXT NOT NULL,
    player_name_e TEXT,
    last_seen_team_id TEXT REFERENCES teams(team_id),
    last_seen_jersey_number TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_players_last_seen_team_id ON players(last_seen_team_id);

-- Player game-level stats (from BoxScores with PeriodCategory=18)
CREATE TABLE IF NOT EXISTS player_game_stats (
    schedule_key BIGINT NOT NULL REFERENCES games(schedule_key) ON DELETE CASCADE,
    player_id TEXT NOT NULL REFERENCES players(player_id),
    team_id TEXT NOT NULL REFERENCES teams(team_id),
    jersey_number TEXT,
    is_starter BOOLEAN NOT NULL DEFAULT FALSE,
    is_playing BOOLEAN NOT NULL DEFAULT FALSE,
    play_time TEXT,

    -- basic box score stats
    points INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fg_pct NUMERIC(8, 4),
    fg2m INTEGER,
    fg2a INTEGER,
    fg2_pct NUMERIC(8, 4),
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct NUMERIC(8, 4),
    ftm INTEGER,
    fta INTEGER,
    ft_pct NUMERIC(8, 4),
    off_rebounds INTEGER,
    def_rebounds INTEGER,
    total_rebounds INTEGER,
    assists INTEGER,
    turnovers INTEGER,
    steals INTEGER,
    blocks INTEGER,
    blocks_received INTEGER,
    fouls INTEGER,
    fouls_drawn INTEGER,
    fast_break_points INTEGER,
    points_in_paint INTEGER,
    second_chance_points INTEGER,

    -- advanced metrics
    efficiency INTEGER,
    plus_minus INTEGER,
    ast_to_ratio NUMERIC(8, 4),
    efg_pct NUMERIC(8, 4),
    ts_pct NUMERIC(8, 4),
    usg_pct NUMERIC(8, 4),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (schedule_key, player_id)
);

CREATE INDEX IF NOT EXISTS idx_player_game_stats_player_id ON player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_team_id ON player_game_stats(team_id);

