# テーブル定義書（Supabase 現在値）

このドキュメントは Supabase REST OpenAPI（`Accept: application/openapi+json`）から自動生成したスナップショットです。

- 取得日時 (UTC): 2026-02-24T08:12:41.632Z
- 取得元: https://mngqmfvsxcqjhsgkbyju.supabase.co/rest/v1/

## テーブル一覧

- `game_team_stats`
- `games`
- `player_affiliations`
- `player_game_stats`
- `player_name_history`
- `players`
- `team_name_history`
- `teams`
- `v_player_transfer_events`
- `v_players_current`
- `v_teams_current`

## game_team_stats

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `schedule_key` | 試合ID | `bigint` | Yes | `-` | PK, FK -> games.schedule_key |
| `team_id` | チームID | `text` | Yes | `-` | PK, FK -> teams.team_id |
| `opponent_team_id` | 対戦相手チームID | `text` | No | `-` | FK -> teams.team_id |
| `is_home` | ホームフラグ | `boolean` | Yes | `-` | - |
| `points` | 得点 | `integer` | No | `-` | - |
| `fgm` | FG成功数 | `integer` | No | `-` | - |
| `fga` | FG試投数 | `integer` | No | `-` | - |
| `fg_pct` | FG成功率 | `numeric` | No | `-` | - |
| `fg2m` | 2P成功数 | `integer` | No | `-` | - |
| `fg2a` | 2P試投数 | `integer` | No | `-` | - |
| `fg2_pct` | 2P成功率 | `numeric` | No | `-` | - |
| `fg3m` | 3P成功数 | `integer` | No | `-` | - |
| `fg3a` | 3P試投数 | `integer` | No | `-` | - |
| `fg3_pct` | 3P成功率 | `numeric` | No | `-` | - |
| `ftm` | FT成功数 | `integer` | No | `-` | - |
| `fta` | FT試投数 | `integer` | No | `-` | - |
| `ft_pct` | FT成功率 | `numeric` | No | `-` | - |
| `off_rebounds` | オフェンスリバウンド | `integer` | No | `-` | - |
| `def_rebounds` | ディフェンスリバウンド | `integer` | No | `-` | - |
| `total_rebounds` | 総リバウンド | `integer` | No | `-` | - |
| `assists` | アシスト | `integer` | No | `-` | - |
| `steals` | スティール | `integer` | No | `-` | - |
| `blocks` | ブロック | `integer` | No | `-` | - |
| `blocks_received` | 被ブロック | `integer` | No | `-` | - |
| `turnovers` | ターンオーバー | `integer` | No | `-` | - |
| `fouls` | ファウル | `integer` | No | `-` | - |
| `fouls_drawn` | 被ファウル | `integer` | No | `-` | - |
| `dunks` | ダンク | `integer` | No | `-` | - |
| `fast_break_points` | 速攻得点 | `integer` | No | `-` | - |
| `second_chance_points` | セカンドチャンス得点 | `integer` | No | `-` | - |
| `points_in_paint` | ペイント内得点 | `integer` | No | `-` | - |
| `possession` | ポゼッション | `numeric` | No | `-` | - |
| `pace` | ペース | `numeric` | No | `-` | - |
| `off_rtg` | オフェンスレーティング | `numeric` | No | `-` | - |
| `def_rtg` | ディフェンスレーティング | `numeric` | No | `-` | - |
| `net_rtg` | ネットレーティング | `numeric` | No | `-` | - |
| `ast_rtg` | アシストレーティング | `numeric` | No | `-` | - |
| `tov_rtg` | ターンオーバーレーティング | `numeric` | No | `-` | - |
| `pft_rtg` | PFTレーティング | `numeric` | No | `-` | - |
| `scp_rtg` | SCPレーティング | `numeric` | No | `-` | - |
| `efg_pct` | eFG% | `numeric` | No | `-` | - |
| `ts_pct` | TS% | `numeric` | No | `-` | - |
| `ast_pct` | アシスト率 | `numeric` | No | `-` | - |
| `tov_pct` | ターンオーバー率 | `numeric` | No | `-` | - |
| `ast_tov_ratio` | AST/TOV比 | `numeric` | No | `-` | - |
| `play_pct` | プレー成功率 | `numeric` | No | `-` | - |
| `ft_d_pct` | FT獲得率 | `numeric` | No | `-` | - |
| `ft_freq` | FT頻度 | `numeric` | No | `-` | - |
| `ft_rate` | FTレート | `numeric` | No | `-` | - |
| `orb_pct` | ORB% | `numeric` | No | `-` | - |
| `drb_pct` | DRB% | `numeric` | No | `-` | - |
| `pft_pct` | PFT% | `numeric` | No | `-` | - |
| `fbp_pct` | FBP% | `numeric` | No | `-` | - |
| `scp_pct` | SCP% | `numeric` | No | `-` | - |
| `pitp_pct` | PITP% | `numeric` | No | `-` | - |
| `perimeter_pts_pct` | ペリメータ得点率 | `numeric` | No | `-` | - |
| `pt2_attempt_pct` | 2P試投率 | `numeric` | No | `-` | - |
| `pt3_attempt_pct` | 3P試投率 | `numeric` | No | `-` | - |
| `pt2_points_share` | 2P得点シェア | `numeric` | No | `-` | - |
| `pt3_points_share` | 3P得点シェア | `numeric` | No | `-` | - |
| `ft_points_share` | FT得点シェア | `numeric` | No | `-` | - |
| `live_tov_pct` | ライブボールTO率 | `numeric` | No | `-` | - |
| `dead_tov_pct` | デッドボールTO率 | `numeric` | No | `-` | - |
| `live_tov_share` | ライブボールTOシェア | `numeric` | No | `-` | - |
| `dead_tov_share` | デッドボールTOシェア | `numeric` | No | `-` | - |
| `shot_chances` | シュートチャンス数 | `numeric` | No | `-` | - |
| `off_success_count` | オフェンス成功数 | `numeric` | No | `-` | - |
| `or_chances` | ORチャンス数 | `numeric` | No | `-` | - |
| `dr_chances` | DRチャンス数 | `numeric` | No | `-` | - |
| `tom` | TOM | `numeric` | No | `-` | - |
| `eff` | EFF | `numeric` | No | `-` | - |
| `vps` | VPS | `numeric` | No | `-` | - |
| `home_efg_pct` | ホームEFG率 | `numeric` | No | `-` | - |
| `away_efg_pct` | アウェーEFG率 | `numeric` | No | `-` | - |
| `home_ts_pct` | ホームTS率 | `numeric` | No | `-` | - |
| `away_ts_pct` | アウェーTS率 | `numeric` | No | `-` | - |
| `home_off_rtg` | ホームオフェンスレーティング | `numeric` | No | `-` | - |
| `away_off_rtg` | アウェーオフェンスレーティング | `numeric` | No | `-` | - |
| `close_win_3pts_or_less` | 接戦勝利（3点差以内） | `integer` | No | `-` | - |
| `close_loss_3pts_or_less` | 接戦敗戦（3点差以内） | `integer` | No | `-` | - |
| `pythagorean_win_pct` | ピタゴラス勝率 | `numeric` | No | `-` | - |
| `opp_possession` | 相手ポゼッション | `numeric` | No | `-` | - |
| `opp_efg_pct` | 相手EFG率 | `numeric` | No | `-` | - |
| `opp_ts_pct` | 相手TS率 | `numeric` | No | `-` | - |
| `opp_fg2_pct` | 相手2P率 | `numeric` | No | `-` | - |
| `opp_fg3_pct` | 相手3P率 | `numeric` | No | `-` | - |
| `opp_pt2_attempt_pct` | 相手2P試投率 | `numeric` | No | `-` | - |
| `opp_pt3_attempt_pct` | 相手3P試投率 | `numeric` | No | `-` | - |
| `opp_pt2_points_share` | 相手2P得点シェア | `numeric` | No | `-` | - |
| `opp_pt3_points_share` | 相手3P得点シェア | `numeric` | No | `-` | - |
| `opp_ft_points_share` | 相手FT得点シェア | `numeric` | No | `-` | - |
| `opp_ast_pct` | 相手アシスト率 | `numeric` | No | `-` | - |
| `opp_ast_tov_ratio` | 相手AST/TOV比 | `numeric` | No | `-` | - |
| `opp_ast_rtg` | 相手アシストレーティング | `numeric` | No | `-` | - |
| `opp_tov_pct` | 相手ターンオーバー率 | `numeric` | No | `-` | - |
| `opp_orb_pct` | 相手ORB率 | `numeric` | No | `-` | - |
| `opp_drb_pct` | 相手DRB率 | `numeric` | No | `-` | - |
| `opp_shot_chances` | 相手シュートチャンス数 | `numeric` | No | `-` | - |
| `opp_success_count` | 相手成功数 | `numeric` | No | `-` | - |
| `opp_ft_d_pct` | 相手FT獲得率 | `numeric` | No | `-` | - |
| `opp_ft_rate` | 相手FTレート | `numeric` | No | `-` | - |
| `opp_fbp_pct` | 相手FBP率 | `numeric` | No | `-` | - |
| `opp_scp_pct` | 相手SCP率 | `numeric` | No | `-` | - |
| `opp_scp_rtg` | 相手SCPレーティング | `numeric` | No | `-` | - |
| `opp_pitp_pct` | 相手PITP率 | `numeric` | No | `-` | - |
| `opp_perimeter_pts_pct` | 相手外角得点率 | `numeric` | No | `-` | - |
| `opp_pft_pct` | 相手PFT率 | `numeric` | No | `-` | - |
| `opp_pft_rtg` | 相手PFTレーティング | `numeric` | No | `-` | - |
| `opp_vps` | 相手VPS | `numeric` | No | `-` | - |
| `home_opp_efg_pct` | ホーム相手EFG率 | `numeric` | No | `-` | - |
| `away_opp_efg_pct` | アウェー相手EFG率 | `numeric` | No | `-` | - |
| `home_opp_ts_pct` | ホーム相手TS率 | `numeric` | No | `-` | - |
| `away_opp_ts_pct` | アウェー相手TS率 | `numeric` | No | `-` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |
| `updated_at` | 更新日時 | `timestamp with time zone` | Yes | `now()` | - |

## games

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `schedule_key` | 試合ID | `bigint` | Yes | `-` | PK |
| `season` | シーズン | `text` | Yes | `-` | - |
| `code` | コード | `integer` | Yes | `-` | - |
| `convention_key` | 大会ID | `text` | Yes | `-` | - |
| `convention_name_j` | 大会名（日本語） | `text` | Yes | `-` | - |
| `convention_name_e` | 大会名（英語） | `text` | No | `-` | - |
| `year` | 年 | `integer` | Yes | `-` | - |
| `setu` | 節 | `text` | No | `-` | - |
| `max_period` | 最大クォーター数 | `smallint` | Yes | `-` | - |
| `game_current_period` | 現在クォーター | `smallint` | No | `-` | - |
| `game_datetime_unix` | 試合日時UNIX | `bigint` | Yes | `-` | - |
| `stadium_cd` | 会場コード | `text` | No | `-` | - |
| `stadium_name_j` | 会場名（日本語） | `text` | No | `-` | - |
| `stadium_name_e` | 会場名（英語） | `text` | No | `-` | - |
| `attendance` | 観客数 | `integer` | No | `-` | - |
| `game_ended_flg` | 試合終了フラグ | `boolean` | Yes | `false` | - |
| `record_fixed_flg` | 記録確定フラグ | `boolean` | Yes | `false` | - |
| `boxscore_exists_flg` | ボックススコア有無フラグ | `boolean` | Yes | `false` | - |
| `play_by_play_exists_flg` | プレー詳細有無フラグ | `boolean` | Yes | `false` | - |
| `home_team_id` | ホームチームID | `text` | Yes | `-` | FK -> teams.team_id |
| `away_team_id` | アウェーチームID | `text` | Yes | `-` | FK -> teams.team_id |
| `home_team_score_q1` | ホームチーム得点Q1 | `smallint` | No | `-` | - |
| `home_team_score_q2` | ホームチーム得点Q2 | `smallint` | No | `-` | - |
| `home_team_score_q3` | ホームチーム得点Q3 | `smallint` | No | `-` | - |
| `home_team_score_q4` | ホームチーム得点Q4 | `smallint` | No | `-` | - |
| `home_team_score_q5` | ホームチーム得点Q5 | `smallint` | No | `-` | - |
| `home_team_score_total` | ホームチーム得点合計 | `smallint` | No | `-` | - |
| `away_team_score_q1` | アウェーチーム得点Q1 | `smallint` | No | `-` | - |
| `away_team_score_q2` | アウェーチーム得点Q2 | `smallint` | No | `-` | - |
| `away_team_score_q3` | アウェーチーム得点Q3 | `smallint` | No | `-` | - |
| `away_team_score_q4` | アウェーチーム得点Q4 | `smallint` | No | `-` | - |
| `away_team_score_q5` | アウェーチーム得点Q5 | `smallint` | No | `-` | - |
| `away_team_score_total` | アウェーチーム得点合計 | `smallint` | No | `-` | - |
| `referee_id` | 主審ID | `bigint` | No | `-` | - |
| `referee_name_j` | 主審名（日本語） | `text` | No | `-` | - |
| `sub_referee_id_1` | 副審1ID | `bigint` | No | `-` | - |
| `sub_referee_name_j_1` | 副審1名（日本語） | `text` | No | `-` | - |
| `sub_referee_id_2` | 副審2ID | `bigint` | No | `-` | - |
| `sub_referee_name_j_2` | 副審2名（日本語） | `text` | No | `-` | - |
| `source_tab` | ソースタブ | `smallint` | No | `-` | - |
| `scraped_at` | 取得日時 | `timestamp with time zone` | Yes | `now()` | - |
| `updated_at` | 更新日時 | `timestamp with time zone` | Yes | `now()` | - |

## player_affiliations

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `affiliation_id` | AFFILIATIONID | `bigint` | Yes | `-` | PK |
| `player_id` | 選手ID | `text` | Yes | `-` | FK -> players.player_id |
| `team_id` | チームID | `text` | Yes | `-` | FK -> teams.team_id |
| `jersey_number` | 背番号 | `text` | No | `-` | - |
| `valid_from` | VALIDFROM | `timestamp with time zone` | Yes | `now()` | - |
| `valid_to` | VALIDTO | `timestamp with time zone` | No | `-` | - |
| `first_schedule_key` | FIRSTSCHEDULEKEY | `bigint` | No | `-` | FK -> games.schedule_key |
| `last_schedule_key` | LASTSCHEDULEKEY | `bigint` | No | `-` | FK -> games.schedule_key |
| `detected_from` | DETECTEDFROM | `text` | Yes | `game_feed` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |

## player_game_stats

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `schedule_key` | 試合ID | `bigint` | Yes | `-` | PK, FK -> games.schedule_key |
| `player_id` | 選手ID | `text` | Yes | `-` | PK, FK -> players.player_id |
| `team_id` | チームID | `text` | Yes | `-` | FK -> teams.team_id |
| `jersey_number` | 背番号 | `text` | No | `-` | - |
| `is_starter` | 先発フラグ | `boolean` | Yes | `false` | - |
| `is_playing` | 出場フラグ | `boolean` | Yes | `false` | - |
| `play_time` | 出場時間 | `text` | No | `-` | - |
| `points` | 得点 | `integer` | No | `-` | - |
| `fgm` | FG成功数 | `integer` | No | `-` | - |
| `fga` | FG試投数 | `integer` | No | `-` | - |
| `fg_pct` | FG成功率 | `numeric` | No | `-` | - |
| `fg2m` | 2P成功数 | `integer` | No | `-` | - |
| `fg2a` | 2P試投数 | `integer` | No | `-` | - |
| `fg2_pct` | 2P成功率 | `numeric` | No | `-` | - |
| `fg3m` | 3P成功数 | `integer` | No | `-` | - |
| `fg3a` | 3P試投数 | `integer` | No | `-` | - |
| `fg3_pct` | 3P成功率 | `numeric` | No | `-` | - |
| `ftm` | FT成功数 | `integer` | No | `-` | - |
| `fta` | FT試投数 | `integer` | No | `-` | - |
| `ft_pct` | FT成功率 | `numeric` | No | `-` | - |
| `off_rebounds` | オフェンスリバウンド | `integer` | No | `-` | - |
| `def_rebounds` | ディフェンスリバウンド | `integer` | No | `-` | - |
| `total_rebounds` | 総リバウンド | `integer` | No | `-` | - |
| `assists` | アシスト | `integer` | No | `-` | - |
| `turnovers` | ターンオーバー | `integer` | No | `-` | - |
| `steals` | スティール | `integer` | No | `-` | - |
| `blocks` | ブロック | `integer` | No | `-` | - |
| `blocks_received` | 被ブロック | `integer` | No | `-` | - |
| `fouls` | ファウル | `integer` | No | `-` | - |
| `fouls_drawn` | 被ファウル | `integer` | No | `-` | - |
| `fast_break_points` | 速攻得点 | `integer` | No | `-` | - |
| `points_in_paint` | ペイント内得点 | `integer` | No | `-` | - |
| `second_chance_points` | セカンドチャンス得点 | `integer` | No | `-` | - |
| `efficiency` | 効率値 | `integer` | No | `-` | - |
| `plus_minus` | プラスマイナス | `integer` | No | `-` | - |
| `ast_to_ratio` | AST/TO比 | `numeric` | No | `-` | - |
| `efg_pct` | eFG% | `numeric` | No | `-` | - |
| `ts_pct` | TS% | `numeric` | No | `-` | - |
| `usg_pct` | USG% | `numeric` | No | `-` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |
| `updated_at` | 更新日時 | `timestamp with time zone` | Yes | `now()` | - |

## player_name_history

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `history_id` | HISTORYID | `bigint` | Yes | `-` | PK |
| `player_id` | 選手ID | `text` | Yes | `-` | FK -> players.player_id |
| `player_name_j` | 選手名（日本語） | `text` | Yes | `-` | - |
| `player_name_e` | 選手名（英語） | `text` | No | `-` | - |
| `valid_from` | VALIDFROM | `timestamp with time zone` | Yes | `now()` | - |
| `valid_to` | VALIDTO | `timestamp with time zone` | No | `-` | - |
| `detected_from` | DETECTEDFROM | `text` | Yes | `system` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |

## players

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `player_id` | 選手ID | `text` | Yes | `-` | PK |
| `player_name_j` | 選手名（日本語） | `text` | Yes | `-` | - |
| `player_name_e` | 選手名（英語） | `text` | No | `-` | - |
| `last_seen_team_id` | 最終所属チームID | `text` | No | `-` | FK -> teams.team_id |
| `last_seen_jersey_number` | 最終背番号 | `text` | No | `-` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |
| `updated_at` | 更新日時 | `timestamp with time zone` | Yes | `now()` | - |

## team_name_history

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `history_id` | HISTORYID | `bigint` | Yes | `-` | PK |
| `team_id` | チームID | `text` | Yes | `-` | FK -> teams.team_id |
| `team_name_j` | チーム名（日本語） | `text` | Yes | `-` | - |
| `team_name_e` | チーム名（英語） | `text` | No | `-` | - |
| `team_short_name_j` | チーム略称（日本語） | `text` | No | `-` | - |
| `team_short_name_e` | チーム略称（英語） | `text` | No | `-` | - |
| `valid_from` | VALIDFROM | `timestamp with time zone` | Yes | `now()` | - |
| `valid_to` | VALIDTO | `timestamp with time zone` | No | `-` | - |
| `detected_from` | DETECTEDFROM | `text` | Yes | `system` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |

## teams

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `team_id` | チームID | `text` | Yes | `-` | PK |
| `team_name_j` | チーム名（日本語） | `text` | Yes | `-` | - |
| `team_name_e` | チーム名（英語） | `text` | No | `-` | - |
| `team_short_name_j` | チーム略称（日本語） | `text` | No | `-` | - |
| `team_short_name_e` | チーム略称（英語） | `text` | No | `-` | - |
| `created_at` | 作成日時 | `timestamp with time zone` | Yes | `now()` | - |
| `updated_at` | 更新日時 | `timestamp with time zone` | Yes | `now()` | - |

## v_player_transfer_events

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `player_id` | 選手ID | `text` | No | `-` | FK -> players.player_id |
| `player_name_j` | 選手名（日本語） | `text` | No | `-` | - |
| `from_team_id` | FROMチームID | `text` | No | `-` | - |
| `to_team_id` | TOチームID | `text` | No | `-` | FK -> teams.team_id |
| `transferred_at` | TRANSFERREDAT | `timestamp with time zone` | No | `-` | - |
| `jersey_number` | 背番号 | `text` | No | `-` | - |

## v_players_current

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `player_id` | 選手ID | `text` | No | `-` | PK |
| `player_name_j` | 選手名（日本語） | `text` | No | `-` | - |
| `player_name_e` | 選手名（英語） | `text` | No | `-` | - |
| `current_team_id` | CURRENTチームID | `text` | No | `-` | FK -> teams.team_id |
| `current_jersey_number` | CURRENTJERSEYNUMBER | `text` | No | `-` | - |
| `affiliation_valid_from` | AFFILIATIONVALIDFROM | `timestamp with time zone` | No | `-` | - |
| `name_valid_from` | 名VALIDFROM | `timestamp with time zone` | No | `-` | - |

## v_teams_current

| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |
|---|---|---|---|---|---|
| `team_id` | チームID | `text` | No | `-` | PK |
| `team_name_j` | チーム名（日本語） | `text` | No | `-` | - |
| `team_name_e` | チーム名（英語） | `text` | No | `-` | - |
| `team_short_name_j` | チーム略称（日本語） | `text` | No | `-` | - |
| `team_short_name_e` | チーム略称（英語） | `text` | No | `-` | - |
| `name_valid_from` | 名VALIDFROM | `timestamp with time zone` | No | `-` | - |
