import os
import requests
import hashlib
from bs4 import BeautifulSoup

# --- CONFIGURATION FROM GITHUB SECRETS ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL_TO_MONITOR = os.environ.get("TARGET_URL")
LAST_STATE_FILE = "last_hash.txt"  # Renamed to reflect we are storing a hash

def get_page_hash(url):
    """Fetches the page and returns a SHA-256 hash of its content."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Option A: Hash the ENTIRE page content
        content = response.text
        
        # Option B: Hash only a specific part (e.g., the <article> section)
        # soup = BeautifulSoup(content, 'html.parser')
        # article = soup.find('article')
        # if article:
        #     content = str(article)

        # Create a digital fingerprint (SHA-256 hash)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def send_telegram_msg(message):
    """Sends notification to Telegram via Bot API."""
    url = f"https://api.telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except Exception as e:
        print(f"Telegram Error: {e}")

def main():
    if not all([TELEGRAM_TOKEN, CHAT_ID, URL_TO_MONITOR]):
        print("Error: Missing required environment variables (Secrets).")
        return

    # 1. Get the current fingerprint of the page
    current_hash = get_page_hash(URL_TO_MONITOR)
    
    # 2. Load the fingerprint from the previous run
    last_known_hash = ""
    if os.path.exists(LAST_STATE_FILE):
        with open(LAST_STATE_FILE, "r") as f:
            last_known_hash = f.read().strip()

    # 3. Compare and notify if they are different
    if current_hash and current_hash != last_known_hash:
        print(f"Change detected on page!")
        send_telegram_msg(f"<b>⚠️ Page Content Updated!</b>\n\nView changes here:\n{URL_TO_MONITOR}")
        
        # Save the new fingerprint for the next 30-minute check
        with open(LAST_STATE_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No content changes detected.")

if __name__ == "__main__":
    main()
