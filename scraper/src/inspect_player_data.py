"""選手データ構造の調査スクリプト"""

import json
from src.game_scraper import fetch_game_context

# 既存のゲームから1つ選んでデータ構造を確認
schedule_key = 502714

print("Fetching game context...")
context = fetch_game_context(schedule_key, include_play_by_play=False)

# contextの全キーを表示
print("\nContext keys:")
print(json.dumps(list(context.keys()), indent=2))

# gameオブジェクトのキーを表示
print("\nGame keys:")
if 'game' in context:
    print(json.dumps(list(context['game'].keys()), indent=2))

# summariesのサンプルを表示
print("\nSummaries sample:")
if 'summaries' in context and context['summaries']:
    summary = context['summaries'][0]
    print(json.dumps(summary, indent=2, ensure_ascii=False))

# 完全なcontextをファイルに保存
output_path = "/Users/ryosuketajima/git-tj999/B_Stats_Site/scraper/data/sample_game_context.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(context, f, indent=2, ensure_ascii=False)

print(f"\nFull context saved to: {output_path}")
