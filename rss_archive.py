#!/usr/bin/python

import feedparser
import time
import os
import requests
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
import tldextract
import traceback
import concurrent.futures
import tzlocal
import random
from tqdm import tqdm

# Constants
DB_FILE = 'archive.db'
MAX_RETRIES = 3
RETRY_DELAY = 7
MAX_LINK_ARCHIVAL_TIME = 200  # 5 minutes

# ANSI escape codes for text color
GREEN = '\033[32m'
RED = '\033[31m'
YELLOW = '\033[33m'
MAGENTA = '\033[35m'
RESET = '\033[0m'

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

def create_archive_table():
    """Create a table for storing archived links with TLD."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archived_links (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            tld TEXT  -- Add a column for TLD
        )
    ''')

    conn.commit()
    conn.close()

def timestamp():
    """Get the current timestamp in a readable format with blue color."""
    local_timezone = tzlocal.get_localzone()
    current_time = datetime.now(local_timezone).strftime("%H:%M:S %Z")
    return f'\033[34m{current_time}\033[0m'

def get_rss_feed_urls_from_file():
    """Get the list of RSS feed URLs from the 'rss_urls' file."""
    rss_feed_urls = []
    try:
        with open('rss_urls', 'r') as file:
            rss_feed_urls = [line.strip() for line in file]
    except FileNotFoundError:
        print("RSS feed URLs file 'rss_urls' not found.")
    return rss_feed_urls

def is_link_archived(link):
    """Check if a link is already archived on the Wayback Machine."""
    availability_url = f'https://archive.org/wayback/available?url={link}'
    response = requests.get(availability_url)

    if response.status_code == 200:
        data = response.json()
        return 'archived_snapshots' in data and len(data['archived_snapshots']) > 0
    else:
        print(f'{timestamp()} {RED}[ERROR CHECKING AVAILABILITY AT IA]: {RESET}{link}')
        return False

def format_request_error(e):
    error_lines = traceback.format_exception(type(e), e, e.__traceback__)
    formatted_error = "\n".join([
        f"{RED}[REQUEST ERROR]:",
        f"    {RESET}{error_lines[-2]}",
        f"    {RESET}{error_lines[-1]}",
        f"{RESET}"
    ])
    return formatted_error

def archive_link(link):
    """Archive a link to the Wayback Machine with retry mechanism."""
    for attempt in range(MAX_RETRIES):
        try:
            # Extract the TLD using tldextract
            ext = tldextract.extract(link)
            tld = '.'.join(part for part in ext if part)

            # Check if the link is already archived in the database
            if is_link_in_database(link):
                print(f'{timestamp()} {YELLOW}[SKIP - ALREADY ARCHIVED LOCALLY]: {RESET}{link}')
                return True

            # Check if the link is already archived on the Wayback Machine
            if is_link_archived(link):
                print(f'{timestamp()} {YELLOW}[SKIP - ALREADY ARCHIVED ON WAYBACK MACHINE]: {RESET}{link}')
                insert_archived_link(link, tld)
                return True

            # Save the link to the Internet Archive
            wayback_machine_url = 'https://web.archive.org/save/' + link
            response = requests.get(wayback_machine_url)

            if response.status_code == 200:
                print(f'{timestamp()} {GREEN}[SUCCESSFULLY ARCHIVED]: {RESET}{link}')
                insert_archived_link(link, tld)
                return True
            else:
                print(f'{timestamp()} {RED}[ERROR ARCHIVING]: {RESET}{link}')

        except requests.exceptions.RequestException as e:
            error_message = format_request_error(e)
            retry_message = f'{timestamp()} {YELLOW}[RETRYING] (ATTEMPT {attempt+1}/{MAX_RETRIES}): {RESET}{link}'

            # Format the error message for clarity
            formatted_error = "\n".join(["-"*50, error_message, retry_message, "-"*50])
            print(f'{formatted_error}')

        time.sleep(RETRY_DELAY)
    return False

def is_link_in_database(link):
    """Check if a link is already archived in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM archived_links WHERE url = ?', (link,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def insert_archived_link(link, tld):
    """Insert an archived link into the database with TLD."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO archived_links (url, tld) VALUES (?, ?)', (link, tld))
    conn.commit()
    conn.close()

def download_rss_feed(rss_feed_url):
    """Download an RSS feed and return its entries."""
    feed = feedparser.parse(rss_feed_url)
    return feed.entries

def download_rss_feeds():
    """Download RSS feeds concurrently and return the list of feed entries."""
    all_entries = []

    # Get the list of RSS feed URLs from the 'rss_urls' file
    rss_feed_urls = get_rss_feed_urls_from_file()

    # Shuffle the RSS feed URLs randomly
    random.shuffle(rss_feed_urls)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_rss_feed, rss_url) for rss_url in rss_feed_urls]

        with tqdm(total=len(rss_feed_urls), desc="Downloading RSS Feeds", ncols=100) as pbar:
            for future in concurrent.futures.as_completed(futures):
                try:
                    entries = future.result()
                    all_entries.extend(entries)
                except Exception as e:
                    print(f"An error occurred: {e}")

                pbar.update(1)

    return all_entries

def main():
    """Main function to retrieve RSS feeds, download links, and archive them to the Wayback Machine."""
    create_database()
    create_archive_table()

    # Get the current time
    current_time = datetime.now(tzlocal.get_localzone()).strftime("%H:%M:%S %Z")
    print(f'Running script at {current_time}')

    # Download RSS feeds and get the list of feed entries
    all_entries = download_rss_feeds()

    # Create a list to store links that need to be archived
    links_to_archive = []

    # Loop through each entry and check if the link is in the database
    for i, entry in enumerate(all_entries, start=1):
        link = entry.link

        # Check if the link is already archived in the database
        if not is_link_in_database(link):

            # Add the link to the list of links to be archived
            links_to_archive.append(link)

    # Shuffle the list of links to be archived randomly
    random.shuffle(links_to_archive)

    # Create a ThreadPoolExecutor to process the links concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Create a list to store link archive futures
        link_futures = []

        # Loop through each link to be archived and submit it for archiving
        for i, link in enumerate(links_to_archive, start=1):
            # Print progress information
            print(f'{timestamp()} {MAGENTA}[ARCHIVING {i}/{len(links_to_archive)}]: {RESET}{link}')

            # Submit the link for archiving
            future = executor.submit(archive_link, link)

            # Wait for the future to complete with a timeout
            try:
                concurrent.futures.wait([future], timeout=MAX_LINK_ARCHIVAL_TIME)
            except concurrent.futures.TimeoutError:
                # If the future times out, cancel it and print a message
                future.cancel()
                print(f'{timestamp()} {YELLOW}[SKIP - TIMEOUT]: {RESET}{link}')
                continue

            link_futures.append(future)

        # Wait for all link archiving futures to complete
        concurrent.futures.wait(link_futures)

if __name__ == '__main__':
    main()
