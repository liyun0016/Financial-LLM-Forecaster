import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse

# Set base URL and headers to mimic a browser
BASE_URL = "https://www.pittsburghpa.gov/Home"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Store visited links to avoid duplicate scraping
visited_links = set()

# Store the scraped data
scraped_data = {}

def clean_text(text):
    """Remove extra spaces and unwanted characters from text."""
    return ' '.join(text.split()).strip()

def scrape_page(url, depth=0, max_depth=3):
    """Recursively scrape the given URL up to a certain depth."""
    if url in visited_links or depth > max_depth:
        return
    
    print(f"Scraping: {url} (Depth: {depth})")
    visited_links.add(url)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch {url}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        title = clean_text(soup.find("title").text) if soup.find("title") else "No Title"
        paragraphs = [clean_text(p.text) for p in soup.find_all("p") if clean_text(p.text)]
        
        # Save data for this page
        scraped_data[url] = {
            "title": title,
            "content": paragraphs,
            "url": url
        }

        # Recursively scrape links within the domain
        for link in soup.find_all("a", href=True):
            full_url = urljoin(url, link["href"])
            parsed_url = urlparse(full_url)
            if "pittsburghpa.gov" in parsed_url.netloc and full_url not in visited_links:
                scrape_page(full_url, depth=depth+1, max_depth=max_depth)

        time.sleep(1)

    except Exception as e:
        print(f"Error scraping {url}: {e}")

# Start scraping from the main page
scrape_page(BASE_URL, max_depth=2)

# Combine all the scraped content into a single string
combined_content = ""
for url, data in scraped_data.items():
    combined_content += f"Title: {data.get('title', 'No Title')}\n"
    combined_content += "Content: " + " ".join(data.get("content", [])) + "\n"
    combined_content += "=" * 80 + "\n\n"

# Create final JSON output with one key
final_output = { BASE_URL: combined_content }

# Save the final output to a JSON file
with open("pittsburgh_website_data.json", "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=4, ensure_ascii=False)

print("Scraping completed! Data saved to 'pittsburgh_website_data.json'")
