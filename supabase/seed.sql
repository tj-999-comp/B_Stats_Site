-- シードデータ（開発・テスト用）

INSERT INTO player_stats (season, player_name, team_name, games_played, points, rebounds, assists, steals, blocks)
VALUES
    ('2024-25', 'サンプル選手A', 'サンプルチーム1', 30, 20.5, 5.3, 3.2, 1.5, 0.3),
    ('2024-25', 'サンプル選手B', 'サンプルチーム2', 28, 18.2, 8.1, 2.0, 1.2, 1.5)
ON CONFLICT (season, player_name, team_name) DO NOTHING;

INSERT INTO team_stats (season, team_name, wins, losses, win_rate)
VALUES
    ('2024-25', 'サンプルチーム1', 25, 5, 0.833),
    ('2024-25', 'サンプルチーム2', 20, 10, 0.667)
ON CONFLICT (season, team_name) DO NOTHING;

INSERT INTO rankings (season, rank, team_name, conference)
VALUES
    ('2024-25', 1, 'サンプルチーム1', '中地区'),
    ('2024-25', 2, 'サンプルチーム2', '中地区')
ON CONFLICT (season, conference, rank) DO NOTHING;
