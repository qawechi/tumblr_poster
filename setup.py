# setup.py
import os
import subprocess
from dotenv import load_dotenv, find_dotenv

def setup_config():
    """
    Checks for missing environment variables, prompts the user to enter them,
    and saves them to the .env file.
    """
    env_file = find_dotenv()
    if not env_file:
        open('.env', 'w').close() # Create the file if it doesn't exist
        env_file = find_dotenv()
        
    load_dotenv(env_file)

    print("\n[2/4] Checking existing configuration...")

    # Define the keys we need for basic operation
    required_keys = [
        'NEWS_API_KEY',
        'GEMINI_API_KEY',
        'TUMBLR_CONSUMER_KEY',
        'TUMBLR_CONSUMER_SECRET',
        'TUMBLR_BLOG_NAME'
    ]
    
    config = {}
    changes_made = False

    # Load existing values and ask for any that are missing
    for key in required_keys:
        value = os.getenv(key)
        if not value:
            value = input(f"   - {key} is missing. Enter it: ")
            changes_made = True
        else:
            print(f"      - Found existing {key}.")
        config[key] = value

    # Re-write the main config to the .env file
    with open(env_file, 'w') as f:
        f.write("# NewsAPI.org Key\n")
        f.write(f'NEWS_API_KEY="{config["NEWS_API_KEY"]}"\n\n')
        f.write("# Google Gemini API Key\n")
        f.write(f'GEMINI_API_KEY="{config["GEMINI_API_KEY"]}"\n\n')
        f.write("# Tumblr API Keys\n")
        f.write(f'TUMBLR_CONSUMER_KEY="{config["TUMBLR_CONSUMER_KEY"]}"\n')
        f.write(f'TUMBLR_CONSUMER_SECRET="{config["TUMBLR_CONSUMER_SECRET"]}"\n')
        f.write(f'TUMBLR_BLOG_NAME="{config["TUMBLR_BLOG_NAME"]}"\n')

    print("\n[3/4] Checking Tumblr authorization...")

    # Check for OAuth tokens
    oauth_token = os.getenv('TUMBLR_OAUTH_TOKEN')
    oauth_secret = os.getenv('TUMBLR_OAUTH_SECRET')

    if oauth_token and oauth_secret:
        print("      - Found existing OAuth tokens. Skipping authorization step.")
        # Append them back to the file since we rewrote it
        with open(env_file, 'a') as f:
            f.write("\n# Tumblr OAuth Tokens\n")
            f.write(f'TUMBLR_OAUTH_TOKEN="{oauth_token}"\n')
            f.write(f'TUMBLR_OAUTH_SECRET="{oauth_secret}"\n')
    else:
        print("      - OAuth tokens not found. Starting authorization process...\n")
        
        # Run get_token.py
        subprocess.run(['python', 'get_token.py'])
        
        print("\nThe script has printed your OAuth Token and Secret above.")
        print("Please copy and paste them here to complete the setup.\n")
        
        new_oauth_token = input("   - Paste the TUMBLR_OAUTH_TOKEN here: ").strip().strip('"')
        new_oauth_secret = input("   - Paste the TUMBLR_OAUTH_SECRET here: ").strip().strip('"')
        
        # Append the new tokens to the .env file
        with open(env_file, 'a') as f:
            f.write("\n# Tumblr OAuth Tokens\n")
            f.write(f'TUMBLR_OAUTH_TOKEN="{new_oauth_token}"\n')
            f.write(f'TUMBLR_OAUTH_SECRET="{new_oauth_secret}"\n')
        print("\n      - Tokens saved.")

if __name__ == "__main__":
    setup_config()