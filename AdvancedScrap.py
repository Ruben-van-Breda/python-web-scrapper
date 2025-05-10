import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import json
import os

visited_urls = set()
failed_urls = []

def sanitize_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_")
    return path if path else "index"

def simple_scrape(url: str, recursive=False, output_dir=None, max_depth=2) -> list:
    results = []
    base_parsed = urlparse(url)
    base_domain = base_parsed.netloc
    base_path = base_parsed.path.rstrip('/')

    def scrape(current_url, depth):
        if current_url in visited_urls or depth > max_depth:
            return
        visited_urls.add(current_url)
        print(f"Visiting: {current_url} [Depth: {depth}]")

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(current_url, headers=headers, timeout=10)

            if response.status_code == 404:
                print(f"⚠️  Skipping 404: {current_url}", file=sys.stderr)
                failed_urls.append(current_url)
                return

            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)

            result = {
                "url": current_url,
                "title": soup.title.string if soup.title else "",
                "content": content
            }

            results.append(result)

            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                filename = sanitize_filename(current_url) + ".txt"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"✅ Saved to: {filepath}")

            if recursive and depth < max_depth:
                for link_tag in soup.find_all('a', href=True):
                    link = urljoin(current_url, link_tag['href'])
                    parsed_link = urlparse(link)

                    if (
                        parsed_link.netloc == base_domain and
                        (
                            parsed_link.path == base_path or
                            parsed_link.path.startswith(base_path + '/')
                        ) and
                        not parsed_link.fragment
                    ):
                        scrape(link, depth + 1)

        except Exception as e:
            print(f"❌ Failed to scrape {current_url}: {e}", file=sys.stderr)
            failed_urls.append(current_url)

    scrape(url, depth=0)

    if failed_urls and output_dir:
        fail_log = os.path.join(output_dir, "failed.txt")
        with open(fail_log, "w") as f:
            f.write("\n".join(failed_urls))
        print(f"❌ Logged {len(failed_urls)} failed URLs to {fail_log}")

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python AdvancedScrap.py <url> [-o output_dir] [-depth N]", file=sys.stderr)
        sys.exit(1)

    raw_url = sys.argv[1]
    output_dir = None
    max_depth = 2  # default

    if "-o" in sys.argv:
        try:
            output_dir = sys.argv[sys.argv.index("-o") + 1]
        except IndexError:
            print("❌ Missing output directory after -o", file=sys.stderr)
            sys.exit(1)

    if "-depth" in sys.argv:
        try:
            max_depth = int(sys.argv[sys.argv.index("-depth") + 1])
        except (IndexError, ValueError):
            print("❌ Missing or invalid number for -depth", file=sys.stderr)
            sys.exit(1)

    recursive = raw_url.endswith("/*")
    url = raw_url.rstrip("/*")

    data = simple_scrape(url, recursive=recursive, output_dir=output_dir, max_depth=max_depth)

    if not output_dir:
        print(json.dumps(data, indent=2))