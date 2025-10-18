# main.py
import json
import requests
import pytumblr
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import logging
from logging.handlers import RotatingFileHandler
import coloredlogs
import random
import os
import sys
import smtplib
import ssl

# Import settings from the config file
from config import (
    NEWS_API_KEY, GEMINI_API_URL, NEWS_API_BASE_URL,
    COUNTRIES, CATEGORIES, KURDISH_CATEGORY_MAP, TIMEZONE,
    TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN,
    TUMBLR_OAUTH_SECRET, TUMBLR_BLOG_NAME, FETCH_COOLDOWN_HOURS,
    EMAIL_NOTIFICATIONS_ENABLED, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL,
    QUEUE_FILE, URL_HISTORY_FILE, TIMESTAMP_FILE, LOG_FILE # Import new paths
)

# Constants
STATUS_FETCHED = 'fetched'
STATUS_TRANSLATED = 'translated'

# --- URL History & Queue Functions ---
def load_url_history():
    if not os.path.exists(URL_HISTORY_FILE): return set()
    try:
        with open(URL_HISTORY_FILE, 'r') as f: return set(json.load(f))
    except (json.JSONDecodeError, FileNotFoundError): return set()

def save_url_history(url_set):
    with open(URL_HISTORY_FILE, 'w') as f: json.dump(list(url_set), f)

def load_news_queue():
    if not os.path.exists(QUEUE_FILE): return []
    try:
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            return [] if not content else json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError): return []

def save_news_queue(articles):
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    logging.info(f"💾 Queue saved. {len(articles)} articles remaining.")

# ... (All other helper functions like cooldowns, email, etc., go here) ...
def send_failure_email(article_title):
    if not EMAIL_NOTIFICATIONS_ENABLED or not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]): return
    message = f"Subject: Tumblr Bot Alert: Post Dropped\n\nScript stopped because a post was dropped.\nFailed Article: {article_title}\nWait 24-48 hours before restarting."
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.encode("utf-8"))
            logging.info("✅ Email alert sent.")
    except Exception as e:
        logging.error(f"Failed to send email alert: {e}")

def fetch_and_filter_news(country, category_code, category_config, url_history):
    # ... (function body is mostly the same, just uses url_history) ...
    logging.info(f"▶️ Fetching news for '{category_config['name']}'...")
    params = {'apiKey': NEWS_API_KEY, 'pageSize': 100, **category_config['params']}
    if category_config['endpoint'] == 'top-headlines': params['country'] = country
    full_api_url = f"{NEWS_API_BASE_URL}/{category_config['endpoint']}"
    try:
        response = requests.get(full_api_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"News API request failed: {e}")
        return [], set()

    if data.get('status') != 'ok': return [], set()

    new_articles, new_urls = [], set()
    for article in data.get('articles', []):
        article_url = article.get('url')
        if not article_url or article_url in url_history: continue
        image_url = article.get('urlToImage', '')
        if image_url and not requests.head(image_url, timeout=5).ok: continue
        new_articles.append({
            "url": article_url, "title": article.get('title', 'No Title'), 
            "summary": article.get('description') or article.get('content', ''),
            "category": category_code, "source": article.get('source', {}).get('name', 'N/A'),
            "urlToImage": image_url, "publishedAt": article['publishedAt'], "status": STATUS_FETCHED,
            "category_ku": KURDISH_CATEGORY_MAP.get(category_code, "گشتی")
        })
        new_urls.add(article_url)
    logging.info(f"✅ Found {len(new_articles)} new articles.")
    return new_articles, new_urls

def translate_articles_gemini(articles_to_translate):
    # ... (This function is unchanged) ...
    if not articles_to_translate:
        logging.info("ℹ️ No articles to translate.")
        return
    logging.info(f"▶️ Translating {len(articles_to_translate)} articles with Gemini...")
    items_to_translate = [{"id": i, "title": a["title"], "summary": a["summary"]} for i, a in enumerate(articles_to_translate)]
    prompt = f"STRICT INSTRUCTION: Translate ONLY the 'title' and 'summary' fields of these news articles into Kurdish Sorani (ckb). RULES: 1. Clean the title: Remove source names (e.g., 'Reuters:'). 2. Bracket Proper Nouns: Enclose all proper nouns (people, places) in parentheses, e.g., '(Joe Biden)'. The output MUST be ONLY a valid JSON array of objects with ONLY 'id', 'title', and 'summary' fields. No extra text or markdown.\n\nInput Data:\n{json.dumps(items_to_translate, ensure_ascii=False)}"
    headers, payload = {'Content-Type': 'application/json'}, {'contents': [{'parts': [{'text': prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        json_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        translated_data = json.loads(json_text.strip().lstrip("```json").rstrip("```").strip())
        for item in translated_data:
            article = articles_to_translate[item['id']]
            article['title_ku'] = item['title']
            article['summary_ku'] = item['summary']
            article['status'] = STATUS_TRANSLATED
        logging.info(f"✅ Translation complete for {len(translated_data)} articles.")
    except Exception as e:
        logging.error(f"Gemini translation failed: {e}")


def post_to_tumblr(client, article):
    # ... (This function is unchanged but for the slower delay) ...
    logging.info(f"▶️ Posting '{article.get('title_ku', 'No Title')[:30]}...'")
    tags = [article['category_ku'], article['source']]
    try:
        if article.get('urlToImage'):
            response = client.create_photo(TUMBLR_BLOG_NAME, state="published", tags=tags, source=article['urlToImage'], caption=f"<h5>{article['title_ku']}</h5><p>{article['summary_ku']}</p>", link=article['url'], format="html")
        else:
            response = client.create_link(TUMBLR_BLOG_NAME, state="published", title=article['title_ku'], url=article['url'], description=f"<p>{article['summary_ku']}</p>", tags=tags, format="html")
        
        post_id = response.get('id')
        if not post_id:
            logging.critical("CRITICAL: Post dropped by spam filter. Shutting down.")
            send_failure_email(article.get('title_ku', 'N/A'))
            sys.exit(1)
        
        time.sleep(3)
        if client.posts(TUMBLR_BLOG_NAME, id=post_id).get('posts'):
            logging.info(f"  - ✅ Verified Post ID: {post_id}")
            return True
        else:
            logging.warning(f"  - VERIFICATION FAILED. Shutting down.")
            send_failure_email(article.get('title_ku', 'N/A'))
            sys.exit(1)
    except Exception as e:
        logging.error(f"An exception occurred during posting: {e}")
        return False


def main():
    # --- Setup Logging ---
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    coloredlogs.install(level='INFO', logger=logger)
    logging.info("--- Script starting ---")

    # --- Initial User Choices ---
    selected_country = prompt_for_choice("Please choose a country:", COUNTRIES, 'us')
    # ... (rest of main function is refactored for new logic)
    selected_category_key = prompt_for_choice("\nProcess all categories or a single one?", CATEGORIES, allow_all=True)
    
    try:
        tumblr_client = pytumblr.TumblrRestClient(TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN, TUMBLR_OAUTH_SECRET)
        tumblr_client.info()
    except Exception as e:
        logging.error(f"Tumblr authentication failed: {e}")
        return

    # --- Load all data once ---
    news_queue = load_news_queue()
    url_history = load_url_history()
    timestamps = load_timestamps()

    categories_to_process = CATEGORIES if selected_category_key == 'all' else {selected_category_key: CATEGORIES[selected_category_key]}

    for category_code, config in categories_to_process.items():
        logging.info(f"\n--- Processing Category: {config['name']} ---")
        if is_on_cooldown(category_code, timestamps):
            continue

        new_articles, new_urls = fetch_and_filter_news(selected_country, category_code, config, url_history)
        if new_articles:
            news_queue.extend(new_articles)
            url_history.update(new_urls)
            timestamps[category_code] = datetime.now().isoformat()
            save_news_queue(news_queue)
            save_url_history(url_history)
            save_timestamps(timestamps)

        articles_to_translate = [a for a in news_queue if a.get('category') == category_code and a.get('status') == STATUS_FETCHED]
        if articles_to_translate:
            translate_articles_gemini(articles_to_translate)
            save_news_queue(news_queue)

    # --- Post all translated articles regardless of category ---
    articles_to_post = [a for a in news_queue if a.get('status') == STATUS_TRANSLATED]
    if articles_to_post:
        articles_to_post.sort(key=lambda x: x['publishedAt'], reverse=True)
        logging.info(f"\n--- Found {len(articles_to_post)} translated articles to post ---")
        for article in articles_to_post:
            if post_to_tumblr(tumblr_client, article):
                news_queue = [item for item in news_queue if item['url'] != article['url']]
                save_news_queue(news_queue)
            
            pause = random.uniform(180, 300) # 3-5 minute pause
            logging.info(f"  - Pausing for {pause:.1f} seconds...")
            time.sleep(pause)

    logging.info("\n✅ Cycle complete. Script finished.")

if __name__ == "__main__":
    main()