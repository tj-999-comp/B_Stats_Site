"""設定ファイル"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY: str = os.environ['SUPABASE_SERVICE_ROLE_KEY']

BASE_URL = 'https://www.bleague.jp'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; BleagueStatsScraper/1.0)',
}

# スクレイピング対象シーズン
SEASONS = ['2024-25']
