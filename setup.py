# setup.py
import subprocess
import os
import pytumblr  # NEW: Import pytumblr to post the confirmation

def load_and_clean_env(file_path='.env'):
    """
    Manually reads a .env file to avoid parsing errors.
    Returns a dictionary of cleaned key-value pairs.
    """
    config = {}
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            config[key] = value
            
    return config

# --- NEW: Function to post confirmation message ---
def post_setup_confirmation(config):
    """Posts a confirmation message to Tumblr after initial setup."""
    print("\n      - Attempting to post a confirmation message to your blog...")
    try:
        # Initialize the client with the just-provided credentials
        client = pytumblr.TumblrRestClient(
            config.get("TUMBLR_CONSUMER_KEY"),
            config.get("TUMBLR_CONSUMER_SECRET"),
            config.get("TUMBLR_OAUTH_TOKEN"),
            config.get("TUMBLR_OAUTH_SECRET"),
        )
        response = client.create_text(
            config.get("TUMBLR_BLOG_NAME"),
            state="published",
            title="✅ Setup Complete!",
            body="This blog is now successfully connected to the automated news poster script."
        )
        if 'id' in response:
            print("      - ✅ Success! A confirmation post has been published to your blog.")
        else:
            print("      - ⚠️ Warning: Could not post a confirmation message. Please check your blog manually.")
    except Exception as e:
        print(f"      - ⚠️ Warning: Failed to post confirmation. Error: {e}")

def setup_config():
    """
    Checks for missing environment variables, prompts the user,
    and saves them to a clean .env file.
    """
    env_file_path = '.env'
    config = load_and_clean_env(env_file_path)

    print("\n[2/4] Checking existing configuration...")

    required_keys = [
        'NEWS_API_KEY', 'GEMINI_API_KEY', 'TUMBLR_CONSUMER_KEY',
        'TUMBLR_CONSUMER_SECRET', 'TUMBLR_BLOG_NAME'
    ]
    
    for key in required_keys:
        if key not in config or not config[key]:
            value = input(f"   - {key} is missing. Enter it: ").strip().strip('"')
            config[key] = value
        else:
            print(f"      - Found existing {key}.")

    # Email configuration logic
    enable_email_choice = config.get("EMAIL_NOTIFICATIONS_ENABLED", "").lower()
    if enable_email_choice not in ['true', 'false']:
        choice = input("\nDo you want to enable email notifications? (yes/no): ").lower()
        config["EMAIL_NOTIFICATIONS_ENABLED"] = "true" if choice.startswith('y') else "false"
    
    if config.get("EMAIL_NOTIFICATIONS_ENABLED") == "true":
        print("      - Email notifications are ENABLED.")
        for key in ["SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL"]:
            if not config.get(key):
                if key == "SENDER_PASSWORD":
                    print("\n     IMPORTANT: For Gmail/Outlook, you must use an 'App Password'.")
                config[key] = input(f"     - Enter the {key}: ")
    else:
        print("      - Email notifications are DISABLED.")

    # Re-write the main config to the .env file cleanly
    with open(env_file_path, 'w') as f:
        f.write("# NewsAPI.org Key\n")
        f.write(f'NEWS_API_KEY="{config.get("NEWS_API_KEY", "")}"\n\n')
        f.write("# Google Gemini API Key\n")
        f.write(f'GEMINI_API_KEY="{config.get("GEMINI_API_KEY", "")}"\n\n')
        f.write("# Tumblr API Keys\n")
        f.write(f'TUMBLR_CONSUMER_KEY="{config.get("TUMBLR_CONSUMER_KEY", "")}"\n')
        f.write(f'TUMBLR_CONSUMER_SECRET="{config.get("TUMBLR_CONSUMER_SECRET", "")}"\n')
        f.write(f'TUMBLR_BLOG_NAME="{config.get("TUMBLR_BLOG_NAME", "")}"\n\n')
        f.write("# Email Notification Settings\n")
        f.write(f'EMAIL_NOTIFICATIONS_ENABLED={config.get("EMAIL_NOTIFICATIONS_ENABLED", "false")}\n')
        f.write(f'SENDER_EMAIL="{config.get("SENDER_EMAIL", "")}"\n')
        f.write(f'SENDER_PASSWORD="{config.get("SENDER_PASSWORD", "")}"\n')
        f.write(f'RECIPIENT_EMAIL="{config.get("RECIPIENT_EMAIL", "")}"\n')

    print("\n[3/4] Checking Tumblr authorization...")

    if config.get('TUMBLR_OAUTH_TOKEN') and config.get('TUMBLR_OAUTH_SECRET'):
        print("      - Found existing OAuth tokens. Skipping authorization step.")
        with open(env_file_path, 'a') as f:
            f.write("\n# Tumblr OAuth Tokens\n")
            f.write(f'TUMBLR_OAUTH_TOKEN="{config.get("TUMBLR_OAUTH_TOKEN")}"\n')
            f.write(f'TUMBLR_OAUTH_SECRET="{config.get("TUMBLR_OAUTH_SECRET")}"\n')
    else:
        print("      - OAuth tokens not found. Starting authorization process...\n")
        subprocess.run(['python', 'get_token.py'])
        
        print("\nThe script has printed your OAuth Token and Secret above.")
        print("Please copy and paste them here to complete the setup.\n")
        
        new_oauth_token = input("   - Paste the TUMBLR_OAUTH_TOKEN here: ").strip().strip('"')
        new_oauth_secret = input("   - Paste the TUMBLR_OAUTH_SECRET here: ").strip().strip('"')
        
        # MODIFIED: Update the in-memory config for immediate use
        config['TUMBLR_OAUTH_TOKEN'] = new_oauth_token
        config['TUMBLR_OAUTH_SECRET'] = new_oauth_secret
        
        with open(env_file_path, 'a') as f:
            f.write("\n# Tumblr OAuth Tokens\n")
            f.write(f'TUMBLR_OAUTH_TOKEN="{new_oauth_token}"\n')
            f.write(f'TUMBLR_OAUTH_SECRET="{new_oauth_secret}"\n')
        print("\n      - Tokens saved.")
        
        # MODIFIED: Post the confirmation message after saving tokens
        post_setup_confirmation(config)

if __name__ == "__main__":
    setup_config()