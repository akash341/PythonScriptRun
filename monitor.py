import os
import requests
import html
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL_TO_MONITOR = os.environ.get("TARGET_URL")
SEEN_LINKS_FILE = "seen_links.txt"

def get_all_links(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = set()
        # Find all <a> tags with hrefs
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            # Basic cleanup: ignore internal anchors (#) or non-http links
            if full_url.startswith("http"):
                links.add(full_url)
        return links
    except Exception as e:
        print(f"Scraping Error: {e}")
        return set()

def main():
    # 1. Load seen links from history file
    seen_links = set()
    if os.path.exists(SEEN_LINKS_FILE):
        with open(SEEN_LINKS_FILE, "r") as f:
            seen_links = {line.strip() for line in f if line.strip()}

    # 2. Get current links from the web
    current_links = get_all_links(URL_TO_MONITOR)
    
    # 3. Identify ONLY new links
    new_links = current_links - seen_links

    if new_links:
        print(f"Found {len(new_links)} new updates!")
        for link in new_links:
            # Send to Telegram
           url = f"https://api.telegram.org{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": f"<b>🚀 New Link Found!</b>\n\n{html.escape(link)}", "parse_mode": "HTML"}
            requests.post(url, data=payload)
        
        # 4. Save updated list back to file
        # We combine old + new to maintain history
        with open(SEEN_LINKS_FILE, "w") as f:
            for link in (seen_links | current_links):
                f.write(f"{link}\n")
    else:
        print("No new content found.")

if __name__ == "__main__":
    main()
