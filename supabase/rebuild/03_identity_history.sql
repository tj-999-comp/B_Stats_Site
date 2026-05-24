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
);


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
