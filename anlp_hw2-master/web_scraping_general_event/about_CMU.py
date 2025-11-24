import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re
import pdfplumber
import os

def remove_scripts_and_styles(soup):
    """Remove script, style, and noscript tags from the soup."""
    for tag_name in ["script", "style", "noscript"]:
        for tag in soup.find_all(tag_name):
            tag.extract()

def extract_all_text(html_soup):
    """
    Remove scripts/styles and return all visible text
    with multiple spaces reduced to a single space.
    """
    remove_scripts_and_styles(html_soup)
    text = html_soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text

BASE_URL = "https://www.cmu.edu/about/"
OUTPUT_JSON = "cmu_about_alltext_with_pdf.json"

# 1. Fetch the main About CMU page
response = requests.get(BASE_URL)
if response.status_code != 200:
    raise Exception(f"Failed to fetch {BASE_URL}, status code: {response.status_code}")

main_soup = BeautifulSoup(response.text, "html.parser")
main_page_text = extract_all_text(main_soup)

# 2. Find all subpage links from the sidebar
sidebar = main_soup.find("div", class_="sidebar")
subpage_links = []
if sidebar:
    for link in sidebar.find_all("a", href=True):
        href = link["href"]
        absolute_url = urljoin(BASE_URL, href)
        subpage_links.append(absolute_url)
else:
    print("No sidebar found on the main page.")

# 3. Find any PDF links on the main page (e.g., cmu-fact-sheet.pdf)
pdf_links = []
for link in main_soup.find_all("a", href=True):
    href = link["href"]
    if href.lower().endswith(".pdf"):
        pdf_links.append(urljoin(BASE_URL, href))

# 4. Scrape each subpage for all text
subpages_data = []
for url in subpage_links:
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Warning: Failed to fetch {url} (status {resp.status_code}). Skipping.")
            continue

        sub_soup = BeautifulSoup(resp.text, "html.parser")
        page_text = extract_all_text(sub_soup)

        title_tag = sub_soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else url

        subpages_data.append({
            "url": url,
            "title": page_title,
            "content": page_text
        })

        print(f"Scraped subpage: {url}")

    except Exception as e:
        print(f"Error scraping {url}: {e}")

# 5. Download and extract text from each PDF link
pdf_data = []
for pdf_url in pdf_links:
    try:
        pdf_filename = pdf_url.split("/")[-1] or "document.pdf"
        # Download the PDF
        print(f"Downloading PDF: {pdf_url}")
        pdf_response = requests.get(pdf_url)
        if pdf_response.status_code != 200:
            print(f"Warning: Failed to fetch PDF {pdf_url} (status {pdf_response.status_code}). Skipping.")
            continue

        # Save PDF locally
        with open(pdf_filename, "wb") as f:
            f.write(pdf_response.content)

        # Extract text with pdfplumber
        print(f"Extracting text from {pdf_filename}")
        extracted_text_pages = []
        with pdfplumber.open(pdf_filename) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text_pages.append(page_text)

        # Combine all PDF pages into one string
        full_pdf_text = "\n".join(extracted_text_pages)

        pdf_data.append({
            "pdf_url": pdf_url,
            "pdf_filename": pdf_filename,
            "content": full_pdf_text
        })

        # Optionally remove the downloaded PDF file
        os.remove(pdf_filename)

    except Exception as e:
        print(f"Error processing PDF {pdf_url}: {e}")

# 6. Combine everything into a dictionary where each key is the URL and the value is all information in one content string.
final_output = {}

# Main page
final_output[BASE_URL] = f"Title: Carnegie Mellon - About (All Text)\nContent:\n{main_page_text}"

# Subpages
for sub in subpages_data:
    url = sub["url"]
    title = sub["title"]
    content = sub["content"]
    final_output[url] = f"Title: {title}\nContent:\n{content}"

# PDFs
for pdf in pdf_data:
    pdf_url = pdf["pdf_url"]
    pdf_filename = pdf["pdf_filename"]
    content = pdf["content"]
    final_output[pdf_url] = f"Filename: {pdf_filename}\nContent:\n{content}"

# 7. Save to JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=4, ensure_ascii=False)

print(f"Done. All text (main page, subpages, PDFs) saved to '{OUTPUT_JSON}'.")