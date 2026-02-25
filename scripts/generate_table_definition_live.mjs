import fs from 'fs';
import path from 'path';

const rootDir = process.cwd();
const envPath = path.join(rootDir, '.env.local');

if (!fs.existsSync(envPath)) {
  throw new Error('.env.local が見つかりません。');
}

const envRaw = fs.readFileSync(envPath, 'utf8');
const env = Object.fromEntries(
  envRaw
    .split('\n')
    .filter((line) => line && !line.trim().startsWith('#') && line.includes('='))
    .map((line) => {
      const idx = line.indexOf('=');
      return [line.slice(0, idx), line.slice(idx + 1)];
    }),
);

const dashboardUrl = env.NEXT_PUBLIC_SUPABASE_URL || '';
const serviceKey = env.SUPABASE_SECRET_KEY || env.SUPABASE_SECRET_KEYS || '';

const projectRefMatch = dashboardUrl.match(/project\/([^/]+)/);
const projectRef = projectRefMatch?.[1] ?? '';

if (!projectRef) {
  throw new Error('NEXT_PUBLIC_SUPABASE_URL から project ref を取得できません。');
}

if (!serviceKey) {
  throw new Error('SUPABASE_SECRET_KEY または SUPABASE_SECRET_KEYS が設定されていません。');
}

const endpoint = `https://${projectRef}.supabase.co/rest/v1/`;

const response = await fetch(endpoint, {
  headers: {
    apikey: serviceKey,
    Authorization: `Bearer ${serviceKey}`,
    Accept: 'application/openapi+json',
  },
});

if (!response.ok) {
  throw new Error(`OpenAPI取得失敗: ${response.status} ${response.statusText}`);
}

const openapi = await response.json();
const defs = openapi.definitions || {};
const tables = Object.keys(defs).sort();

const parseConstraint = (desc = '') => {
  const flags = [];
  if (desc.includes('<pk/>')) flags.push('PK');
  const fkMatches = [...desc.matchAll(/<fk table='([^']+)' column='([^']+)'\/>/g)];
  for (const match of fkMatches) {
    flags.push(`FK -> ${match[1]}.${match[2]}`);
  }
  return flags.length ? flags.join(', ') : '-';
};

const exactJapaneseNameMap = {
  schedule_key: '試合ID',
  game_date: '試合日',
  game_datetime: '試合日時',
  game_datetime_unix: '試合日時UNIX',
  game_ended_flg: '試合終了フラグ',
  game_current_period: '現在クォーター',
  max_period: '最大クォーター数',
  record_fixed_flg: '記録確定フラグ',
  boxscore_exists_flg: 'ボックススコア有無フラグ',
  play_by_play_exists_flg: 'プレー詳細有無フラグ',
  season: 'シーズン',
  year: '年',
  code: 'コード',
  setu: '節',
  convention_key: '大会ID',
  convention_name_j: '大会名（日本語）',
  convention_name_e: '大会名（英語）',
  section_name_j: 'セクション名（日本語）',
  section_name_e: 'セクション名（英語）',
  venue_name_j: '会場名（日本語）',
  venue_name_e: '会場名（英語）',
  home_team_id: 'ホームチームID',
  away_team_id: 'アウェーチームID',
  home_team_name_j: 'ホームチーム名（日本語）',
  away_team_name_j: 'アウェーチーム名（日本語）',
  home_score: 'ホーム得点',
  away_score: 'アウェー得点',
  attendance: '観客数',
  player_id: '選手ID',
  player_name_j: '選手名（日本語）',
  player_name_e: '選手名（英語）',
  team_id: 'チームID',
  team_name_j: 'チーム名（日本語）',
  team_name_e: 'チーム名（英語）',
  team_short_name_j: 'チーム略称（日本語）',
  team_short_name_e: 'チーム略称（英語）',
  opponent_team_id: '対戦相手チームID',
  jersey_number: '背番号',
  last_seen_team_id: '最終所属チームID',
  last_seen_jersey_number: '最終背番号',
  is_home: 'ホームフラグ',
  is_starter: '先発フラグ',
  is_playing: '出場フラグ',
  points: '得点',
  play_time: '出場時間',
  fgm: 'FG成功数',
  fga: 'FG試投数',
  fg_pct: 'FG成功率',
  fg2m: '2P成功数',
  fg2a: '2P試投数',
  fg2_pct: '2P成功率',
  fg3m: '3P成功数',
  fg3a: '3P試投数',
  fg3_pct: '3P成功率',
  ftm: 'FT成功数',
  fta: 'FT試投数',
  ft_pct: 'FT成功率',
  off_rebounds: 'オフェンスリバウンド',
  def_rebounds: 'ディフェンスリバウンド',
  total_rebounds: '総リバウンド',
  assists: 'アシスト',
  steals: 'スティール',
  blocks: 'ブロック',
  blocks_received: '被ブロック',
  turnovers: 'ターンオーバー',
  fouls: 'ファウル',
  fouls_drawn: '被ファウル',
  dunks: 'ダンク',
  fast_break_points: '速攻得点',
  second_chance_points: 'セカンドチャンス得点',
  points_in_paint: 'ペイント内得点',
  possession: 'ポゼッション',
  pace: 'ペース',
  off_rtg: 'オフェンスレーティング',
  def_rtg: 'ディフェンスレーティング',
  net_rtg: 'ネットレーティング',
  ast_rtg: 'アシストレーティング',
  tov_rtg: 'ターンオーバーレーティング',
  pft_rtg: 'PFTレーティング',
  scp_rtg: 'SCPレーティング',
  efg_pct: 'eFG%',
  ts_pct: 'TS%',
  ast_pct: 'アシスト率',
  tov_pct: 'ターンオーバー率',
  ast_tov_ratio: 'AST/TOV比',
  ast_to_ratio: 'AST/TO比',
  play_pct: 'プレー成功率',
  ft_d_pct: 'FT獲得率',
  ft_freq: 'FT頻度',
  ft_rate: 'FTレート',
  orb_pct: 'ORB%',
  drb_pct: 'DRB%',
  pft_pct: 'PFT%',
  fbp_pct: 'FBP%',
  scp_pct: 'SCP%',
  pitp_pct: 'PITP%',
  perimeter_pts_pct: 'ペリメータ得点率',
  pt2_attempt_pct: '2P試投率',
  pt3_attempt_pct: '3P試投率',
  pt2_points_share: '2P得点シェア',
  pt3_points_share: '3P得点シェア',
  ft_points_share: 'FT得点シェア',
  live_tov_pct: 'ライブボールTO率',
  dead_tov_pct: 'デッドボールTO率',
  live_tov_share: 'ライブボールTOシェア',
  dead_tov_share: 'デッドボールTOシェア',
  shot_chances: 'シュートチャンス数',
  off_success_count: 'オフェンス成功数',
  or_chances: 'ORチャンス数',
  dr_chances: 'DRチャンス数',
  tom: 'TOM',
  eff: 'EFF',
  vps: 'VPS',
  pythagorean_win_pct: 'ピタゴラス勝率',
  close_win_3pts_or_less: '接戦勝利（3点差以内）',
  close_loss_3pts_or_less: '接戦敗戦（3点差以内）',
  opp_possession: '相手ポゼッション',
  opp_ast_tov_ratio: '相手AST/TOV比',
  opp_shot_chances: '相手シュートチャンス数',
  opp_success_count: '相手成功数',
  opp_ft_d_pct: '相手FT獲得率',
  opp_ft_rate: '相手FTレート',
  opp_perimeter_pts_pct: '相手外角得点率',
  efficiency: '効率値',
  plus_minus: 'プラスマイナス',
  usg_pct: 'USG%',
  stadium_cd: '会場コード',
  stadium_name_j: '会場名（日本語）',
  stadium_name_e: '会場名（英語）',
  referee_id: '主審ID',
  referee_name_j: '主審名（日本語）',
  sub_referee_id_1: '副審1ID',
  sub_referee_name_j_1: '副審1名（日本語）',
  sub_referee_id_2: '副審2ID',
  sub_referee_name_j_2: '副審2名（日本語）',
  source_tab: 'ソースタブ',
  scraped_at: '取得日時',
  created_at: '作成日時',
  updated_at: '更新日時',
};

const tokenJapaneseMap = {
  opp: '相手',
  home: 'ホーム',
  away: 'アウェー',
  off: 'オフェンス',
  def: 'ディフェンス',
  net: 'ネット',
  ast: 'アシスト',
  tov: 'ターンオーバー',
  pct: '率',
  rtg: 'レーティング',
  share: 'シェア',
  points: '得点',
  score: '得点',
  q1: 'Q1',
  q2: 'Q2',
  q3: 'Q3',
  q4: 'Q4',
  q5: 'Q5',
  total: '合計',
  attempt: '試投',
  attempts: '試投',
  ratio: '比',
  success: '成功',
  count: '数',
  perimeter: '外角',
  pts: '得点',
  stadium: '会場',
  cd: 'コード',
  referee: '審判',
  sub: '副',
  name: '名',
  id: 'ID',
  source: 'ソース',
  tab: 'タブ',
  to: 'TO',
  plus: 'プラス',
  minus: 'マイナス',
  team: 'チーム',
  possession: 'ポゼッション',
  shot: 'シュート',
  ftd: 'FT獲得',
  rate: 'レート',
  rebounds: 'リバウンド',
  chance: 'チャンス',
  chances: 'チャンス',
  live: 'ライブ',
  dead: 'デッド',
  ft: 'FT',
  fg: 'FG',
  fg2: '2P',
  fg3: '3P',
  pt2: '2P',
  pt3: '3P',
};

const toJapaneseColumnName = (column) => {
  if (exactJapaneseNameMap[column]) {
    return exactJapaneseNameMap[column];
  }

  const segments = column.split('_');
  const translated = segments.map((segment) => tokenJapaneseMap[segment] || segment.toUpperCase());
  return translated.join('');
};

const lines = [];
lines.push('# テーブル定義書（Supabase 現在値）');
lines.push('');
lines.push('このドキュメントは Supabase REST OpenAPI（`Accept: application/openapi+json`）から自動生成したスナップショットです。');
lines.push('');
lines.push(`- 取得日時 (UTC): ${new Date().toISOString()}`);
lines.push(`- 取得元: ${endpoint}`);
lines.push('');
lines.push('## テーブル一覧');
lines.push('');
for (const table of tables) {
  lines.push(`- \`${table}\``);
}

for (const table of tables) {
  const def = defs[table] || {};
  const required = new Set(def.required || []);
  const props = def.properties || {};

  lines.push('');
  lines.push(`## ${table}`);
  lines.push('');
  lines.push('| カラム名 | 日本語名 | 型 | NOT NULL | デフォルト | 制約 |');
  lines.push('|---|---|---|---|---|---|');

  for (const [column, meta] of Object.entries(props)) {
    const japaneseName = toJapaneseColumnName(column);
    const type = meta.format || meta.type || '-';
    const notNull = required.has(column) ? 'Yes' : 'No';
    const defaultValue = Object.prototype.hasOwnProperty.call(meta, 'default')
      ? String(meta.default)
      : '-';
    const constraint = parseConstraint(meta.description || '');

    lines.push(
      `| \`${column}\` | ${japaneseName} | \`${type}\` | ${notNull} | \`${defaultValue}\` | ${constraint} |`,
    );
  }
}

const outputPath = path.join(rootDir, 'docs', 'table_definition.md');
fs.writeFileSync(outputPath, `${lines.join('\n')}\n`, 'utf8');

console.log(`Generated: ${outputPath}`);
