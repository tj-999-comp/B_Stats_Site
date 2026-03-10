"""設定ファイル"""

import os
from pathlib import Path
from dotenv import load_dotenv

# scripts/db/config.py → parent.parent.parent = B_Stats_Site/
SCRAPER_ROOT: Path = Path(__file__).resolve().parent.parent.parent / 'scraper'
load_dotenv(SCRAPER_ROOT / '.env')

SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
SUPABASE_SECRET_KEYS: str = os.getenv('SUPABASE_SECRET_KEYS', '')
DB_ENABLED: bool = bool(SUPABASE_URL and SUPABASE_SECRET_KEYS)

BASE_URL = 'https://www.bleague.jp'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/123.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.bleague.jp/',
}

# スクレイピング対象シーズン
SEASONS = ['2024-25']
