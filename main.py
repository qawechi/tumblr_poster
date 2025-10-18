# main.py
import json
import requests
import pytumblr
from datetime import datetime
from zoneinfo import ZoneInfo
import time

# Import settings from the config file
from config import (
    NEWS_API_KEY, GEMINI_API_URL, NEWS_API_BASE_URL, OUTPUT_FILE,
    COUNTRIES, CATEGORIES, KURDISH_CATEGORY_MAP, TIMEZONE,
    TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN,
    TUMBLR_OAUTH_SECRET, TUMBLR_BLOG_NAME
)

def prompt_for_choice(prompt_message, options, default_key=None):
    """Prompts the user to select an option from a list."""
    print(prompt_message)
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
    # MODIFIED: More descriptive save message
    print(f"💾 Progress saved. Total articles in '{file_path}': {len(all_articles)}")

def fetch_and_filter_news(country, category_code, category_config, existing_articles):
    """Fetches news based on the dynamic config for each category."""
    print(f"▶️ Step 1: Fetching latest news for '{category_config['name']}'...")
    
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
        print(f"❌ ERROR: News API request failed: {e}")
        return []

    if data.get('status') != 'ok':
        print(f"❌ ERROR: News API returned status: {data.get('message', 'Unknown Error')}")
        return []

    existing_urls = {article['url'] for article in existing_articles}
    new_articles = []
    
    kurdish_category = KURDISH_CATEGORY_MAP.get(category_code, "گشتی")

    for article in data.get('articles', []):
        if not article.get('url') or article['url'] in existing_urls:
            continue

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
            "urlToImage": article.get('urlToImage', ''),
            # MODIFIED: Store original timestamp for sorting
            "publishedAt": article['publishedAt'],
            "title_ku": "",
            "summary_ku": "",
            "category_ku": kurdish_category,
            # MODIFIED: Add initial status for tracking
            "status": "fetched"
        })
    
    print(f"✅ Fetch complete. Found {len(new_articles)} new articles.")
    return new_articles

def translate_articles_gemini(articles_to_translate):
    """Translates a list of articles using Gemini and updates their status."""
    if not articles_to_translate:
        print("ℹ️ No articles are awaiting translation.")
        return

    print(f"▶️ Step 2: Translating {len(articles_to_translate)} articles with Gemini...")
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
            # MODIFIED: Update the original article object directly
            articles_to_translate[article_index]['title_ku'] = item['title']
            articles_to_translate[article_index]['summary_ku'] = item['summary']
            articles_to_translate[article_index]['status'] = 'translated' # Update status
            
        print(f"✅ Translation complete. {len(translated_data)} articles updated to 'translated' status.")
    except (requests.exceptions.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"❌ ERROR: Gemini translation failed: {e}")

def post_to_tumblr(client, article):
    """Posts a single article to Tumblr."""
    print(f"▶️ Step 4: Attempting to post '{article['title_ku'][:30]}...' to Tumblr...")
    tags = [article['category_ku'], article['source']]
    post_id = None
    try:
        if article.get('urlToImage'):
            caption_html = (f'<h5 class="card-title lh-base">{article["title_ku"]}</h5><p class="card-text text-muted">{article["summary_ku"]}</p>')
            response = client.create_photo(TUMBLR_BLOG_NAME, state="published", tags=tags, source=article['urlToImage'], caption=caption_html, link=article['url'], format="html")
        else:
            body_html = f'<p class="card-text text-muted">{article["summary_ku"]}</p>'
            response = client.create_text(TUMBLR_BLOG_NAME, state="published", tags=tags, title=article['title_ku'], body=body_html, format="html")
        
        if 'id' in response:
            post_id = response['id']
            print(f"  - API returned success with Post ID: {post_id}. Verifying...")
        else:
            print("  - ❌ ERROR: API call succeeded but returned no post ID. Post likely dropped.")
            return False

        time.sleep(3)
        verification = client.posts(TUMBLR_BLOG_NAME, id=post_id)
        
        if verification and 'posts' in verification and len(verification['posts']) > 0:
            print(f"  - ✅ Verified! Post {post_id} is live on Tumblr.")
            return True
        else:
            print(f"  - ❌ VERIFICATION FAILED: Post {post_id} was not found. It was likely rate-limited.")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: An exception occurred during posting or verification: {e}")
        return False

# --- MAIN EXECUTION FLOW ---
if __name__ == "__main__":
    selected_country = prompt_for_choice("Please choose a country:", COUNTRIES, 'us')
    print(f"\n✅ Configuration set for Country='{selected_country}'. Starting process...\n")

    try:
        tumblr_client = pytumblr.TumblrRestClient(TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_OAUTH_TOKEN, TUMBLR_OAUTH_SECRET)
        tumblr_client.info()
        print("✅ Tumblr client authenticated successfully.")
    except Exception as e:
        print(f"❌ ERROR: Could not authenticate with Tumblr. Check your API keys. Details: {e}")
        exit()

    for category_code, category_config in CATEGORIES.items():
        category_name = category_config['name']
        print(f"\n--- Processing Category: {category_name} ({category_code}) ---")

        # Load all articles from the database file
        all_articles = load_existing_news(OUTPUT_FILE)
        
        # --- Stage 1: FETCH ---
        newly_fetched = fetch_and_filter_news(selected_country, category_code, category_config, all_articles)
        if newly_fetched:
            all_articles.extend(newly_fetched)
            save_all_news(OUTPUT_FILE, all_articles)
        
        # --- Stage 2: TRANSLATE ---
        articles_to_translate = [a for a in all_articles if a.get('category') == category_code and a.get('status') == 'fetched']
        if articles_to_translate:
            translate_articles_gemini(articles_to_translate)
            save_all_news(OUTPUT_FILE, all_articles) # Save status changes
        else:
            print("ℹ️ No new articles to translate for this category.")

        # --- Stage 3 & 4: SORT and POST ---
        articles_to_post = [a for a in all_articles if a.get('category') == category_code and a.get('status') == 'translated']
        
        if articles_to_post:
            # MODIFIED: Sort articles by newest first before posting
            print(f"▶️ Step 3: Sorting {len(articles_to_post)} translated articles by newest first...")
            articles_to_post.sort(key=lambda x: x['publishedAt'], reverse=True)

            for article in articles_to_post:
                success = post_to_tumblr(tumblr_client, article)
                if success:
                    # MODIFIED: Update status to 'posted' and save progress immediately
                    article['status'] = 'posted'
                    save_all_news(OUTPUT_FILE, all_articles)
                
                # Pause between each post
                print("  - Pausing for 15 seconds before next post...")
                time.sleep(15)
        else:
            print("ℹ️ No new articles to post for this category.")

        print(f"\n--- Category '{category_name}' complete. Pausing for 60 seconds... ---")
        time.sleep(60)

    print("\n\n✅ All categories have been processed. Script finished.")