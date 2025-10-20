import psycopg2
import sys
# Import your database URL from your existing config.py
from config import DATABASE_URL 

# --- Configuration Constants ---
STATUS_POSTED = 'posted'

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        if not DATABASE_URL:
            print("❌ ERROR: DATABASE_URL not set in config.py. Exiting.")
            sys.exit(1)
        # Use autocommit=False to manage transactions manually
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"❌ ERROR: Could not connect to the database. Check DATABASE_URL and credentials. Error: {e}")
        sys.exit(1)

def reset_database(conn):
    """
    Resets the database by:
    1. Deleting all articles EXCEPT those with STATUS_POSTED.
    2. Clearing the category_cooldowns table entirely.
    """
    print("\n--- ⚠️ STARTING DATABASE RESET (PRESERVING POSTED ARTICLES) ⚠️ ---")
    
    deleted_count = 0
    
    try:
        with conn.cursor() as cursor:
            
            # 1. DELETE ALL UNPOSTED ARTICLES
            print(f"1. Deleting articles with status NOT equal to '{STATUS_POSTED}'...")
            
            # Delete all rows where status is NOT 'posted'
            cursor.execute("DELETE FROM articles WHERE status != %s", (STATUS_POSTED,))
            deleted_count = cursor.rowcount
            print(f"   -> Successfully deleted {deleted_count} unposted articles.")
            
            # 2. RESET CATEGORY COOLDOWNS
            print("2. Truncating 'category_cooldowns' table...")
            
            # TRUNCATE deletes all data and resets the table structure immediately
            cursor.execute("TRUNCATE TABLE category_cooldowns")
            print("   -> All category cooldowns have been reset.")
            
            # 3. COMMIT CHANGES
            conn.commit()
            
        print(f"\n--- ✅ DATABASE RESET COMPLETE ---")
        print(f"Total articles cleared from the processing queue: {deleted_count}")
        print("Your bot can now start fresh fetching new articles and categories.")

    except Exception as e:
        conn.rollback() # Revert changes if any operation fails
        print(f"❌ CRITICAL ERROR: Database reset failed. Changes rolled back. Error: {e}")
        sys.exit(1)


def main():
    try:
        with get_db_connection() as conn:
            
            print("=========================================================")
            print("  POSTGRESQL DATABASE RESET UTILITY")
            print("=========================================================")
            
            # Check the count of posted articles we are keeping for user confirmation
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM articles WHERE status = %s", (STATUS_POSTED,))
                posted_count = cursor.fetchone()[0]
            
            print(f"Found {posted_count} articles with status 'posted' that WILL BE PRESERVED.")

            response = input("\nCONFIRM: Do you want to proceed with the full database reset (clearing all unposted data)? (yes/no): ").strip().lower()

            if response == 'yes':
                reset_database(conn)
            else:
                print("\nDatabase reset cancelled. No changes were made.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()