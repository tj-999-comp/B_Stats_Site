"""設定ファイル"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
SUPABASE_SECRET_KEYS: str = os.getenv('SUPABASE_SECRET_KEYS', '')
DB_ENABLED: bool = bool(SUPABASE_URL and SUPABASE_SECRET_KEYS)

BASE_URL = 'https://www.bleague.jp'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; BleagueStatsScraper/1.0)',
}

# スクレイピング対象シーズン
SEASONS = ['2024-25']
