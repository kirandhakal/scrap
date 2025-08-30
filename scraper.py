import requests
from bs4 import BeautifulSoup
import os
import json
import hashlib
from urllib.parse import urljoin, urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class NoticeScraper:
    def __init__(self, urls, telegram_token, chat_id, seen_file="seen_notices.json"):
        self.urls = urls
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.seen_file = seen_file
        self.max_workers = 3  # Limit concurrent requests
        self.request_delay = 1  # Delay between requests to be respectful

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        })
        self.seen_notices = self.load_seen()

    def load_seen(self):
        """Load seen notices with better error handling"""
        if os.path.exists(self.seen_file):
            try:
                with open(self.seen_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    # Clean old entries (keep last 1000 per site)
                    for site in data:
                        if len(data[site]) > 1000:
                            data[site] = data[site][-1000:]
                    return data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"⚠️ Error loading seen file: {e}. Starting fresh.")
                return {}
        return {}

    def save_seen(self):
        """Save with atomic write to prevent corruption"""
        temp_file = f"{self.seen_file}.tmp"
        try:
            with open(temp_file, "w", encoding='utf-8') as f:
                json.dump(self.seen_notices, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.seen_file)
        except Exception as e:
            print(f"⚠️ Error saving seen file: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def send_telegram_message(self, text, max_retries=3):
        """Send message with retry logic"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        for attempt in range(max_retries):
            try:
                r = self.session.post(url, data=payload, timeout=15)
                r.raise_for_status()
                print(f"📩 Sent Telegram message ({len(text)} chars)")
                return True
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"⚠️ Telegram error after {max_retries} attempts: {e}")
                    return False
                print(f"⚠️ Telegram attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
        return False

    def fetch_page(self, url, timeout=15):
        """Fetch page with better error handling and rate limiting"""
        try:
            time.sleep(self.request_delay)  # Be respectful
            r = self.session.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout fetching {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching {url}: {e}")
            return None

    def generate_content_hash(self, url, title=""):
        """Generate hash for deduplication"""
        content = f"{url}:{title}".lower()
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def find_notice_links(self, html, base_url):
        """Improved notice detection with better keywords"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        
        # Enhanced keywords for notice detection
        notice_keywords = [
            "notice", "सूचना", "announcement",
            "vacancy", "रिक्त", "result", "नतिजा", "admission", "भर्ना"
        ]
        
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not href:
                continue
                
            text = a.get_text(strip=True).lower()
            title = a.get("title", "").lower()
            
            # Check if any keyword matches
            if any(keyword in href.lower() or keyword in text or keyword in title 
                   for keyword in notice_keywords):
                full_url = urljoin(base_url, href)
                # Avoid duplicates and invalid URLs
                if full_url not in links and full_url.startswith(('http://', 'https://')):
                    links.append(full_url)
        
        return links

    def find_notice_files(self, html, base_url):
        """Find downloadable files with better filtering"""
        soup = BeautifulSoup(html, "html.parser")
        files = []
        
        file_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
        
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if any(ext in href.lower() for ext in file_extensions):
                full_url = urljoin(base_url, href)
                if full_url.startswith(('http://', 'https://')):
                    files.append(full_url)
        
        return list(set(files))

    def process_notice_link(self, link, site_name):
        """Process individual notice link"""
        try:
            page_html = self.fetch_page(link)
            if not page_html:
                return None

            # Extract title from page
            soup = BeautifulSoup(page_html, "html.parser")
            title_elem = soup.find('title') or soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True)[:100] if title_elem else "Notice"

            files = self.find_notice_files(page_html, link)
            
            message_parts = [f"📢 <b>{site_name.upper()}</b>"]
            if title and title.lower() != "notice":
                message_parts.append(f"📋 {title}")
            message_parts.append(f"🔗 {link}")
            
            for file_url in files:
                message_parts.append(f"📄 {file_url}")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            print(f"✗ Error processing {link}: {e}")
            return None

    def check_site(self, url):
        """Check site with improved error handling and concurrency"""
        site_name = urlparse(url).netloc.split(".")[0]
        print(f"\n🔎 Checking {site_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        html = self.fetch_page(url)
        if not html:
            return 0

        notice_links = self.find_notice_links(html, url)
        if not notice_links:
            print("No notice links found.")
            return 0

        # Filter out already seen notices
        site_seen = self.seen_notices.get(site_name, [])
        new_links = []
        
        for link in notice_links:
            link_hash = self.generate_content_hash(link)
            if link not in site_seen and link_hash not in site_seen:
                new_links.append(link)

        if not new_links:
            print("No new notices.")
            return 0

        print(f"Found {len(new_links)} new notices")
        
        # Process links concurrently but respectfully
        messages = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_link = {
                executor.submit(self.process_notice_link, link, site_name): link 
                for link in new_links[:10]  # Limit to 10 new notices per run
            }
            
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    message = future.result()
                    if message:
                        messages.append(message)
                        # Mark as seen
                        link_hash = self.generate_content_hash(link)
                        self.seen_notices.setdefault(site_name, []).extend([link, link_hash])
                except Exception as e:
                    print(f"✗ Error processing {link}: {e}")

        # Send messages
        if messages:
            combined = "\n\n".join(messages)
            # Split long messages
            max_length = 3500
            if len(combined) <= max_length:
                self.send_telegram_message(combined)
            else:
                chunks = [combined[i:i+max_length] for i in range(0, len(combined), max_length)]
                for chunk in chunks:
                    self.send_telegram_message(chunk)
                    time.sleep(1)  # Avoid rate limits

        return len(messages)

    def run(self):
        """Main execution with better error handling"""
        print(f"🚀 Starting scraper run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_new = 0
        for url in self.urls:
            try:
                count = self.check_site(url)
                total_new += count
            except Exception as e:
                print(f"✗ Error checking {url}: {e}")
                continue
        
        # Save state
        try:
            self.save_seen()
            print(f"\n✅ Run complete. New items: {total_new}")
        except Exception as e:
            print(f"⚠️ Error saving state: {e}")

        return total_new


if __name__ == "__main__":
    # === CONFIG ===
    URLS = [
        "https://madhyabindumun.gov.np/en/search/node/notice",
        "https://kawasotimun.gov.np/search/node/notice", 
        "https://gaindakotmun.gov.np/en/search/node/notice",
        "https://devchulimun.gov.np/search/node/notice"
    ]

    # Get bot credentials from environment variables
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    CHAT_ID = os.getenv("CHAT_ID", "")

    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Missing BOT_TOKEN or CHAT_ID environment variables")
        print("\nHow to set up:")
        print("1. Create a bot via @BotFather on Telegram")
        print("2. Get your chat ID by messaging your bot and visiting:")
        print("   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        print("\nFor local testing:")
        print('export BOT_TOKEN="your_bot_token_here"')
        print('export CHAT_ID="your_chat_id_here"')
        print("python scraper.py")
        exit(1)

    try:
        scraper = NoticeScraper(URLS, BOT_TOKEN, CHAT_ID)
        scraper.run()
    except KeyboardInterrupt:
        print("\n⏹️ Scraper stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        exit(1)
