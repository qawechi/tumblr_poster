# main.py
import json
import requests
import pytumblr
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import logging
import coloredlogs # NEW: Import for colorful logs

# Import settings from the config file
from config import (
    NEWS_API_KEY, GEMINI_API_URL, NEWS_API_BASE_URL, OUTPUT_FILE,
    COUNTRIES, CATEGORIES, KURDISH_CATEGORY_MAP, TIMEZONE,
    TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN,
    TUMBLR_OAUTH_SECRET, TUMBLR_BLOG_NAME
)

# --- Helper function to check if an image URL is valid ---
def is_image_url_valid(url):
    """
    Checks if an image URL is accessible by sending a HEAD request.
    This is faster than downloading the whole image.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False
    try:
        # Use a HEAD request to get headers only, with a 5-second timeout
        response = requests.head(url, allow_redirects=True, timeout=5)
        # Check for a successful status code (2xx)
        if response.status_code == 200:
            return True
        else:
            logging.warning(f"Image check failed for {url} with status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException as e:
        logging.warning(f"Could not reach image URL {url}. Error: {e}")
        return False

def prompt_for_choice(prompt_message, options, default_key=None):
    """Prompts the user to select an option from a list."""
    print(prompt_message) # This remains a print because it's direct user interaction
    indexed_options = list(options.keys())
    
    for i, key in enumerate(indexed_options):
        number = i + 1
        label = options[key]['name'] if isinstance(options[key], dict) else options[key]
        default_text = " [Default]" if key == default_key else ""
        print(f"  {number}) {label}{default_text}")

    while True:
        try:
            choice = input("> ")
            if choice == "" and default_key is not None:
                return default_key
            
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(indexed_options):
                return indexed_options[choice_index]
            else:
                print("❌ Invalid number. Please try again.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def load_existing_news(file_path):
    """Loads news from the JSON file, returning an empty list if it doesn't exist."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_all_news(file_path, all_articles):
    """Saves the combined list of articles to the JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=4)
    logging.info(f"💾 Progress saved. Total articles in '{file_path}': {len(all_articles)}")

def fetch_and_filter_news(country, category_code, category_config, existing_articles):
    """Fetches news, validates images, and filters out duplicates."""
    logging.info(f"▶️ Step 1: Fetching latest news for '{category_config['name']}'...")
    
    params = {
        'apiKey': NEWS_API_KEY,
        'pageSize': 100,
    }
    
    params.update(category_config['params'])
    
    endpoint = category_config['endpoint']
    if endpoint == 'top-headlines':
        params['country'] = country
        
    full_api_url = f"{NEWS_API_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(full_api_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"News API request failed: {e}")
        return []

    if data.get('status') != 'ok':
        logging.error(f"News API returned status: {data.get('message', 'Unknown Error')}")
        return []

    existing_urls = {article['url'] for article in existing_articles}
    new_articles = []
    
    kurdish_category = KURDISH_CATEGORY_MAP.get(category_code, "گشتی")
    
    articles_from_api = data.get('articles', [])
    logging.info(f"Found {len(articles_from_api)} raw articles from API. Filtering now...")

    for article in articles_from_api:
        # Basic filter for duplicates and missing URLs
        if not article.get('url') or article['url'] in existing_urls:
            continue
            
        # --- Image Validation Step ---
        image_url = article.get('urlToImage', '')
        if image_url and not is_image_url_valid(image_url):
            logging.warning(f"Skipping article due to invalid image URL: '{article.get('title', 'No Title')}'")
            continue # Skip this article entirely

        try:
            dt_utc = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
            dt_local = dt_utc.astimezone(ZoneInfo(TIMEZONE))
            date_str = dt_local.strftime('%Y/%m/%d')
            time_str = dt_local.strftime('%I:%M %p')
        except (ValueError, KeyError):
            date_str = 'Unknown Date'
            time_str = 'Unknown Time'

        new_articles.append({
            "title": article.get('title', 'No Title'),
            "summary": article.get('description') or article.get('content', 'No summary available.'),
            "category": category_code,
            "source": article.get('source', {}).get('name', 'نادیار'),
            "date": date_str,
            "time": time_str,
            "url": article['url'],
            "urlToImage": image_url, # Use the validated image_url
            "publishedAt": article['publishedAt'],
            "title_ku": "",
            "summary_ku": "",
            "category_ku": kurdish_category,
            "status": "fetched"
        })
    
    logging.info(f"✅ Fetch complete. Found {len(new_articles)} new, valid articles.")
    return new_articles

def translate_articles_gemini(articles_to_translate):
    """Translates a list of articles using Gemini and updates their status."""
    if not articles_to_translate:
        logging.info("ℹ️ No articles are awaiting translation.")
        return

    logging.info(f"▶️ Step 2: Translating {len(articles_to_translate)} articles with Gemini...")
    items_to_translate = [{"id": i, "title": article["title"], "summary": article["summary"]} for i, article in enumerate(articles_to_translate)]
    prompt = f"STRICT INSTRUCTION: Translate ONLY the 'title' and 'summary' fields of the following news articles into Kurdish Sorani (ckb). Follow these rules precisely:\n\n1.  Clean the Title: For the translated 'title', you MUST REMOVE any news source name or prefix (e.g., 'Reuters:', 'CNN reports', '- Associated Press'). The title should only be the core headline.\n\n2.  Bracket Proper Nouns: In BOTH the translated 'title' and 'summary', you MUST ENCLOSE all proper nouns (names of people, places, organizations, brands, etc.) in single parentheses. For example, 'Joe Biden' should become '(جۆ بایدن)' and 'Iraq' should become '(عێراق)'.\n\nThe output MUST be ONLY a valid JSON array of objects. The output structure must STRICTLY contain ONLY the 'id', 'title', and 'summary' fields. The translated text must REPLACE the original English text. DO NOT include any introductory text, concluding remarks, explanations, or any markdown formatting like ```json. Output the raw JSON array and nothing else.\n\nInput Data to Translate (JSON array):\n{json.dumps(items_to_translate, ensure_ascii=False)}"
    headers = {'Content-Type': 'application/json'}
    payload = {'contents': [{'parts': [{'text': prompt}]}]}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        json_text = response_data['candidates'][0]['content']['parts'][0]['text']
        cleaned_json = json_text.strip().lstrip("```json").rstrip("```").strip()
        translated_data = json.loads(cleaned_json)
        
        for item in translated_data:
            article_index = item['id']
            articles_to_translate[article_index]['title_ku'] = item['title']
            articles_to_translate[article_index]['summary_ku'] = item['summary']
            articles_to_translate[article_index]['status'] = 'translated'
            
        logging.info(f"✅ Translation complete. {len(translated_data)} articles updated to 'translated' status.")
    except (requests.exceptions.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        logging.error(f"Gemini translation failed: {e}")

def post_to_tumblr(client, article):
    """Posts a single article to Tumblr."""
    logging.info(f"▶️ Step 4: Attempting to post '{article['title_ku'][:30]}...' to Tumblr...")
    tags = [article['category_ku'], article['source']]
    post_id = None

    # --- Define the "Read More" link that only shows on the post's own page ---
    # We use double curly braces {{...}} so Python's f-string ignores them
    # and passes the single braces {...} to the Tumblr API.
    read_more_link_html = f'{{block:PermalinkPage}}<p style="text-align: left; margin-top: 15px;"><a href="{article["url"]}" target="_blank">درێژەی بابەت</a></p>{{/block:PermalinkPage}}'

    try:
        if article.get('urlToImage'):
            # Append the read more link to the caption
            caption_html = (
                f'<h5 class="card-title lh-base">{article["title_ku"]}</h5>'
                f'<p class="card-text text-muted">{article["summary_ku"]}</p>'
                f'{read_more_link_html}'
            )
            response = client.create_photo(TUMBLR_BLOG_NAME, state="published", tags=tags, source=article['urlToImage'], caption=caption_html, link=article['url'], format="html")
        else:
            # Append the read more link to the body
            body_html = (
                f'<p class="card-text text-muted">{article["summary_ku"]}</p>'
                f'{read_more_link_html}'
            )
            response = client.create_text(TUMBLR_BLOG_NAME, state="published", tags=tags, title=article['title_ku'], body=body_html, format="html")

        if 'id' in response:
            post_id = response['id']
            logging.info(f"  - API returned success with Post ID: {post_id}. Verifying...")
        else:
            logging.error("  - API call succeeded but returned no post ID. Post likely dropped.")
            return False

        time.sleep(3)
        verification = client.posts(TUMBLR_BLOG_NAME, id=post_id)

        if verification and 'posts' in verification and len(verification['posts']) > 0:
            logging.info(f"  - ✅ Verified! Post {post_id} is live on Tumblr.")
            return True
        else:
            logging.warning(f"  - VERIFICATION FAILED: Post {post_id} was not found. It was likely rate-limited.")
            return False

    except Exception as e:
        logging.error(f"An exception occurred during posting or verification: {e}")
        return False

# --- MAIN EXECUTION FLOW ---
if __name__ == "__main__":
    # --- NEW: Setup colorful logging ---
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a formatter for the file (no colors)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create a handler to write to script.log
    file_handler = logging.FileHandler("script.log")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Use coloredlogs to create a colorful handler for the console
    # The level and logger parameters ensure it attaches to our existing setup
    coloredlogs.install(level='INFO', logger=logger)

    logging.info("--- Script starting ---")

    selected_country = prompt_for_choice("Please choose a country:", COUNTRIES, 'us')
    logging.info(f"Configuration set for Country='{selected_country}'. Starting process...")

    try:
        tumblr_client = pytumblr.TumblrRestClient(TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN, TUMBLR_OAUTH_SECRET)
        tumblr_client.info()
        logging.info("✅ Tumblr client authenticated successfully.")
    except Exception as e:
        logging.error(f"Could not authenticate with Tumblr. Check your API keys. Details: {e}")
        exit()

    for category_code, category_config in CATEGORIES.items():
        category_name = category_config['name']
        logging.info(f"\n--- Processing Category: {category_name} ({category_code}) ---")

        all_articles = load_existing_news(OUTPUT_FILE)
        
        newly_fetched = fetch_and_filter_news(selected_country, category_code, category_config, all_articles)
        if newly_fetched:
            all_articles.extend(newly_fetched)
            save_all_news(OUTPUT_FILE, all_articles)
        
        articles_to_translate = [a for a in all_articles if a.get('category') == category_code and a.get('status') == 'fetched']
        if articles_to_translate:
            translate_articles_gemini(articles_to_translate)
            save_all_news(OUTPUT_FILE, all_articles)
        else:
            logging.info("ℹ️ No new articles to translate for this category.")

        articles_to_post = [a for a in all_articles if a.get('category') == category_code and a.get('status') == 'translated']
        
        if articles_to_post:
            logging.info(f"▶️ Step 3: Sorting {len(articles_to_post)} translated articles by newest first...")
            articles_to_post.sort(key=lambda x: x['publishedAt'], reverse=True)

            for article in articles_to_post:
                success = post_to_tumblr(tumblr_client, article)
                if success:
                    article['status'] = 'posted'
                    save_all_news(OUTPUT_FILE, all_articles)
                
                logging.info("  - Pausing for 15 seconds before next post...")
                time.sleep(15)
        else:
            logging.info("ℹ️ No new articles to post for this category.")

        logging.info(f"--- Category '{category_name}' complete. Pausing for 60 seconds... ---")
        time.sleep(60)

    logging.info("\n✅ All categories have been processed. Script finished.")