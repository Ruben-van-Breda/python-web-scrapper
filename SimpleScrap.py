import requests
from bs4 import BeautifulSoup
import sys
import json

def simple_scrape(url: str) -> dict:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(separator=' ', strip=True)
        return {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "content": content
        }

    except Exception as e:
        print(f"❌ Failed to scrape: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python WebScrap.py https://example.com", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    data = simple_scrape(url)
    print(json.dumps(data, indent=2))