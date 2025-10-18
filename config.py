# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET = os.getenv("TUMBLR_CONSUMER_SECRET")
TUMBLR_OAUTH_TOKEN = os.getenv("TUMBLR_OAUTH_TOKEN")
TUMBLR_OAUTH_SECRET = os.getenv("TUMBLR_OAUTH_SECRET")
TUMBLR_BLOG_NAME = os.getenv("TUMBLR_BLOG_NAME")

# --- File Configuration ---
OUTPUT_FILE = 'news.json'
TIMEZONE = 'Asia/Baghdad'

# --- API Endpoints ---
NEWS_API_BASE_URL = "https://newsapi.org/v2" # Base URL, endpoint will be added later
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"

# --- User-Selectable Options ---
COUNTRIES = {
    'us': 'United States', 'gb': 'United Kingdom', 'de': 'Germany',
    'fr': 'France', 'ca': 'Canada', 'au': 'Australia', 'tr': 'Turkey',
    'ae': 'United Arab Emirates', 'ar': 'Argentina', 'at': 'Austria',
    'be': 'Belgium', 'bg': 'Bulgaria', 'br': 'Brazil', 'ch': 'Switzerland',
    'cn': 'China', 'co': 'Colombia', 'cu': 'Cuba', 'cz': 'Czech Republic',
    'eg': 'Egypt', 'gr': 'Greece', 'hk': 'Hong Kong', 'hu': 'Hungary',
    'id': 'Indonesia', 'ie': 'Ireland', 'il': 'Israel', 'in': 'India',
    'it': 'Italy', 'jp': 'Japan', 'kr': 'South Korea', 'lt': 'Lithuania',
    'lv': 'Latvia', 'ma': 'Morocco', 'mx': 'Mexico', 'my': 'Malaysia',
    'ng': 'Nigeria', 'nl': 'Netherlands', 'no': 'Norway', 'nz': 'New Zealand',
    'ph': 'Philippines', 'pl': 'Poland', 'pt': 'Portugal', 'ro': 'Romania',
    'rs': 'Serbia', 'ru': 'Russia', 'sa': 'Saudi Arabia', 'se': 'Sweden',
    'sg': 'Singapore', 'si': 'Slovenia', 'sk': 'Slovakia', 'th': 'Thailand',
    'tw': 'Taiwan', 'ua': 'Ukraine', 've': 'Venezuela', 'za': 'South Africa'
}

# --- NEW: Upgraded Category Definitions ---
CATEGORIES = {
    # This is the new, special category for Kurdistan
    'kurdistan': {
        'name': 'Kurdistan',
        'endpoint': 'everything', # Uses the /everything endpoint
        'params': {'q': 'kurd OR kurdistan OR Kurdish OR kurds', 'searchIn': 'title,description'}
    },
    'general': {
        'name': 'General',
        'endpoint': 'top-headlines', # Uses the /top-headlines endpoint
        'params': {'category': 'general'}
    },
    'business': {
        'name': 'Business',
        'endpoint': 'top-headlines',
        'params': {'category': 'business'}
    },
    'entertainment': {
        'name': 'Entertainment',
        'endpoint': 'top-headlines',
        'params': {'category': 'entertainment'}
    },
    'health': {
        'name': 'Health',
        'endpoint': 'top-headlines',
        'params': {'category': 'health'}
    },
    'science': {
        'name': 'Science',
        'endpoint': 'top-headlines',
        'params': {'category': 'science'}
    },
    'sports': {
        'name': 'Sports',
        'endpoint': 'everything',
        'params': {'q': 'laliga OR la liga OR El Clásico OR UEFA OR fifa', 'searchIn': 'title,description'}
    },
    'technology': {
        'name': 'Technology',
        'endpoint': 'top-headlines',
        'params': {'category': 'technology'}
    },
    'politics': {
        'name': 'Politics',
        'endpoint': 'top-headlines',
        'params': {'category': 'politics'}
    }
}

# --- Translation Mapping ---
KURDISH_CATEGORY_MAP = {
    'kurdistan': 'کورد', # New translation
    'business': 'ئابووری',
    'entertainment': 'هەمەڕەنگ',
    'general': 'گشتی',
    'health': 'تەندرووستی',
    'science': 'زانست',
    'sports': 'وەرزش',
    'technology': 'تەکنەلۆژیا',
    'politics': 'سیاسەت'
}