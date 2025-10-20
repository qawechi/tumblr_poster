# setup.py
import os
import pytumblr
from urllib.parse import urlparse
from requests_oauthlib import OAuth1Session
from dotenv import set_key, find_dotenv

def load_and_clean_env(file_path='.env'):
    """Loads and cleans variables from the .env file."""
    config = {}
    if not os.path.exists(file_path): return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip().strip('"').strip("'")
    return config

def authorize_and_get_tokens(consumer_key, consumer_secret, env_file_path):
    """Handles the entire OAuth1 flow and saves tokens to the .env file."""
    print("\n   - Starting Tumblr authorization...")
    request_token_url = 'https://www.tumblr.com/oauth/request_token'
    oauth_session = OAuth1Session(client_key=consumer_key, client_secret=consumer_secret, callback_uri='https://www.example.com')

    try:
        fetch_response = oauth_session.fetch_request_token(request_token_url)
        resource_owner_key = fetch_response.get('oauth_token')
        resource_owner_secret = fetch_response.get('oauth_token_secret')
    except Exception as e:
        print(f"   - ❌ ERROR: Could not get request token from Tumblr. Check your Consumer Key/Secret. Details: {e}")
        return None, None

    base_authorization_url = 'https://www.tumblr.com/oauth/authorize'
    authorization_url = oauth_session.authorization_url(base_authorization_url)

    print("\n   --- ACTION REQUIRED ---")
    print(f"   1. Go to this URL in your browser:\n\n      {authorization_url}\n")
    print("   2. Click 'Allow'. You'll be redirected to a non-working 'example.com' page.")
    print("   3. Copy the ENTIRE URL from your browser's address bar and paste it below.")
    print("   -----------------------\n")
    
    redirected_url = input("   - Paste the full redirected URL here: ").strip()

    try:
        oauth_response = oauth_session.parse_authorization_response(redirected_url)
        verifier = oauth_response.get('oauth_verifier')

        access_token_url = 'https://www.tumblr.com/oauth/access_token'
        final_session = OAuth1Session(
            client_key=consumer_key, client_secret=consumer_secret,
            resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret,
            verifier=verifier
        )
        final_credentials = final_session.fetch_access_token(access_token_url)
        
        oauth_token = final_credentials.get('oauth_token')
        oauth_secret = final_credentials.get('oauth_token_secret')

        set_key(env_file_path, "TUMBLR_OAUTH_TOKEN", oauth_token)
        set_key(env_file_path, "TUMBLR_OAUTH_SECRET", oauth_secret)
        
        print("\n   - ✅ Success! OAuth tokens have been automatically saved to your .env file.")
        return oauth_token, oauth_secret
        
    except Exception as e:
        print(f"\n   - ❌ ERROR: Could not parse the URL or get the final token. Please try again. Details: {e}")
        return None, None

def post_setup_confirmation(config):
    """Posts a confirmation message to the Tumblr blog."""
    print("\n   - Attempting to post a confirmation message to your blog...")
    try:
        client = pytumblr.TumblrRestClient(
            config.get("TUMBLR_CONSUMER_KEY"), config.get("TUMBLR_CONSUMER_SECRET"),
            config.get("TUMBLR_OAUTH_TOKEN"), config.get("TUMBLR_OAUTH_SECRET"),
        )
        response = client.create_text(
            config.get("TUMBLR_BLOG_NAME"), state="published",
            title="✅ Setup Complete!",
            body="This blog is now successfully connected to the automated DANA news script."
        )
        if 'id' in response:
            print("   - ✅ Success! Confirmation post published to your Tumblr.")
        else:
            print(f"   - ⚠️ Warning: Could not post confirmation message. Response: {response}")
    except Exception as e:
        print(f"   - ⚠️ Warning: Failed to post confirmation. Error: {e}")

def setup_config():
    """Main function to guide user through setting up the .env file."""
    env_file_path = find_dotenv()
    if not env_file_path:
        env_file_path = '.env'
        open(env_file_path, 'w').close()

    config = load_and_clean_env(env_file_path)

    print("\n[STEP 1] General Configuration")
    required_keys = [
        'NEWS_API_KEYS', 'GEMINI_API_KEY', 'TUMBLR_CONSUMER_KEY',
        'TUMBLR_CONSUMER_SECRET', 'TUMBLR_BLOG_NAME',
        'CONTACT_EMAIL', 'BLOG_URL',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'
    ]
    
    for key in required_keys:
        if not config.get(key):
            prompt_message = f"   - {key} is missing. Please enter it: "
            if key == 'NEWS_API_KEYS':
                prompt_message = "   - NEWS_API_KEYS is missing. Please enter your comma-separated keys: "
            
            config[key] = input(prompt_message).strip()
            set_key(env_file_path, key, config[key])
        else:
            print(f"   - Found existing {key}.")

    # New unattended execution settings
    if not config.get("TARGET_COUNTRY"):
        config["TARGET_COUNTRY"] = input("   - Enter the default Target Country code (e.g., 'us'): ").strip().lower() or "us"
        set_key(env_file_path, "TARGET_COUNTRY", config["TARGET_COUNTRY"])
    if not config.get("TARGET_CATEGORY"):
        config["TARGET_CATEGORY"] = input("   - Enter the default Target Category ('all' or a specific one): ").strip().lower() or "all"
        set_key(env_file_path, "TARGET_CATEGORY", config["TARGET_CATEGORY"])
    if config.get("USE_SELENIUM_SCRAPING") is None:
        selenium_choice = input("   - Enable advanced (slower) Selenium scraping? (y/n, default is n): ").strip().lower()
        use_selenium = "true" if selenium_choice.startswith('y') else "false"
        config["USE_SELENIUM_SCRAPING"] = use_selenium
        set_key(env_file_path, "USE_SELENIUM_SCRAPING", config["USE_SELENIUM_SCRAPING"])


    print("\n[STEP 2] Checking Tumblr Authorization")
    if config.get('TUMBLR_OAUTH_TOKEN') and config.get('TUMBLR_OAUTH_SECRET'):
        print("   - Found existing OAuth tokens. Skipping authorization.")
    else:
        token, secret = authorize_and_get_tokens(
            config.get("TUMBLR_CONSUMER_KEY"),
            config.get("TUMBLR_CONSUMER_SECRET"),
            env_file_path
        )
        if token and secret:
            config['TUMBLR_OAUTH_TOKEN'] = token
            config['TUMBLR_OAUTH_SECRET'] = secret
            post_setup_confirmation(config)

if __name__ == "__main__":
    setup_config()