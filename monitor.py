import os
import requests
import html
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL_TO_MONITOR = os.environ.get("TARGET_URL")
SEEN_LINKS_FILE = "seen_links.txt"  # Stores all links we have already notified about

def get_all_links(url):
    """Scrapes all links from the page and returns them as a set."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        
        # Look for links specifically in the body or a known content div to avoid menu links
        content_area = soup.find('body')
        for a in content_area.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            # Basic filter: exclude common menu/social links if needed
            if "facebook.com" not in full_url and "twitter.com" not in full_url:
                links.add(full_url)
        return links
    except Exception as e:
        print(f"Scraping Error: {e}")
        return set()

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except Exception as e:
        print(f"Telegram Error: {e}")

def main():
    if not all([TELEGRAM_TOKEN, CHAT_ID, URL_TO_MONITOR]):
        print("Error: Missing required environment variables.")
        return

    # 1. Get current links from the page
    current_links = get_all_links(URL_TO_MONITOR)
    
    # 2. Load seen links from the file
    seen_links = set()
    if os.path.exists(SEEN_LINKS_FILE):
        with open(SEEN_LINKS_FILE, "r") as f:
            seen_links = set(line.strip() for line in f if line.strip())

    # 3. Find truly NEW links (links in current set but NOT in seen set)
    new_links = current_links - seen_links

    if new_links:
        print(f"Detected {len(new_links)} new updates!")
        for link in new_links:
            safe_link = html.escape(link)
            send_telegram_msg(f"<b>🚀 New Update Found!</b>\n\n{safe_link}")
        
        # 4. Save updated list of seen links
        # Using 'a' (append) or 'w' (overwrite) depends on preference. 
        # Here we overwrite to keep only currently active links.
        with open(SEEN_LINKS_FILE, "w") as f:
            for link in current_links:
                f.write(f"{link}\n")
    else:
        print("No new links detected.")

if __name__ == "__main__":
    main()
