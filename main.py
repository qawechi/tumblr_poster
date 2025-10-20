# main.py
import json
import requests
import pytumblr
from datetime import datetime, timedelta
import time
import logging
from logging.handlers import RotatingFileHandler
import coloredlogs
import random
import os
import smtplib
import ssl
import telegram
from telegram.error import TelegramError
import asyncio
import psycopg2 # Use PostgreSQL driver
from psycopg2.extras import DictCursor # To get dictionary-like results
import re

# Import settings from the config file
from config import (
    NEWS_API_KEYS, GEMINI_API_URL, NEWS_API_BASE_URL,
    COUNTRIES, CATEGORIES, KURDISH_CATEGORY_MAP,
    TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN,
    TUMBLR_OAUTH_SECRET, TUMBLR_BLOG_NAME, FETCH_COOLDOWN_HOURS,
    EMAIL_NOTIFICATIONS_ENABLED, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL,
    DATABASE_URL, LOG_FILE, CONTACT_EMAIL, BLOG_URL,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TRANSLATION_CHUNK_SIZE,
    GEMINI_TAG_COUNT, POST_TO_TUMBLR, POST_TO_TELEGRAM,
    CYCLE_COOLDOWN_MINUTES, TARGET_COUNTRY, TARGET_CATEGORY,
    USE_SELENIUM_SCRAPING
)

# Imports for Web Scraping
from newspaper import Article, Config
import nltk

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# One-time setup for newspaper3k's dependency
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logging.info("Downloading 'punkt' for NLTK (one-time setup)...")
    nltk.download('punkt')

# Constants
STATUS_FETCHED = 'fetched'
STATUS_TRANSLATED = 'translated'
STATUS_POSTED = 'posted'

## Database Functions
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Note: TEXT is used for all string types. PostgreSQL is flexible.
                cursor.execute('''CREATE TABLE IF NOT EXISTS articles (
                                  url TEXT PRIMARY KEY, title TEXT, summary TEXT, category TEXT, 
                                  source TEXT, urlToImage TEXT, publishedAt TEXT, 
                                  status TEXT DEFAULT 'fetched', title_ku TEXT, summary_ku TEXT, 
                                  category_ku TEXT, generated_tags TEXT
                               )''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS category_cooldowns (
                                  category_code TEXT PRIMARY KEY, 
                                  last_fetched TIMESTAMPTZ NOT NULL
                               )''')
                conn.commit()
        logging.info("🗃️ Database initialized successfully.")
    except Exception as e:
        logging.critical(f"❌ Failed to initialize database: {e}")
        raise

def is_url_in_db(conn, url):
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM articles WHERE url = %s", (url,))
        return cursor.fetchone() is not None

def add_articles_to_db(conn, articles):
    with conn.cursor() as cursor:
        articles_to_insert = [(a['url'], a['title'], a['summary'], a['category'], a['source'], a['urlToImage'], a['publishedAt'], a['status'], a['category_ku']) for a in articles]
        # Use executemany for batch inserts
        psycopg2.extras.execute_values(
            cursor,
            'INSERT INTO articles (url, title, summary, category, source, urlToImage, publishedAt, status, category_ku) VALUES %s ON CONFLICT (url) DO NOTHING',
            articles_to_insert
        )
        conn.commit()

def get_articles_by_status(conn, status):
    # Use DictCursor to get results as dictionaries
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT * FROM articles WHERE status = %s", (status,))
        # DictCursor results are already dictionary-like
        return [dict(row) for row in cursor.fetchall()]

def update_article_translation(conn, url, title_ku, summary_ku, tags_json):
    with conn.cursor() as cursor:
        cursor.execute('UPDATE articles SET title_ku = %s, summary_ku = %s, generated_tags = %s, status = %s WHERE url = %s', 
                       (title_ku, summary_ku, tags_json, STATUS_TRANSLATED, url))
        conn.commit()

def update_article_status(conn, url, status):
    with conn.cursor() as cursor:
        cursor.execute("UPDATE articles SET status = %s WHERE url = %s", (status, url))
        conn.commit()

def is_on_cooldown(conn, category_code):
    with conn.cursor() as cursor:
        cursor.execute("SELECT last_fetched FROM category_cooldowns WHERE category_code = %s", (category_code,))
        result = cursor.fetchone()
        if not result: return False
        
        # In PostgreSQL, last_fetched is a timezone-aware datetime object
        last_fetch_time = result[0]
        
        # We need a timezone-aware `now` to compare
        now_utc = datetime.now(last_fetch_time.tzinfo)

        if now_utc < last_fetch_time + timedelta(hours=FETCH_COOLDOWN_HOURS):
            logging.info(f"Category '{category_code}' is on cooldown. Skipping fetch.")
            return True
    return False

def update_cooldown_timestamp(conn, category_code):
    with conn.cursor() as cursor:
        # Use `NOW()` for a timezone-aware timestamp from the database itself
        cursor.execute('INSERT INTO category_cooldowns (category_code, last_fetched) VALUES (%s, NOW()) ON CONFLICT (category_code) DO UPDATE SET last_fetched = NOW()', 
                       (category_code,))
        conn.commit()


## Helper Functions
def send_failure_email(article_title):
    if not EMAIL_NOTIFICATIONS_ENABLED or not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]): return
    message = f"Subject: Tumblr Bot Alert: Post Dropped\n\nScript stopped because a post was dropped.\nFailed Article: {article_title}"
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.encode("utf-8"))
            logging.info("✅ Email alert sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email alert: {e}")
def is_image_url_valid(url):
    if not url or not url.startswith(('http://', 'https://')): return False
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException: return False

## Core API & Scraping Functions
def scrape_full_article_text(url):
    """Scrapes article text. Uses Selenium if enabled, otherwise uses newspaper3k directly."""
    if not USE_SELENIUM_SCRAPING:
        try:
            config = Config()
            config.browser_user_agent = f'DANA News Bot/1.0 (Contact: {CONTACT_EMAIL}; Blog: {BLOG_URL})'
            config.request_timeout = 10
            article = Article(url, config=config)
            article.download()
            article.parse()
            if len(article.text) < 250:
                logging.warning(f"Scraped text is too short (<250 chars). Skipping. URL: {url}")
                return None
            return article.text
        except Exception as e:
            logging.error(f"Failed to scrape article at {url} with newspaper3k. Error: {e}")
            return None
    else:
        logging.info(f"   -> Using Selenium to scrape: {url}")
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument(f"user-agent=DANA News Bot/1.0 (Contact: {CONTACT_EMAIL}; Blog: {BLOG_URL})")
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(url)
            time.sleep(3)
            page_source = driver.page_source

            config = Config()
            config.browser_user_agent = f'DANA News Bot/1.0 (Contact: {CONTACT_EMAIL}; Blog: {BLOG_URL})'
            article = Article(url, config=config)
            article.download(input_html=page_source)
            article.parse()

            if len(article.text) < 250:
                logging.warning(f"Scraped text (via Selenium) is too short. Skipping.")
                return None
            return article.text
        except Exception as e:
            logging.error(f"Failed to scrape article at {url} with Selenium. Error: {e}")
            return None
        finally:
            if driver:
                driver.quit()

def fetch_and_filter_news(conn, country, category_code, category_config):
    """Fetches a list of articles, trying multiple API keys on failure."""
    logging.info(f"▶️ Fetching news for '{category_config['name']}'...")
    headers = {'User-Agent': f'DANA News Bot/1.0 (Contact: {CONTACT_EMAIL}; Blog: {BLOG_URL})'}

    if not NEWS_API_KEYS:
        logging.error("❌ No NewsAPI keys found in .env file. Skipping fetch.")
        return []

    for api_key in NEWS_API_KEYS:
        params = {'apiKey': api_key, **category_config.get('params', {})}
        if category_config.get('endpoint') == 'top-headlines':
            params['country'] = country
        
        full_api_url = f"{NEWS_API_BASE_URL}/{category_config['endpoint']}"

        try:
            response = requests.get(full_api_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'ok':
                logging.info(f"   - Successfully fetched using API key ending in '...{api_key[-4:]}'")
                new_articles = []
                for article in data.get('articles', []):
                    article_url = article.get('url')
                    if not article_url or is_url_in_db(conn, article_url):
                        continue
                    
                    image_url = article.get('urlToImage', '')
                    if image_url and not is_image_url_valid(image_url):
                        logging.warning(f"Skipping article with invalid image URL: {image_url}")
                        continue

                    logging.info(f"  -> Scraping full text for: {article_url}")
                    full_text = scrape_full_article_text(article_url)
                    if not full_text:
                        logging.warning("  -> Skipping article due to scraping failure or short content.")
                        continue
                        
                    new_articles.append({
                        "url": article_url, "title": article.get('title', 'No Title'), "summary": full_text,
                        "category": category_code, "source": article.get('source', {}).get('name', 'N/A'),
                        "urlToImage": image_url, "publishedAt": article['publishedAt'], "status": STATUS_FETCHED,
                        "category_ku": KURDISH_CATEGORY_MAP.get(category_code, "گشتی")
                    })
                logging.info(f"✅ Found and successfully scraped {len(new_articles)} new articles.")
                return new_articles
            else:
                logging.warning(f"   - API key ...{api_key[-4:]} failed with status: {data.get('message')}")
                continue

        except requests.exceptions.RequestException as e:
            logging.warning(f"   - API key ...{api_key[-4:]} failed with network error: {e}")
            continue

    logging.error("❌ All NewsAPI keys failed. Cannot fetch news for this category.")
    return []

def translate_articles_gemini(articles_to_translate):
    if not articles_to_translate: return []
    logging.info(f"▶️ Translating and structuring {len(articles_to_translate)} articles with Gemini...")
    items_to_translate = [{"id": a["url"], "title": a["title"], "summary": a["summary"]} for a in articles_to_translate]
    prompt = f"""
    STRICT INSTRUCTION: For each news article, perform four tasks and return a single JSON array of objects.
    1.  **Translate and Structure**: Translate the 'title' and 'summary' fields into professional Kurdish Sorani (ckb). The translated 'summary' MUST be formatted as a single string of valid HTML. Use `<p>` tags for each paragraph. Use `<h4>` for subheadings. Use `<strong>` to emphasize key phrases.
    2.  **Clean and Format**: In the translated 'title', you MUST REMOVE any source names (e.g., 'Reuters:'). In BOTH the translated 'title' and the HTML 'summary', you MUST ENCLOSE all proper nouns in single parentheses. Example: '<strong>Joe Biden</strong>' becomes '<strong>(جۆ بایدن)</strong>'. Pay close attention to proper Kurdish punctuation, including commas (،), semicolons (؛), and periods (.).
    3.  **Generate Tags**: Create a new field named 'tags'. It MUST be a JSON array of exactly {GEMINI_TAG_COUNT} relevant keywords in Kurdish. Do not use hashtags (#).
    The output MUST be ONLY a valid JSON array of objects. Each object must contain ONLY 'id', 'title', 'summary' (as an HTML string), and 'tags'. The 'id' MUST be the original article URL. Do not include any extra text or markdown.
    Input Data: {json.dumps(items_to_translate, ensure_ascii=False)}
    """
    headers, payload = {'Content-Type': 'application/json'}, {'contents': [{'parts': [{'text': prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        json_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        translated_data = json.loads(json_text.strip().lstrip("```json").rstrip("```").strip())
        logging.info(f"✅ Translation and structuring complete for {len(translated_data)} articles.")
        return translated_data
    except (requests.exceptions.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        logging.error(f"Gemini API call failed: {e}. Will retry on the next cycle.")
        return []

## Posting Functions & Main Logic
def post_to_tumblr(client, article):
    logging.info(f"▶️ Posting to Tumblr '{article.get('title_ku', 'No Title')[:30]}...'")
    tags = [article['category_ku'], article['source']]
    try:
        if article.get('generated_tags'): tags.extend(json.loads(article['generated_tags']))
    except json.JSONDecodeError: logging.warning("Could not parse generated_tags from database.")
    
    full_summary_html = article['summary_ku']
    source_html = f"<p class='text-center'><a class='link-secondary link-offset-3' href='{article['url']}' target='_blank'>{article['source']}</a></p>"
    
    try:
        if article.get('urlToImage'):
            summary_with_more_tag = full_summary_html.replace('</p>', '</p>[[MORE]]', 1)
            caption_html = f"<h5 class='card-title lh-base pt-1'>{article['title_ku']}</h5>{summary_with_more_tag}{source_html}"
            response = client.create_photo(TUMBLR_BLOG_NAME, state="published", tags=tags, source=article['urlToImage'], caption=caption_html, link=article['url'], format="html")
        else:
            description_html = f"<p class='card-text text-muted 1h-base'>{full_summary_html}</p>{source_html}"
            response = client.create_link(TUMBLR_BLOG_NAME, state="published", title=article['title_ku'], url=article['url'], description=description_html, tags=tags, format="html")
        
        post_id = response.get('id')
        if not post_id:
            logging.critical("CRITICAL: Post dropped by Tumblr spam filter.")
            send_failure_email(article.get('title_ku', 'N/A'))
            return None

        time.sleep(3)
        if client.posts(TUMBLR_BLOG_NAME, id=post_id).get('posts'):
            logging.info(f"  - ✅ Verified Tumblr Post ID: {post_id}")
            return post_id
        else:
            logging.warning("  - VERIFICATION FAILED. Post may have been dropped.")
            send_failure_email(article.get('title_ku', 'N/A'))
            return None
    except Exception as e:
        logging.error(f"An exception occurred during posting to Tumblr: {e}")
        return None
async def async_post_to_telegram(telegram_bot, article, see_more_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return False
    logging.info(f"▶️ Posting summary to Telegram: '{article.get('title_ku', 'No Title')[:30]}...'")
    title_ku, summary_html = article['title_ku'], article['summary_ku']
    plain_text_summary = re.sub('<[^<]+?>', '', summary_html).strip()
    preview_text = (plain_text_summary[:450] + '...') if len(plain_text_summary) > 450 else plain_text_summary
    post_text = f"<b>{title_ku}</b>\n\n{preview_text}\n\n<i><a href='{see_more_url}'>درێژەی بابەت...</a></i>"
    try:
        image_url = article.get('urlToImage')
        if image_url and is_image_url_valid(image_url):
            await telegram_bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_url, caption=post_text, parse_mode='HTML')
        else:
            await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=post_text, parse_mode='HTML', disable_web_page_preview=True)
        logging.info("  - ✅ Telegram summary post sent successfully.")
        return True
    except TelegramError as e:
        logging.error(f"❌ Telegram posting failed (Error: {e}).")
        return False
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred during Telegram posting: {e}")
        return False
def post_to_telegram(telegram_bot, article, see_more_url):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(async_post_to_telegram(telegram_bot, article, see_more_url))
    except Exception as e:
        logging.error(f"❌ Synchronous Telegram wrapper failed: {e}")
        return False
async def async_check_telegram(telegram_bot):
    await telegram_bot.get_me()
def run_cycle(tumblr_client, telegram_bot, selected_country, selected_category_key):
    logging.info("--- Starting new cycle ---")
    try:
        with get_db_connection() as conn:
            categories_to_process = CATEGORIES if selected_category_key == 'all' else {selected_category_key: CATEGORIES[selected_category_key]}
            for i, (category_code, config) in enumerate(categories_to_process.items()):
                if i > 0: logging.info("")
                logging.info(f"--- Processing Category: {config['name']} ---")
                if is_on_cooldown(conn, category_code): continue
                new_articles = fetch_and_filter_news(conn, selected_country, category_code, config)
                if new_articles:
                    add_articles_to_db(conn, new_articles)
                    update_cooldown_timestamp(conn, category_code)

            articles_to_translate = get_articles_by_status(conn, STATUS_FETCHED)
            if articles_to_translate:
                logging.info(f"\n--- Found {len(articles_to_translate)} articles to translate ---")
                for i in range(0, len(articles_to_translate), TRANSLATION_CHUNK_SIZE):
                    chunk = articles_to_translate[i:i + TRANSLATION_CHUNK_SIZE]
                    logging.info(f"Processing translation chunk {i//TRANSLATION_CHUNK_SIZE + 1}...")
                    translated_results = translate_articles_gemini(chunk)
                    for item in translated_results:
                        tags_json = json.dumps(item.get('tags', []), ensure_ascii=False)
                        update_article_translation(conn, item['id'], item['title'], item['summary'], tags_json)
                    logging.info("Chunk translated and saved to DB.")

            articles_to_post = get_articles_by_status(conn, STATUS_TRANSLATED)
            if articles_to_post:
                if POST_TO_TUMBLR or POST_TO_TELEGRAM:
                    # **CORRECTED LINE:** Use .get() with a default value to prevent KeyError
                    articles_to_post.sort(
                        key=lambda x: x.get('publishedAt', datetime.min.isoformat()), 
                        reverse=False
                    )
                    logging.info(f"\n--- Found {len(articles_to_post)} translated articles to post ---")
                    for article in articles_to_post:
                        tumblr_post_id, telegram_posted = None, False
                        if POST_TO_TUMBLR:
                            tumblr_post_id = post_to_tumblr(tumblr_client, article)
                        if POST_TO_TELEGRAM:
                            see_more_url = f"https://{TUMBLR_BLOG_NAME}.tumblr.com/post/{tumblr_post_id}" if tumblr_post_id else article['url']
                            telegram_posted = post_to_telegram(telegram_bot, article, see_more_url)
                        if tumblr_post_id or telegram_posted:
                            update_article_status(conn, article['url'], STATUS_POSTED)
                            logging.info(f"Article '{article['title_ku'][:30]}...' marked as posted.")
                            pause = random.uniform(180, 300)
                            logging.info(f"   - Pausing for {pause:.1f} seconds...")
                            time.sleep(pause)
                        else:
                            logging.warning("All active posts failed for article. It will be retried next cycle.")
                else:
                    logging.info("\nℹ️ Posting to Tumblr and Telegram is disabled in config. Skipping posting stage.")
    except psycopg2.Error as e:
        logging.critical(f"Database connection error during cycle: {e}")
        # The script will pause and retry in the main loop.
        raise
    logging.info("--- Cycle complete ---")
def main():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    coloredlogs.install(level='INFO', logger=logger)
    logging.info("--- Bot starting up ---")

    if not DATABASE_URL:
        logging.critical("DATABASE_URL is not set in the .env file. Exiting.")
        return

    init_db()
    if TARGET_COUNTRY not in COUNTRIES:
        logging.critical(f"Invalid TARGET_COUNTRY '{TARGET_COUNTRY}' in .env file. Exiting.")
        return
    if TARGET_CATEGORY != 'all' and TARGET_CATEGORY not in CATEGORIES:
        logging.critical(f"Invalid TARGET_CATEGORY '{TARGET_CATEGORY}' in .env file. Exiting.")
        return
    logging.info(f"✅ Configuration loaded: Country='{TARGET_COUNTRY}', Category='{TARGET_CATEGORY}', Selenium='{USE_SELENIUM_SCRAPING}'")
    try:
        tumblr_client = pytumblr.TumblrRestClient(TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN, TUMBLR_OAUTH_SECRET)
        tumblr_client.info()
        logging.info("✅ Tumblr client initialized.")
        telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        try: loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(async_check_telegram(telegram_bot))
        logging.info("✅ Telegram bot initialized.")
    except Exception as e:
        logging.error(f"API authentication failed: {e}. Check your keys in the .env file. Exiting.")
        return
    while True:
        try:
            run_cycle(tumblr_client, telegram_bot, TARGET_COUNTRY, TARGET_CATEGORY)
            logging.info(f"Cooldown initiated. Waiting for {CYCLE_COOLDOWN_MINUTES} minutes...")
            time.sleep(CYCLE_COOLDOWN_MINUTES * 60)
        except KeyboardInterrupt:
            logging.info("Bot stopped manually by user.")
            break
        except Exception as e:
            logging.critical(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            logging.critical("Restarting cycle after a 10-minute safety pause...")
            time.sleep(10 * 60)

if __name__ == "__main__":
    main()