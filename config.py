# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- Folder and File Configuration ---
# The DATA_DIR and LOGS_DIR are still useful for logs, but the DB file is no longer needed.
DATA_DIR = 'data'
LOGS_DIR = 'logs'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, 'script.log')

# --- Database Connection ---
# Use the online PostgreSQL database URL from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# --- API Keys ---
NEWS_API_KEYS_STRING = os.getenv("NEWS_API_KEYS", "")
NEWS_API_KEYS = [key.strip() for key in NEWS_API_KEYS_STRING.split(',') if key.strip()]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET = os.getenv("TUMBLR_CONSUMER_SECRET")
TUMBLR_OAUTH_TOKEN = os.getenv("TUMBLR_OAUTH_TOKEN")
TUMBLR_OAUTH_SECRET = os.getenv("TUMBLR_OAUTH_SECRET")
TUMBLR_BLOG_NAME = os.getenv("TUMBLR_BLOG_NAME")

# --- Telegram Keys ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Script Settings ---
USE_SELENIUM_SCRAPING = os.getenv("USE_SELENIUM_SCRAPING", "false").lower() == "true"
TARGET_COUNTRY = os.getenv("TARGET_COUNTRY", "us")
TARGET_CATEGORY = os.getenv("TARGET_CATEGORY", "all")
TIMEZONE = 'Asia/Baghdad'
FETCH_COOLDOWN_HOURS = 2
TRANSLATION_CHUNK_SIZE = 80
GEMINI_TAG_COUNT = 4
CYCLE_COOLDOWN_MINUTES = int(os.getenv("CYCLE_COOLDOWN_MINUTES", "60"))

# --- Posting Platform Toggles ---
POST_TO_TUMBLR = os.getenv("POST_TO_TUMBLR", "true").lower() == "true"
POST_TO_TELEGRAM = os.getenv("POST_TO_TELEGRAM", "true").lower() == "true"

# --- User-Agent Information ---
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")
BLOG_URL = os.getenv("BLOG_URL")

# --- API Endpoints ---
NEWS_API_BASE_URL = "https://newsapi.org/v2"
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

# --- Category Definitions ---
CATEGORIES = {
    'kurdistan': {'name': 'Kurdistan', 'endpoint': 'everything', 'params': {'q': 'kurd OR kurdistan OR Kurdish OR kurds', 'searchIn': 'title,description', 'pageSize': 10}},
    'general': {'name': 'General', 'endpoint': 'top-headlines', 'params': {'category': 'general', 'pageSize': 10}},
    'business': {'name': 'Business', 'endpoint': 'top-headlines', 'params': {'category': 'business', 'pageSize': 10}},
    'entertainment': {'name': 'Entertainment', 'endpoint': 'top-headlines', 'params': {'category': 'entertainment', 'pageSize': 10}},
    'health': {'name': 'Health', 'endpoint': 'top-headlines', 'params': {'category': 'health', 'pageSize': 10}},
    'science': {'name': 'Science', 'endpoint': 'top-headlines', 'params': {'category': 'science', 'pageSize': 10}},
    'sports': {'name': 'Sports', 'endpoint': 'everything', 'params': {'q': 'laliga OR UEFA OR fifa OR "premier league" OR "el clasico"', 'searchIn': 'title,description', 'pageSize': 10}},
    'technology': {'name': 'Technology', 'endpoint': 'top-headlines', 'params': {'category': 'technology', 'pageSize': 10}}
}

# --- Translation Mapping ---
KURDISH_CATEGORY_MAP = {
    'kurdistan': 'کورد', 'business': 'ئابووری', 'entertainment': 'هەمەڕەنگ',
    'general': 'گشتی', 'health': 'تەندرووستی', 'science': 'زانست',
    'sports': 'وەرزش', 'technology': 'تەکنەلۆژیا'
}

# --- Email Notification Settings ---
EMAIL_NOTIFICATIONS_ENABLED = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "False").lower() == "true"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")