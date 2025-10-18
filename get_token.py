# get_token.py
import pytumblr
from urllib.parse import urlparse, parse_qs
from requests_oauthlib import OAuth1Session

# --- Step 1: Automatically import your keys from config.py ---
try:
    from config import TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET
except ImportError:
    print("❌ ERROR: Could not import keys from config.py. Make sure the file exists.")
    exit()

if not TUMBLR_CONSUMER_KEY or not TUMBLR_CONSUMER_SECRET:
    print("❌ ERROR: Your TUMBLR_CONSUMER_KEY or TUMBLR_CONSUMER_SECRET is missing from the .env file.")
    exit()

print("✅ Successfully loaded Consumer Key from your config.")
print("-" * 30)

# --- Step 2: Get request token ---
request_token_url = 'https://www.tumblr.com/oauth/request_token'
oauth_session = OAuth1Session(client_key=TUMBLR_CONSUMER_KEY, client_secret=TUMBLR_CONSUMER_SECRET)
fetch_response = oauth_session.fetch_request_token(request_token_url)

resource_owner_key = fetch_response.get('oauth_token')
resource_owner_secret = fetch_response.get('oauth_token_secret')

# --- Step 3: Get the authorization URL to visit ---
base_authorization_url = 'https://www.tumblr.com/oauth/authorize'
authorization_url = oauth_session.authorization_url(base_authorization_url)

print("1. Go to this URL in your browser:\n")
print(authorization_url)
print("\n2. Click 'Allow' in your browser.")
print("3. You will be redirected to 'example.com'. Copy the ENTIRE URL from your browser's address bar.")
print("-" * 30)

# --- Step 4: Paste the redirected URL to extract the final tokens ---
redirected_url = input("Paste the full redirected URL here: ")

# Parse the URL to get the necessary parameters
try:
    oauth_response = oauth_session.parse_authorization_response(redirected_url)
    verifier = oauth_response.get('oauth_verifier')

    # --- Step 5: Exchange the verifier for the final access token and secret ---
    access_token_url = 'https://www.tumblr.com/oauth/access_token'
    oauth_session = OAuth1Session(
        client_key=TUMBLR_CONSUMER_KEY,
        client_secret=TUMBLR_CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier
    )
    final_credentials = oauth_session.fetch_access_token(access_token_url)
    
    print("\n✅ Success! Here are your final keys:\n")
    print(f"TUMBLR_OAUTH_TOKEN=\"{final_credentials.get('oauth_token')}\"")
    print(f"TUMBLR_OAUTH_SECRET=\"{final_credentials.get('oauth_token_secret')}\"")
    print("\nCopy these two lines into your .env file.")

except Exception as e:
     print(f"\n❌ ERROR: Could not parse the URL. Make sure you copied the full URL. Details: {e}")