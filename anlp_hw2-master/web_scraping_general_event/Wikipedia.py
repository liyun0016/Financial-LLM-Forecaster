import requests
from bs4 import BeautifulSoup
import json
import re

# Define the Wikipedia URLs
urls = {
    "Pittsburgh": "https://en.wikipedia.org/wiki/Pittsburgh",
    "History_of_Pittsburgh": "https://en.wikipedia.org/wiki/History_of_Pittsburgh"
}

# Set headers to mimic a browser visit
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Function to clean text (remove citations like [1], [citation needed], and extra spaces)
def clean_text(text):
    text = re.sub(r"\[\d+\]", "", text)  # Remove [1], [2], etc.
    text = re.sub(r"\[citation needed\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()  # Remove excessive spaces
    return text

# Function to scrape Wikipedia page
def scrape_wikipedia(url):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract all paragraphs from the main content
        content = "\n".join([clean_text(p.text.strip()) for p in soup.find_all("p") if p.text.strip()])
        
        return {
            "content": content,
            "url": url
        }
    else:
        print(f"Failed to retrieve: {url}")
        return None

# Iterate over the URLs, scrape and save each as a separate JSON file in the format { "url": "content" }
for key, url in urls.items():
    scraped_data = scrape_wikipedia(url)
    if scraped_data:
        # Build new data structure: key is the URL and value is the scraped content
        file_data = { scraped_data["url"]: scraped_data["content"] }
        
        # Save to a JSON file named after the key
        file_name = f"{key}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=4, ensure_ascii=False)
        print(f"Saved data to {file_name}")
