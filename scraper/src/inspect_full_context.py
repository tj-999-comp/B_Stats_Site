"""HTMLから_contexts_s3id.dataの完全な構造を取得"""

import json
import requests
from src.config import BASE_URL, HEADERS

schedule_key = 502714

# BOX SCOREタブ（tab=2）でリクエスト
url = f'{BASE_URL}/game_detail/'
params = {
    'ScheduleKey': str(schedule_key),
    'tab': '2',  # BOX SCORE tab
}

print(f"Fetching: {url}")
print(f"Params: {params}")

response = requests.get(url, params=params, headers=HEADERS, timeout=60)
response.raise_for_status()

html = response.text

# _contexts_s3id.data を抽出
needle = '_contexts_s3id.data = '
start = html.find(needle)
if start < 0:
    print("ERROR: Could not find _contexts_s3id.data")
    exit(1)

index = start + len(needle)
while index < len(html) and html[index] != '{':
    index += 1

brace_depth = 0
end = index
for cursor in range(index, len(html)):
    char = html[cursor]
    if char == '{':
        brace_depth += 1
    elif char == '}':
        brace_depth -= 1
        if brace_depth == 0:
            end = cursor + 1
            break

raw_json = html[index:end]
context = json.loads(raw_json)

# 全キーを表示
print("\nAll keys in _contexts_s3id.data:")
print(json.dumps(list(context.keys()), indent=2))

# BoxScoresキーがあれば確認
if 'BoxScores' in context:
    print("\nBoxScores found! Sample:")
    box_scores = context['BoxScores']
    if box_scores and len(box_scores) > 0:
        sample = box_scores[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))

# PlayersOnHomeキーがあれば確認
if 'PlayersOnHome' in context:
    print("\nPlayersOnHome found! Sample:")
    players_home = context['PlayersOnHome']
    if players_home and len(players_home) > 0:
        sample = players_home[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))

# PlayersOnAwayキーがあれば確認
if 'PlayersOnAway' in context:
    print("\nPlayersOnAway found! Sample:")
    players_away = context['PlayersOnAway']
    if players_away and len(players_away) > 0:
        sample = players_away[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))

# 完全なデータを保存
output_path = "/Users/ryosuketajima/git-tj999/B_Stats_Site/scraper/data/full_context_tab2.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(context, f, indent=2, ensure_ascii=False)

print(f"\nFull context saved to: {output_path}")
print(f"Total keys: {len(context.keys())}")
