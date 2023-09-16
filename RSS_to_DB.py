import sqlite3

# Database file name
DB_FILE = 'archive.db'

# RSS URLs file name
RSS_URLS_FILE = 'rss_urls'

def create_database():
    """Create the SQLite database and tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create a table for storing RSS feed URLs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rss_feeds (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE
        )
    ''')

    conn.commit()
    conn.close()

def read_rss_urls_from_file():
    """Read RSS feed URLs from the "rss_urls" file."""
    try:
        with open(RSS_URLS_FILE, 'r') as f:
            rss_feed_urls = f.read().splitlines()
        return rss_feed_urls
    except FileNotFoundError:
        print(f'Error: {RSS_URLS_FILE} not found.')
        return []

def insert_rss_urls_to_database(rss_feed_urls):
    """Insert RSS feed URLs into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for url in rss_feed_urls:
        try:
            cursor.execute('INSERT OR IGNORE INTO rss_feeds (url) VALUES (?)', (url,))
        except sqlite3.IntegrityError:
            # Ignore duplicate entries
            pass

    conn.commit()
    conn.close()

def main():
    """Main function to transfer RSS feed URLs from the file to the database."""
    create_database()

    # Read RSS feed URLs from the file
    rss_feed_urls = read_rss_urls_from_file()

    if rss_feed_urls:
        # Insert RSS feed URLs into the database
        insert_rss_urls_to_database(rss_feed_urls)
        print(f'Successfully transferred {len(rss_feed_urls)} RSS feed URLs to the database.')
    else:
        print('No RSS feed URLs found in the file.')

if __name__ == '__main__':
    main()
