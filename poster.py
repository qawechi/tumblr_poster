# telegram_test_poster.py
import os
import sys
import telegram
from telegram.error import TelegramError
from dotenv import load_dotenv
import asyncio  # <-- NEW: Import asyncio

# --- 1. Load Environment Variables ---
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- 2. Change the function to be asynchronous (async) ---
async def send_test_message():
    """Initializes the bot and sends a test message to the configured chat."""
    print("--- Telegram Test Poster Starting ---")

    # Check for credentials
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing from the .env file.")
        print("Please run setup.py or verify your .env file.")
        sys.exit(1)

    print(f"✅ Bot Token found. Target Chat ID: {TELEGRAM_CHAT_ID}")

    try:
        # Initialize the bot client
        # In modern ptb, the Bot object is the starting point for async calls
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        
        # --- NEW: Use 'await' for asynchronous calls ---
        bot_info = await bot.get_me() 
        print(f"✅ Bot successfully authenticated. Bot Username: @{bot_info.username}")
        
        # --- Test Message Content (HTML formatting is used) ---
        test_title = "✅ پەنجەرەی تاقیکردنەوە سەرکەوتوو بوو!"
        test_body = "ئەمە پۆستێکی تاقیکردنەوەیە بۆ پشتڕاستکردنەوەی کارکردنی بۆتی تەلەگرام."
        test_url = "https://www.google.com"
        
        message_text = (
            f"<b>{test_title}</b>\n\n"
            f"{test_body}\n\n"
            f'<a href="{test_url}">سەرچاوە: Google</a>\n\n'
            f"#تەلەگرام #بۆت #تازە"
        )

        # Send the message
        print(f"➡️ Attempting to send message to Chat ID: {TELEGRAM_CHAT_ID}")
        
        # --- NEW: Use 'await' for asynchronous calls ---
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message_text,
            parse_mode='HTML',
            disable_web_page_preview=True 
        )

        print("\n🎉 SUCCESS! Message should now be visible in your specified Telegram chat/channel.")
        
    except TelegramError as e:
        print(f"\n❌ TELEGRAM ERROR: Posting failed.")
        if "chat not found" in str(e):
            print("   - Issue: The TELEGRAM_CHAT_ID is likely incorrect or the bot is not an admin in the channel/group.")
        elif "forbidden" in str(e):
            print("   - Issue: The bot token is revoked, or the bot was blocked by the user/chat owner.")
        else:
            print(f"   - Details: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ GENERAL ERROR: An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # --- NEW: Run the asynchronous function synchronously ---
    asyncio.run(send_test_message())