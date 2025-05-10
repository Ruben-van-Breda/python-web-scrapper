#!/usr/bin/env python3

import argparse
import json
import os
import sys
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup


def web_scrap(url, mode="full"):
    """
    Scrapes the content from the given URL.
    
    @param url - URL to scrape
    @param mode - Scraping mode: 'text' (text only), 'full' (text with metadata), 
                 'html' (complete HTML), or 'advanced' (detailed structured content)
    @returns Dictionary containing the URL and the scraped content
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        result = {"url": url}
        
        if mode == "text":
            # Extract only the text content from the page
            result["content"] = soup.get_text(separator=' ', strip=True)
        
        elif mode == "full":
            # Extract text and metadata
            result["title"] = soup.title.text if soup.title else ""
            result["meta_description"] = soup.find("meta", attrs={"name": "description"})["content"] if soup.find("meta", attrs={"name": "description"}) else ""
            
            # Get main content
            result["content"] = soup.get_text(separator=' ', strip=True)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                links.append({
                    "text": link.text.strip(),
                    "href": link['href']
                })
            result["links"] = links
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                image_data = {
                    "src": img['src'],
                    "alt": img.get('alt', '')
                }
                images.append(image_data)
            result["images"] = images
            
        elif mode == "html":
            # Store the complete HTML
            result["html"] = str(soup)
            
        elif mode == "advanced":
            # Extract comprehensive structured content
            result["title"] = soup.title.text if soup.title else ""
            
            # Extract all meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                if meta.get('name'):
                    meta_tags[meta.get('name')] = meta.get('content', '')
                elif meta.get('property'):
                    meta_tags[meta.get('property')] = meta.get('content', '')
            result["meta_tags"] = meta_tags
            
            # Extract page structure as a hierarchy
            result["structure"] = extract_page_structure(soup, url)
            
            # Extract all scripts with type="application/ld+json" (structured data)
            structured_data = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    structured_data.append(json.loads(script.string))
                except (json.JSONDecodeError, TypeError):
                    pass
            result["structured_data"] = structured_data
            
            # Extract tables
            tables = []
            for table in soup.find_all('table'):
                tables.append(extract_table(table))
            result["tables"] = tables
            
            # Find main content area (heuristic approach)
            main_content = find_main_content(soup)
            if main_content:
                result["main_content"] = extract_content_elements(main_content, url)
            else:
                result["main_content"] = extract_content_elements(soup.body, url) if soup.body else []
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_page_structure(soup, base_url):
    """
    Extracts the hierarchical structure of the page with headers (h1-h6).
    
    @param soup - BeautifulSoup object
    @param base_url - Base URL for resolving relative URLs
    @returns List of hierarchical page sections
    """
    structure = []
    
    # Extract all headings
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    for i, heading in enumerate(headings):
        current_level = int(heading.name[1])
        section = {
            "level": current_level,
            "text": heading.get_text(strip=True),
            "id": heading.get('id', ''),
            "content": []
        }
        
        # Get content until next heading of same or higher level
        next_sibling = heading.next_sibling
        while next_sibling:
            if next_sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and int(next_sibling.name[1]) <= current_level:
                break
                
            if next_sibling.name:
                content = extract_element_content(next_sibling, base_url)
                if content:
                    section["content"].append(content)
                    
            next_sibling = next_sibling.next_sibling
            
        structure.append(section)
    
    return structure


def extract_element_content(element, base_url):
    """
    Extracts content from an HTML element based on its type.
    
    @param element - BeautifulSoup element
    @param base_url - Base URL for resolving relative URLs
    @returns Dictionary with element type and content
    """
    if not element.name:
        return None
        
    if element.name == 'p':
        return {
            "type": "paragraph",
            "text": element.get_text(strip=True)
        }
    elif element.name in ['ul', 'ol']:
        items = []
        for li in element.find_all('li', recursive=False):
            items.append(li.get_text(strip=True))
        return {
            "type": "list",
            "list_type": "unordered" if element.name == 'ul' else "ordered",
            "items": items
        }
    elif element.name == 'pre' or element.name == 'code':
        return {
            "type": "code",
            "text": element.get_text(strip=False)
        }
    elif element.name == 'blockquote':
        return {
            "type": "quote",
            "text": element.get_text(strip=True)
        }
    elif element.name == 'img' and element.get('src'):
        return {
            "type": "image",
            "src": urljoin(base_url, element.get('src')),
            "alt": element.get('alt', '')
        }
    elif element.name == 'a' and element.get('href'):
        return {
            "type": "link",
            "text": element.get_text(strip=True),
            "href": urljoin(base_url, element.get('href'))
        }
    elif element.name == 'table':
        return {
            "type": "table",
            "data": extract_table(element)
        }
    elif element.name == 'div' or element.name == 'section':
        content = []
        for child in element.children:
            if child.name:
                child_content = extract_element_content(child, base_url)
                if child_content:
                    content.append(child_content)
        if content:
            return {
                "type": "container",
                "content": content
            }
    
    return None


def extract_table(table):
    """
    Extracts data from an HTML table.
    
    @param table - BeautifulSoup table element
    @returns Dictionary with headers and rows
    """
    table_data = {"headers": [], "rows": []}
    
    # Extract headers
    headers = table.find_all('th')
    if headers:
        table_data["headers"] = [header.get_text(strip=True) for header in headers]
    
    # Extract rows
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if cells and not all(cell.name == 'th' for cell in cells):
            table_data["rows"].append([cell.get_text(strip=True) for cell in cells])
    
    return table_data


def find_main_content(soup):
    """
    Attempts to find the main content area of the page using common selectors.
    
    @param soup - BeautifulSoup object
    @returns Main content element or None if not found
    """
    # Try common content container selectors
    for selector in ['main', 'article', '#content', '.content', '#main', '.main', '.post', '.entry', '.entry-content']:
        try:
            if selector.startswith('#'):
                element = soup.find(id=selector[1:])
            elif selector.startswith('.'):
                element = soup.find(class_=selector[1:])
            else:
                element = soup.find(selector)
            
            if element:
                return element
        except:
            continue
    
    return None


def extract_content_elements(container, base_url):
    """
    Extracts structured content from the main content container.
    
    @param container - BeautifulSoup element containing the main content
    @param base_url - Base URL for resolving relative URLs
    @returns List of content elements
    """
    content = []
    
    # Get direct children of the container
    for element in container.children:
        if element.name:
            element_content = extract_element_content(element, base_url)
            if element_content:
                content.append(element_content)
    
    return content


def save_output(data, destination):
    """
    Saves the scraped data to a JSON file at the specified destination.
    
    @param data - Dictionary containing the scraped data
    @param destination - Path to save the output
    @returns Path to the saved file
    """
    try:
        # Create the destination directory if it doesn't exist
        os.makedirs(destination, exist_ok=True)
        
        # Parse the URL to extract the domain for the filename
        parsed_url = urlparse(data["url"])
        domain = parsed_url.netloc.replace("www.", "")
        
        # Create filename based on domain
        filename = os.path.join(destination, f"{domain}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return filename
    except Exception as e:
        print(f"Error saving output to {destination}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function to parse arguments and execute the web scraping functionality.
    """
    parser = argparse.ArgumentParser(description='Web scraper to extract content from a URL and save it as JSON.')
    parser.add_argument('-url', required=True, help='URL to scrape')
    parser.add_argument('-o', '--output', dest='destination', required=True, help='Destination folder to save the output')
    parser.add_argument('-m', '--mode', dest='mode', choices=['text', 'full', 'html', 'advanced'], default='full',
                        help='Scraping mode: text (text only), full (text with metadata), html (complete HTML), or advanced (detailed structured content)')
    
    args = parser.parse_args()
    
    # Validate URL
    try:
        result = urlparse(args.url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
    except ValueError as e:
        print(f"Error: {e}. Please provide a valid URL with scheme (e.g., http:// or https://)", file=sys.stderr)
        sys.exit(1)
    
    # Scrape the webpage
    scraped_data = web_scrap(args.url, args.mode)
    
    # Save the scraped data
    output_file = save_output(scraped_data, args.destination)
    
    print(f"Successfully scraped {args.url} using {args.mode} mode")
    print(f"Output saved to {output_file}")


if __name__ == "__main__":
    main()
