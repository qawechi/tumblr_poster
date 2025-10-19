# setup.py
import subprocess
import os
import pytumblr

def load_and_clean_env(file_path='.env'):
    config = {}
    if not os.path.exists(file_path): return {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip().strip('"').strip("'")
    return config

def post_setup_confirmation(config):
    print("\n      - Attempting to post a confirmation message...")
    try:
        client = pytumblr.TumblrRestClient(
            config.get("TUMBLR_CONSUMER_KEY"), config.get("TUMBLR_CONSUMER_SECRET"),
            config.get("TUMBLR_OAUTH_TOKEN"), config.get("TUMBLR_OAUTH_SECRET"),
        )
        response = client.create_text(
            config.get("TUMBLR_BLOG_NAME"), state="published",
            title="✅ Setup Complete!",
            body="This blog is now successfully connected to the automated news poster script."
        )
        if 'id' in response:
            print("      - ✅ Success! Confirmation post published.")
        else:
            print("      - ⚠️ Warning: Could not post confirmation message.")
    except Exception as e:
        print(f"      - ⚠️ Warning: Failed to post confirmation. Error: {e}")

def setup_config():
    env_file_path = '.env'
    config = load_and_clean_env(env_file_path)

    print("\n[2/4] Checking existing configuration...")

    # MODIFIED: Added CONTACT_EMAIL, BLOG_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    required_keys = [
        'NEWS_API_KEY', 'GEMINI_API_KEY', 'TUMBLR_CONSUMER_KEY',
        'TUMBLR_CONSUMER_SECRET', 'TUMBLR_BLOG_NAME',
        'CONTACT_EMAIL', 'BLOG_URL',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'
    ]
    
    for key in required_keys:
        if not config.get(key):
            config[key] = input(f"   - {key} is missing. Enter it: ").strip().strip('"')
        else:
            print(f"      - Found existing {key}.")

    if config.get("EMAIL_NOTIFICATIONS_ENABLED", "").lower() not in ['true', 'false']:
        config["EMAIL_NOTIFICATIONS_ENABLED"] = "true" if input("\nEnable email notifications? (y/n): ").lower().startswith('y') else "false"
    
    if config.get("EMAIL_NOTIFICATIONS_ENABLED") == "true":
        print("      - Email notifications are ENABLED.")
        for key in ["SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL"]:
            if not config.get(key):
                if key == "SENDER_PASSWORD": print("\n     IMPORTANT: Use an 'App Password' for Gmail/Outlook.")
                config[key] = input(f"     - Enter the {key}: ")
    
    # Writing configuration to .env file
    with open(env_file_path, 'w') as f:
        f.write(f'NEWS_API_KEY="{config.get("NEWS_API_KEY", "")}"\n')
        f.write(f'GEMINI_API_KEY="{config.get("GEMINI_API_KEY", "")}"\n')
        f.write(f'TUMBLR_CONSUMER_KEY="{config.get("TUMBLR_CONSUMER_KEY", "")}"\n')
        f.write(f'TUMBLR_CONSUMER_SECRET="{config.get("TUMBLR_CONSUMER_SECRET", "")}"\n')
        f.write(f'TUMBLR_BLOG_NAME="{config.get("TUMBLR_BLOG_NAME", "")}"\n\n')
        
        # NEW: Telegram Bot Settings
        f.write("# Telegram Bot Settings\n")
        f.write(f'TELEGRAM_BOT_TOKEN="{config.get("TELEGRAM_BOT_TOKEN", "")}"\n')
        f.write(f'TELEGRAM_CHAT_ID="{config.get("TELEGRAM_CHAT_ID", "")}"\n\n')

        f.write("# User-Agent Information\n")
        f.write(f'CONTACT_EMAIL="{config.get("CONTACT_EMAIL", "")}"\n')
        f.write(f'BLOG_URL="{config.get("BLOG_URL", "")}"\n\n')
        f.write("# Email Notification Settings\n")
        f.write(f'EMAIL_NOTIFICATIONS_ENABLED={config.get("EMAIL_NOTIFICATIONS_ENABLED", "false")}\n')
        f.write(f'SENDER_EMAIL="{config.get("SENDER_EMAIL", "")}"\n')
        f.write(f'SENDER_PASSWORD="{config.get("SENDER_PASSWORD", "")}"\n')
        f.write(f'RECIPIENT_EMAIL="{config.get("RECIPIENT_EMAIL", "")}"\n')

    print("\n[3/4] Checking Tumblr authorization...")

    if config.get('TUMBLR_OAUTH_TOKEN') and config.get('TUMBLR_OAUTH_SECRET'):
        print("      - Found existing OAuth tokens. Skipping authorization.")
        with open(env_file_path, 'a') as f:
            f.write("\n# Tumblr OAuth Tokens\n")
            f.write(f'TUMBLR_OAUTH_TOKEN="{config.get("TUMBLR_OAUTH_TOKEN")}"\n')
            f.write(f'TUMBLR_OAUTH_SECRET="{config.get("TUMBLR_OAUTH_SECRET")}"\n')
    else:
        print("      - OAuth tokens not found. Starting authorization...\n")
        subprocess.run(['python', 'get_token.py'])
        new_oauth_token = input("\n   - Paste the TUMBLR_OAUTH_TOKEN here: ").strip().strip('"')
        new_oauth_secret = input("   - Paste the TUMBLR_OAUTH_SECRET here: ").strip().strip('"')
        config['TUMBLR_OAUTH_TOKEN'] = new_oauth_token
        config['TUMBLR_OAUTH_SECRET'] = new_oauth_secret
        with open(env_file_path, 'a') as f:
            f.write("\n# Tumblr OAuth Tokens\n")
            f.write(f'TUMBLR_OAUTH_TOKEN="{new_oauth_token}"\n')
            f.write(f'TUMBLR_OAUTH_SECRET="{new_oauth_secret}"\n')
        print("\n      - Tokens saved.")
        post_setup_confirmation(config)

if __name__ == "__main__":
    setup_config()