import os
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION FROM GITHUB SECRETS ---
# Reads the values you added to Settings > Secrets > Actions
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL_TO_MONITOR = os.environ.get("TARGET_URL")
LAST_LINK_FILE = "last_article.txt"

def get_latest_article():
    """Scrapes the target website for the newest article link."""
    try:
        response = requests.get(URL_TO_MONITOR, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # COMMON SELECTOR: This looks for the first <a> tag inside an <article>
        # You may need to change 'article' to 'div' or use a specific class
        article = soup.find('article')
        if article:
            link_tag = article.find('a')
            if link_tag and link_tag.get('href'):
                link = link_tag['href']
                # Make link absolute if it's relative
                if link.startswith('/'):
                    from urllib.parse import urljoin
                    link = urljoin(URL_TO_MONITOR, link)
                return link
    except Exception as e:
        print(f"Scraping Error: {e}")
    return None

def send_telegram_msg(message):
    """Sends notification to Telegram via Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
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

    current_link = get_latest_article()
    
    # Load previous state
    last_known_link = ""
    if os.path.exists(LAST_LINK_FILE):
        with open(LAST_LINK_FILE, "r") as f:
            last_known_link = f.read().strip()

    if current_link and current_link != last_known_link:
        print(f"New update detected: {current_link}")
        send_telegram_msg(f"<b>🚀 New Article Found!</b>\n\n{current_link}")
        
        # Save new state to file
        with open(LAST_LINK_FILE, "w") as f:
            f.write(current_link)
    else:
        print("No new changes detected.")

if __name__ == "__main__":
    main()
