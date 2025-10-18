# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Folder and File Configuration ---
DATA_DIR = 'data'
LOGS_DIR = 'logs'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Main data files
QUEUE_FILE = os.path.join(DATA_DIR, 'news_queue.json')
URL_HISTORY_FILE = os.path.join(DATA_DIR, 'url_history.json')
TIMESTAMP_FILE = os.path.join(DATA_DIR, 'cache_timestamps.json')
LOG_FILE = os.path.join(LOGS_DIR, 'script.log')

# --- API Keys ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET = os.getenv("TUMBLR_CONSUMER_SECRET")
TUMBLR_OAUTH_TOKEN = os.getenv("TUMBLR_OAUTH_TOKEN")
TUMBLR_OAUTH_SECRET = os.getenv("TUMBLR_OAUTH_SECRET")
TUMBLR_BLOG_NAME = os.getenv("TUMBLR_BLOG_NAME")

# --- Script Settings ---
TIMEZONE = 'Asia/Baghdad'
FETCH_COOLDOWN_HOURS = 2

# --- API Endpoints ---
NEWS_API_BASE_URL = "https://newsapi.org/v2"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

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

# --- Category Definitions ---
CATEGORIES = {
    'kurdistan': {'name': 'Kurdistan', 'endpoint': 'everything', 'params': {'q': 'kurd OR kurdistan OR Kurdish OR kurds', 'searchIn': 'title,description'}},
    'general': {'name': 'General', 'endpoint': 'top-headlines', 'params': {'category': 'general'}},
    'business': {'name': 'Business', 'endpoint': 'top-headlines', 'params': {'category': 'business'}},
    'entertainment': {'name': 'Entertainment', 'endpoint': 'top-headlines', 'params': {'category': 'entertainment'}},
    'health': {'name': 'Health', 'endpoint': 'top-headlines', 'params': {'category': 'health'}},
    'science': {'name': 'Science', 'endpoint': 'top-headlines', 'params': {'category': 'science'}},
    'sports': {'name': 'Sports', 'endpoint': 'everything', 'params': {'q': 'laliga OR la liga OR El Clásico OR UEFA OR fifa', 'searchIn': 'title,description'}},
    'technology': {'name': 'Technology', 'endpoint': 'top-headlines', 'params': {'category': 'technology'}},
    'politics': {'name': 'Politics', 'endpoint': 'top-headlines', 'params': {'category': 'politics'}}
}

# --- Translation Mapping ---
KURDISH_CATEGORY_MAP = {
    'kurdistan': 'کورد', 'business': 'ئابووری', 'entertainment': 'هەمەڕەنگ',
    'general': 'گشتی', 'health': 'تەندرووستی', 'science': 'زانست',
    'sports': 'وەرزش', 'technology': 'تەکنەلۆژیا', 'politics': 'سیاسەت'
}

# --- Email Notification Settings ---
EMAIL_NOTIFICATIONS_ENABLED = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "False").lower() == "true"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")