import time
import json
import os
import requests
import pdfplumber
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Base URL
BASE_URL = "https://www.pittsburghpa.gov/City-Government/Finances-Budget/Taxes/Tax-Forms"

# Directory to save PDF files
PDF_DIR = "tax_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

# Set up Selenium WebDriver (headless mode)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run without opening browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Set up the WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 1. Open the webpage
driver.get(BASE_URL)
time.sleep(3)  # Allow JavaScript to load content

# 2. Expand all dropdown lists (accordion items)
accordion_buttons = driver.find_elements(By.CSS_SELECTOR, "a.accordion-trigger")
for button in accordion_buttons:
    driver.execute_script("arguments[0].click();", button)
    time.sleep(1)  # Allow content to load

# 3. Get the updated page source after JavaScript execution
page_source = driver.page_source
soup = BeautifulSoup(page_source, "html.parser")

# 4. Find all PDF links
pdf_links = []
accordion_container = soup.find("div", class_="accordion-list-container")

if accordion_container:
    for link in accordion_container.find_all("a", href=True):
        pdf_url = urljoin(BASE_URL, link["href"])  # Make absolute URL
        if pdf_url.lower().endswith(".pdf"):  # Filter only PDFs (case-insensitive)
            pdf_links.append(pdf_url)

# Close Selenium WebDriver
driver.quit()

print(f"Found {len(pdf_links)} PDF links.")

# 5. Download each PDF and extract text
# Build a dictionary to store output in the format { "url": "content" }
output_data = {}

for pdf_url in pdf_links:
    try:
        pdf_name = pdf_url.split("/")[-1] or "document.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        
        # Download the PDF file
        print(f"Downloading: {pdf_url}")
        response = requests.get(pdf_url, timeout=15, verify=False)  # 'verify=False' to skip SSL errors if any
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        
        # Extract text using pdfplumber
        print(f"Extracting text from: {pdf_name}")
        pdf_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text.append(page_text)
        
        # Combine all pages into one string
        full_text = "\n".join(pdf_text).strip()
        
        # Combine filename and full text into one content string
        combined_content = f"Filename: {pdf_name}\nExtracted Text:\n{full_text}"
        
        # Store the result with the PDF URL as key
        output_data[pdf_url] = combined_content

    except Exception as e:
        print(f"Error processing {pdf_url}: {e}")

# 6. Save extracted documents to JSON in the format { "url": "content" }
with open("tax_pdf_knowledge.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4, ensure_ascii=False)
