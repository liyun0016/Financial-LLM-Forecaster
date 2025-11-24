import requests
from bs4 import BeautifulSoup
import re
import json

# URL to scrape
url = "https://www.visitpittsburgh.com"

# Set headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Fetch the page
response = requests.get(url, headers=headers)
if response.status_code != 200:
    raise Exception(f"Failed to retrieve {url}. Status code: {response.status_code}")

# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")

# Remove script, style, and noscript elements
for tag in soup(["script", "style", "noscript"]):
    tag.decompose()

# Extract visible text and remove extra whitespace
text = soup.get_text(separator=" ")
clean_text = re.sub(r"\s+", " ", text).strip()

# Create final JSON with the URL as the key and the content as the value
final_output = {url: clean_text}

# Save to JSON file
with open("visitpittsburgh.json", "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=4, ensure_ascii=False)
