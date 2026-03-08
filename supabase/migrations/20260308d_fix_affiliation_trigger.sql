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
