-- 作成日: 2026-05-26
-- 用途: rebuild SQL を1ファイルで実行するための統合スクリプト
-- 実行順: 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07

-- =====================================================================
-- BEGIN: 01_base_schema.sql
-- =====================================================================
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
    year INTEGER NOT NULL,          -- シーズン開始年（Season Year）。game_date から算出: 10-12月→当該年, 1-5月→前年
    setu TEXT,
    game_type TEXT,                 -- 試合区分: setu <= 100 は RS、setu >= 101 は CS
    max_period SMALLINT NOT NULL,
    game_current_period SMALLINT,
    game_datetime_unix BIGINT NOT NULL,
    game_datetime      TEXT,
    game_date          TEXT,
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


-- END: 01_base_schema.sql

-- =====================================================================
-- BEGIN: 02_precheck_identity_history.sql
-- =====================================================================
-- Pre-check for migration 20260224_identity_history
-- Read-only queries

-- 1) required base tables
SELECT
  table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('teams', 'players', 'games', 'player_game_stats')
ORDER BY table_name;

-- 2) object existence before apply
SELECT
  'table' AS object_type,
  table_name AS object_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('team_name_history', 'player_name_history', 'player_affiliations')
UNION ALL
SELECT
  'view' AS object_type,
  table_name AS object_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('v_teams_current', 'v_players_current', 'v_player_transfer_events')
ORDER BY object_type, object_name;

-- 3) current data volume
SELECT 'teams' AS table_name, COUNT(*) AS row_count FROM teams
UNION ALL
SELECT 'players' AS table_name, COUNT(*) AS row_count FROM players
UNION ALL
SELECT 'player_game_stats' AS table_name, COUNT(*) AS row_count FROM player_game_stats;

-- END: 02_precheck_identity_history.sql

-- =====================================================================
-- BEGIN: 03_identity_history.sql
-- =====================================================================
-- Identity/history enhancement for team/player rename and player transfer tracking
-- Compatible with existing UPSERT flow (teams, players, player_game_stats)

-- =========================
-- 1) History tables
-- =========================

CREATE TABLE IF NOT EXISTS team_name_history (
    history_id BIGSERIAL PRIMARY KEY,
    team_id TEXT NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    team_name_j TEXT NOT NULL,
    team_name_e TEXT,
    team_short_name_j TEXT,
    team_short_name_e TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    detected_from TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE INDEX IF NOT EXISTS idx_team_name_history_team_id
    ON team_name_history(team_id);

CREATE INDEX IF NOT EXISTS idx_team_name_history_valid_from
    ON team_name_history(valid_from);

CREATE UNIQUE INDEX IF NOT EXISTS ux_team_name_history_open
    ON team_name_history(team_id)
    WHERE valid_to IS NULL;


CREATE TABLE IF NOT EXISTS player_name_history (
    history_id BIGSERIAL PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    player_name_j TEXT NOT NULL,
    player_name_e TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    detected_from TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE INDEX IF NOT EXISTS idx_player_name_history_player_id
    ON player_name_history(player_id);

CREATE INDEX IF NOT EXISTS idx_player_name_history_valid_from
    ON player_name_history(valid_from);

CREATE UNIQUE INDEX IF NOT EXISTS ux_player_name_history_open
    ON player_name_history(player_id)
    WHERE valid_to IS NULL;


CREATE TABLE IF NOT EXISTS player_affiliations (
    affiliation_id BIGSERIAL PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id TEXT NOT NULL REFERENCES teams(team_id),
    jersey_number TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    first_schedule_key BIGINT REFERENCES games(schedule_key),
    last_schedule_key BIGINT REFERENCES games(schedule_key),
    detected_from TEXT NOT NULL DEFAULT 'game_feed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE INDEX IF NOT EXISTS idx_player_affiliations_player_id
    ON player_affiliations(player_id);

CREATE INDEX IF NOT EXISTS idx_player_affiliations_team_id
    ON player_affiliations(team_id);

CREATE INDEX IF NOT EXISTS idx_player_affiliations_valid_from
    ON player_affiliations(valid_from);

CREATE UNIQUE INDEX IF NOT EXISTS ux_player_affiliations_open
    ON player_affiliations(player_id)
    WHERE valid_to IS NULL;


-- =========================
-- 2) Backfill from current tables
-- =========================

INSERT INTO team_name_history (
    team_id,
    team_name_j,
    team_name_e,
    team_short_name_j,
    team_short_name_e,
    valid_from,
    valid_to,
    detected_from
)
SELECT
    t.team_id,
    t.team_name_j,
    t.team_name_e,
    t.team_short_name_j,
    t.team_short_name_e,
    t.created_at,
    NULL,
    'backfill'
FROM teams t
WHERE NOT EXISTS (
    SELECT 1
    FROM team_name_history h
    WHERE h.team_id = t.team_id
);


INSERT INTO player_name_history (
    player_id,
    player_name_j,
    player_name_e,
    valid_from,
    valid_to,
    detected_from
)
SELECT
    p.player_id,
    p.player_name_j,
    p.player_name_e,
    p.created_at,
    NULL,
    'backfill'
FROM players p
WHERE NOT EXISTS (
    SELECT 1
    FROM player_name_history h
    WHERE h.player_id = p.player_id
);


WITH ordered AS (
    SELECT
        pgs.player_id,
        pgs.team_id,
        pgs.jersey_number,
        pgs.schedule_key,
        TO_TIMESTAMP(g.game_datetime_unix) AS game_at,
        CASE
            WHEN LAG(pgs.team_id) OVER w IS DISTINCT FROM pgs.team_id
              OR LAG(pgs.jersey_number) OVER w IS DISTINCT FROM pgs.jersey_number
            THEN 1
            ELSE 0
        END AS change_flag
    FROM player_game_stats pgs
    JOIN games g ON g.schedule_key = pgs.schedule_key
    WINDOW w AS (PARTITION BY pgs.player_id ORDER BY pgs.schedule_key)
),
segmented AS (
    SELECT
        player_id,
        team_id,
        jersey_number,
        schedule_key,
        game_at,
        SUM(change_flag) OVER (
            PARTITION BY player_id
            ORDER BY schedule_key
            ROWS UNBOUNDED PRECEDING
        ) AS grp
    FROM ordered
),
stints AS (
    SELECT
        player_id,
        team_id,
        jersey_number,
        MIN(schedule_key) AS first_schedule_key,
        MAX(schedule_key) AS last_schedule_key,
        MIN(game_at) AS valid_from
    FROM segmented
    GROUP BY player_id, team_id, jersey_number, grp
),
stints_with_next AS (
    SELECT
        s.*,
        LEAD(s.valid_from) OVER (
            PARTITION BY s.player_id
            ORDER BY s.valid_from, s.first_schedule_key
        ) AS next_valid_from
    FROM stints s
)
INSERT INTO player_affiliations (
    player_id,
    team_id,
    jersey_number,
    valid_from,
    valid_to,
    first_schedule_key,
    last_schedule_key,
    detected_from
)
SELECT
    s.player_id,
    s.team_id,
    s.jersey_number,
    s.valid_from,
    s.next_valid_from,
    s.first_schedule_key,
    s.last_schedule_key,
    'backfill'
FROM stints_with_next s
WHERE NOT EXISTS (
    SELECT 1
    FROM player_affiliations a
    WHERE a.player_id = s.player_id
      AND a.first_schedule_key = s.first_schedule_key
      AND a.team_id = s.team_id
      AND a.jersey_number IS NOT DISTINCT FROM s.jersey_number
)
ON CONFLICT DO NOTHING;


-- =========================
-- 3) Trigger functions
-- =========================

CREATE OR REPLACE FUNCTION track_team_name_history()
RETURNS TRIGGER AS $$
DECLARE
    has_same_open BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM team_name_history h
        WHERE h.team_id = NEW.team_id
          AND h.valid_to IS NULL
          AND h.team_name_j IS NOT DISTINCT FROM NEW.team_name_j
          AND h.team_name_e IS NOT DISTINCT FROM NEW.team_name_e
          AND h.team_short_name_j IS NOT DISTINCT FROM NEW.team_short_name_j
          AND h.team_short_name_e IS NOT DISTINCT FROM NEW.team_short_name_e
    ) INTO has_same_open;

    IF NOT has_same_open THEN
        UPDATE team_name_history
        SET valid_to = NOW()
        WHERE team_id = NEW.team_id
          AND valid_to IS NULL;

        INSERT INTO team_name_history (
            team_id,
            team_name_j,
            team_name_e,
            team_short_name_j,
            team_short_name_e,
            valid_from,
            valid_to,
            detected_from
        )
        VALUES (
            NEW.team_id,
            NEW.team_name_j,
            NEW.team_name_e,
            NEW.team_short_name_j,
            NEW.team_short_name_e,
            NOW(),
            NULL,
            CASE WHEN TG_OP = 'INSERT' THEN 'teams_insert' ELSE 'teams_update' END
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION track_player_name_history()
RETURNS TRIGGER AS $$
DECLARE
    has_same_open BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM player_name_history h
        WHERE h.player_id = NEW.player_id
          AND h.valid_to IS NULL
          AND h.player_name_j IS NOT DISTINCT FROM NEW.player_name_j
          AND h.player_name_e IS NOT DISTINCT FROM NEW.player_name_e
    ) INTO has_same_open;

    IF NOT has_same_open THEN
        UPDATE player_name_history
        SET valid_to = NOW()
        WHERE player_id = NEW.player_id
          AND valid_to IS NULL;

        INSERT INTO player_name_history (
            player_id,
            player_name_j,
            player_name_e,
            valid_from,
            valid_to,
            detected_from
        )
        VALUES (
            NEW.player_id,
            NEW.player_name_j,
            NEW.player_name_e,
            NOW(),
            NULL,
            CASE WHEN TG_OP = 'INSERT' THEN 'players_insert' ELSE 'players_update' END
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION track_player_affiliation_from_game_stats()
RETURNS TRIGGER AS $$
DECLARE
    current_open RECORD;
    event_at TIMESTAMPTZ;
BEGIN
    SELECT TO_TIMESTAMP(g.game_datetime_unix)
      INTO event_at
      FROM games g
     WHERE g.schedule_key = NEW.schedule_key;

    IF event_at IS NULL THEN
        event_at := NOW();
    END IF;

    SELECT *
      INTO current_open
      FROM player_affiliations a
     WHERE a.player_id = NEW.player_id
       AND a.valid_to IS NULL
     ORDER BY a.valid_from DESC, a.affiliation_id DESC
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO player_affiliations (
            player_id,
            team_id,
            jersey_number,
            valid_from,
            valid_to,
            first_schedule_key,
            last_schedule_key,
            detected_from
        )
        VALUES (
            NEW.player_id,
            NEW.team_id,
            NEW.jersey_number,
            event_at,
            NULL,
            NEW.schedule_key,
            NEW.schedule_key,
            'player_game_stats_insert'
        );
        RETURN NEW;
    END IF;

    -- out-of-order historical upsert should not rewrite current open interval
    IF current_open.last_schedule_key IS NOT NULL
       AND NEW.schedule_key < current_open.last_schedule_key THEN
        RETURN NEW;
    END IF;

    IF current_open.team_id IS NOT DISTINCT FROM NEW.team_id
       AND current_open.jersey_number IS NOT DISTINCT FROM NEW.jersey_number THEN
        UPDATE player_affiliations
           SET last_schedule_key = GREATEST(COALESCE(last_schedule_key, NEW.schedule_key), NEW.schedule_key)
         WHERE affiliation_id = current_open.affiliation_id;
        RETURN NEW;
    END IF;

    UPDATE player_affiliations
       SET valid_to = event_at,
           last_schedule_key = GREATEST(COALESCE(last_schedule_key, NEW.schedule_key), NEW.schedule_key)
     WHERE affiliation_id = current_open.affiliation_id;

    INSERT INTO player_affiliations (
        player_id,
        team_id,
        jersey_number,
        valid_from,
        valid_to,
        first_schedule_key,
        last_schedule_key,
        detected_from
    )
    VALUES (
        NEW.player_id,
        NEW.team_id,
        NEW.jersey_number,
        event_at,
        NULL,
        NEW.schedule_key,
        NEW.schedule_key,
        'player_game_stats_transfer'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =========================
-- 4) Triggers
-- =========================

DROP TRIGGER IF EXISTS trg_track_team_name_history
    ON teams;

CREATE TRIGGER trg_track_team_name_history
AFTER INSERT OR UPDATE OF team_name_j, team_name_e, team_short_name_j, team_short_name_e
ON teams
FOR EACH ROW
EXECUTE FUNCTION track_team_name_history();


DROP TRIGGER IF EXISTS trg_track_player_name_history
    ON players;

CREATE TRIGGER trg_track_player_name_history
AFTER INSERT OR UPDATE OF player_name_j, player_name_e
ON players
FOR EACH ROW
EXECUTE FUNCTION track_player_name_history();


DROP TRIGGER IF EXISTS trg_track_player_affiliation
    ON player_game_stats;

CREATE TRIGGER trg_track_player_affiliation
AFTER INSERT OR UPDATE OF team_id, jersey_number
ON player_game_stats
FOR EACH ROW
EXECUTE FUNCTION track_player_affiliation_from_game_stats();


-- =========================
-- 5) Utility views
-- =========================

CREATE OR REPLACE VIEW v_teams_current AS
SELECT
    t.team_id,
    COALESCE(h.team_name_j, t.team_name_j) AS team_name_j,
    COALESCE(h.team_name_e, t.team_name_e) AS team_name_e,
    COALESCE(h.team_short_name_j, t.team_short_name_j) AS team_short_name_j,
    COALESCE(h.team_short_name_e, t.team_short_name_e) AS team_short_name_e,
    h.valid_from AS name_valid_from
FROM teams t
LEFT JOIN team_name_history h
       ON h.team_id = t.team_id
      AND h.valid_to IS NULL;


CREATE OR REPLACE VIEW v_players_current AS
SELECT
    p.player_id,
    COALESCE(h.player_name_j, p.player_name_j) AS player_name_j,
    COALESCE(h.player_name_e, p.player_name_e) AS player_name_e,
    a.team_id AS current_team_id,
    a.jersey_number AS current_jersey_number,
    a.valid_from AS affiliation_valid_from,
    h.valid_from AS name_valid_from
FROM players p
LEFT JOIN player_name_history h
       ON h.player_id = p.player_id
      AND h.valid_to IS NULL
LEFT JOIN player_affiliations a
       ON a.player_id = p.player_id
      AND a.valid_to IS NULL;


CREATE OR REPLACE VIEW v_player_transfer_events AS
SELECT
    a.player_id,
    p.player_name_j,
    LAG(a.team_id) OVER w AS from_team_id,
    a.team_id AS to_team_id,
    a.valid_from AS transferred_at,
    a.jersey_number
FROM player_affiliations a
JOIN players p ON p.player_id = a.player_id
WINDOW w AS (PARTITION BY a.player_id ORDER BY a.valid_from, a.affiliation_id);

-- END: 03_identity_history.sql

-- =====================================================================
-- BEGIN: 04_postcheck_identity_history.sql
-- =====================================================================
-- Post-check for migration 20260224_identity_history
-- Read-only queries

-- 1) created tables
SELECT
  table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('team_name_history', 'player_name_history', 'player_affiliations')
ORDER BY table_name;

-- 2) created views
SELECT
  table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('v_teams_current', 'v_players_current', 'v_player_transfer_events')
ORDER BY table_name;

-- 3) created triggers
SELECT
  trigger_name,
  event_object_table,
  action_timing,
  event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN (
    'trg_track_team_name_history',
    'trg_track_player_name_history',
    'trg_track_player_affiliation'
  )
ORDER BY trigger_name;

-- 4) backfill counts
SELECT 'team_name_history' AS table_name, COUNT(*) AS row_count FROM team_name_history
UNION ALL
SELECT 'player_name_history' AS table_name, COUNT(*) AS row_count FROM player_name_history
UNION ALL
SELECT 'player_affiliations' AS table_name, COUNT(*) AS row_count FROM player_affiliations;

-- 5) open rows sanity check (ideally one open row per entity)
SELECT team_id, COUNT(*) AS open_rows
FROM team_name_history
WHERE valid_to IS NULL
GROUP BY team_id
HAVING COUNT(*) > 1;

SELECT player_id, COUNT(*) AS open_rows
FROM player_name_history
WHERE valid_to IS NULL
GROUP BY player_id
HAVING COUNT(*) > 1;

SELECT player_id, COUNT(*) AS open_rows
FROM player_affiliations
WHERE valid_to IS NULL
GROUP BY player_id
HAVING COUNT(*) > 1;

-- 6) sample views
SELECT * FROM v_teams_current LIMIT 10;
SELECT * FROM v_players_current LIMIT 10;
SELECT *
FROM v_player_transfer_events
WHERE from_team_id IS NOT NULL
LIMIT 20;

-- END: 04_postcheck_identity_history.sql

-- =====================================================================
-- BEGIN: 05_batch_game_and_players_columns.sql
-- =====================================================================
-- 作成日: 2026-05-24
-- 目的: games / players の付加カラムを一括適用する（Step4,5,6,9 の統合）

-- games: 日時・日付・試合区分
ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_datetime TEXT;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_date TEXT;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS game_type TEXT;

-- players: 国籍
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS nationality TEXT;

-- 既存データがある場合のみ game_type をバックフィル
UPDATE games
SET game_type = CASE
    WHEN setu::integer <= 100 THEN 'RS'
    ELSE 'CS'
END
WHERE setu IS NOT NULL;

-- END: 05_batch_game_and_players_columns.sql

-- =====================================================================
-- BEGIN: 06_batch_player_identity.sql
-- =====================================================================
-- 作成日: 2026-05-24
-- 目的: player_id 変更追跡関連を一括適用する（Step7,8,11 の統合）

-- players: 旧ID保持カラム
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS old_player_id TEXT;

-- 旧 migration で player_id_aliases が残っている場合にのみリネーム
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'player_id_aliases'
    ) THEN
        EXECUTE 'ALTER TABLE player_id_aliases RENAME TO player_id_map';
    END IF;
END $$;

-- player_id_map が未作成なら作成
CREATE TABLE IF NOT EXISTS player_id_map (
    old_player_id TEXT PRIMARY KEY,
    player_id     TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    note          TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_id_map_player_id
    ON player_id_map(player_id);

-- 旧列名があるケースを新列へ統一
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'player_id_map'
          AND column_name = 'alias_id'
    ) THEN
        EXECUTE 'ALTER TABLE player_id_map RENAME COLUMN alias_id TO old_player_id';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'player_id_map'
          AND column_name = 'canonical_player_id'
    ) THEN
        EXECUTE 'ALTER TABLE player_id_map RENAME COLUMN canonical_player_id TO player_id';
    END IF;
END $$;

-- players.player_id 更新時に関連テーブルへ連鎖するよう FK を再定義
ALTER TABLE player_game_stats
    DROP CONSTRAINT IF EXISTS player_game_stats_player_id_fkey,
    ADD CONSTRAINT player_game_stats_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE player_name_history
    DROP CONSTRAINT IF EXISTS player_name_history_player_id_fkey,
    ADD CONSTRAINT player_name_history_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE player_affiliations
    DROP CONSTRAINT IF EXISTS player_affiliations_player_id_fkey,
    ADD CONSTRAINT player_affiliations_player_id_fkey
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE CASCADE;

-- END: 06_batch_player_identity.sql

-- =====================================================================
-- BEGIN: 07_fix_affiliation_trigger.sql
-- =====================================================================
-- トリガー関数 track_player_affiliation_from_game_stats の修正
--
-- 問題: 過去データを時系列と逆順（例：2月→3月→1月）でUPSERTすると、
--       既存の affiliation (valid_from=3月) に valid_to=1月 をセットしようとして
--       CHECK制約 (valid_to > valid_from) に違反する。
--
-- 修正: event_at が現在オープンな affiliation の valid_from 以前であれば
--       スキップする（out-of-order historical upsert ガード）。

CREATE OR REPLACE FUNCTION track_player_affiliation_from_game_stats()
RETURNS TRIGGER AS $$
DECLARE
    current_open RECORD;
    event_at TIMESTAMPTZ;
BEGIN
    SELECT TO_TIMESTAMP(g.game_datetime_unix)
      INTO event_at
      FROM games g
     WHERE g.schedule_key = NEW.schedule_key;

    IF event_at IS NULL THEN
        event_at := NOW();
    END IF;

    SELECT *
      INTO current_open
      FROM player_affiliations a
     WHERE a.player_id = NEW.player_id
       AND a.valid_to IS NULL
     ORDER BY a.valid_from DESC, a.affiliation_id DESC
     LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO player_affiliations (
            player_id,
            team_id,
            jersey_number,
            valid_from,
            valid_to,
            first_schedule_key,
            last_schedule_key,
            detected_from
        )
        VALUES (
            NEW.player_id,
            NEW.team_id,
            NEW.jersey_number,
            event_at,
            NULL,
            NEW.schedule_key,
            NEW.schedule_key,
            'player_game_stats_insert'
        );
        RETURN NEW;
    END IF;

    -- out-of-order historical upsert: event が現在オープンな interval の開始以前なら無視する
    -- （valid_to < valid_from の制約違反を防ぐ）
    IF event_at <= current_open.valid_from THEN
        RETURN NEW;
    END IF;

    -- schedule_key ベースの追加ガード（同一 interval 内の旧イベント）
    IF current_open.last_schedule_key IS NOT NULL
       AND NEW.schedule_key < current_open.last_schedule_key THEN
        RETURN NEW;
    END IF;

    IF current_open.team_id IS NOT DISTINCT FROM NEW.team_id
       AND current_open.jersey_number IS NOT DISTINCT FROM NEW.jersey_number THEN
        UPDATE player_affiliations
           SET last_schedule_key = GREATEST(COALESCE(last_schedule_key, NEW.schedule_key), NEW.schedule_key)
         WHERE affiliation_id = current_open.affiliation_id;
        RETURN NEW;
    END IF;

    UPDATE player_affiliations
       SET valid_to = event_at,
           last_schedule_key = GREATEST(COALESCE(last_schedule_key, NEW.schedule_key), NEW.schedule_key)
     WHERE affiliation_id = current_open.affiliation_id;

    INSERT INTO player_affiliations (
        player_id,
        team_id,
        jersey_number,
        valid_from,
        valid_to,
        first_schedule_key,
        last_schedule_key,
        detected_from
    )
    VALUES (
        NEW.player_id,
        NEW.team_id,
        NEW.jersey_number,
        event_at,
        NULL,
        NEW.schedule_key,
        NEW.schedule_key,
        'player_game_stats_transfer'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- END: 07_fix_affiliation_trigger.sql

