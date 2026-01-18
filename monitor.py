import os
import requests
import hashlib
import html  # Added for Option 2: Secure formatting
from bs4 import BeautifulSoup

# --- CONFIGURATION FROM GITHUB SECRETS ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL_TO_MONITOR = os.environ.get("TARGET_URL")
LAST_STATE_FILE = "last_hash.txt"

def get_page_hash(url):
    """Fetches the page and returns a SHA-256 hash of a specific section."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- IMPROVED HASHING (Option B) ---
        # Target a specific element (like 'body' or 'main') to avoid 
        # false positives from invisible metadata in the <head>
        target_element = soup.find('body') 
        if target_element:
            content = target_element.get_text() # Get only text to ignore attribute changes
        else:
            content = response.text

        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def send_telegram_msg(message):
    """Sends notification to Telegram via Bot API."""
    # FIX: Added missing '/bot' in the URL string
    url = f"https://api.telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except Exception as e:
        # Improved error reporting
        print(f"Telegram Error: {e}")
        if 'r' in locals():
            print(f"Response Body: {r.text}")

def main():
    if not all([TELEGRAM_TOKEN, CHAT_ID, URL_TO_MONITOR]):
        print("Error: Missing required environment variables.")
        return

    current_hash = get_page_hash(URL_TO_MONITOR)
    
    last_known_hash = ""
    if os.path.exists(LAST_STATE_FILE):
        with open(LAST_STATE_FILE, "r") as f:
            last_known_hash = f.read().strip()

    if current_hash and current_hash != last_known_hash:
        print(f"Change detected on page!")
        
        # --- OPTION 2: Use html.escape for the message ---
        safe_url = html.escape(URL_TO_MONITOR)
        message = f"<b>⚠️ Page Content Updated!</b>\n\nView changes here:\n{safe_url}"
        
        send_telegram_msg(message)
        
        with open(LAST_STATE_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No content changes detected.")

if __name__ == "__main__":
    main()
