# prepare_database.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

def prepare_and_migrate():
    """
    A one-time script to:
    1. Ensure tables exist in the PostgreSQL database.
    2. Migrate data from a local SQLite DB to PostgreSQL.
    """
    print("--- Database Preparation & Migration Tool ---")
    print("This script will prepare your online database and migrate local data.")

    # --- Load Configuration ---
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLITE_DB_PATH = os.path.join('data', 'news_bot.db')

    # --- Pre-flight Checks ---
    if not DATABASE_URL:
        print("\n❌ FATAL ERROR: DATABASE_URL not found in your .env file. Halting.")
        return
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"\n❌ FATAL ERROR: Local database file not found at '{SQLITE_DB_PATH}'.")
        print("   If this is a fresh install with no old data, you don't need to run this script.")
        print("   The main bot will create the tables for you. Halting.")
        return

    pg_conn = None
    sqlite_conn = None

    try:
        # --- [STEP 1] Connect to Databases ---
        print("\n[1/4] Connecting to databases...")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        print("  - ✅ Connected to local SQLite database.")
        
        pg_conn = psycopg2.connect(DATABASE_URL)
        print("  - ✅ Connected to online PostgreSQL database.")

        # --- [STEP 2] Create Tables in PostgreSQL (Safely) ---
        print("\n[2/4] Ensuring online tables exist...")
        with pg_conn.cursor() as cursor:
            # Table for articles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    url TEXT PRIMARY KEY, 
                    title TEXT, 
                    summary TEXT, 
                    category TEXT, 
                    source TEXT, 
                    urlToImage TEXT, 
                    publishedAt TEXT, 
                    status TEXT DEFAULT 'fetched', 
                    title_ku TEXT, 
                    summary_ku TEXT, 
                    category_ku TEXT, 
                    generated_tags TEXT
                )
            ''')
            # Table for cooldowns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_cooldowns (
                    category_code TEXT PRIMARY KEY, 
                    last_fetched TIMESTAMPTZ NOT NULL
                )
            ''')
        pg_conn.commit()
        print("  - ✅ Tables 'articles' and 'category_cooldowns' are ready.")

        # --- [STEP 3] Migrate Articles ---
        print("\n[3/4] Migrating articles...")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM articles")
        articles = sqlite_cursor.fetchall()
        
        if not articles:
            print("  - ℹ️ No articles found in local database to migrate.")
        else:
            print(f"  - Found {len(articles)} articles in local DB.")
            articles_to_insert = [tuple(article) for article in articles]
            with pg_conn.cursor() as pg_cursor:
                execute_values(
                    pg_cursor,
                    """
                    INSERT INTO articles (url, title, summary, category, source, urlToImage, publishedAt, status, title_ku, summary_ku, category_ku, generated_tags)
                    VALUES %s
                    ON CONFLICT (url) DO NOTHING;
                    """,
                    articles_to_insert
                )
            pg_conn.commit()
            print(f"  - ✅ Successfully migrated {len(articles)} articles.")

        # --- [STEP 4] Migrate Cooldowns ---
        print("\n[4/4] Migrating category cooldowns...")
        sqlite_cursor.execute("SELECT * FROM category_cooldowns")
        cooldowns = sqlite_cursor.fetchall()
        
        if not cooldowns:
            print("  - ℹ️ No cooldown records found to migrate.")
        else:
            print(f"  - Found {len(cooldowns)} cooldown records.")
            cooldowns_to_insert = [tuple(cooldown) for cooldown in cooldowns]
            with pg_conn.cursor() as pg_cursor:
                execute_values(
                    pg_cursor,
                    """
                    INSERT INTO category_cooldowns (category_code, last_fetched)
                    VALUES %s
                    ON CONFLICT (category_code) DO NOTHING;
                    """,
                    cooldowns_to_insert
                )
            pg_conn.commit()
            print(f"  - ✅ Successfully migrated {len(cooldowns)} cooldown records.")
        
        print("\n---  Migration Complete! ---")
        print("Your online database is now ready. You can run the main bot using 'start.bat'.")

    except psycopg2.Error as e:
        print(f"\n❌ DATABASE ERROR: A PostgreSQL error occurred: {e}")
        if pg_conn:
            pg_conn.rollback() # Roll back any partial changes
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: An error occurred: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if pg_conn:
            pg_conn.close()
        print("\nAll database connections closed.")

if __name__ == "__main__":
    prepare_and_migrate()