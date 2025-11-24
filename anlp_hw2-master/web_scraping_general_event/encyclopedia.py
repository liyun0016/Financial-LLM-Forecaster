import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def remove_scripts_and_styles(soup):
    """Remove script, style, and noscript tags from the soup."""
    for tag_name in ["script", "style", "noscript"]:
        for tag in soup.find_all(tag_name):
            tag.extract()

def extract_text(element):
    """
    Given a BeautifulSoup element, return all visible text,
    reducing multiple spaces to a single space.
    """
    if not element:
        return ""
    remove_scripts_and_styles(element)
    text = element.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text

URL = "https://www.britannica.com/place/Pittsburgh"
OUTPUT_JSON = "pittsburgh_britannica.json"

def scroll_to_bottom(driver, pause_time=2, max_scrolls=10):
    """
    Scroll down the page to load dynamic content (infinite scroll).
    Repeat up to 'max_scrolls' times or until the page no longer grows.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(URL)
        time.sleep(3)  # Allow the page to load

        # Scroll to the bottom to load any dynamic content
        scroll_to_bottom(driver, pause_time=3, max_scrolls=20)
        
        # Parse the final rendered HTML
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Grab the <title>
        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else "Pittsburgh - Britannica"
        
        # Extract text from the main article container
        main_article = soup.find("article", class_="article-content container-lg qa-content px-0 pt-0 pb-40 py-lg-20 content")
        main_article_text = extract_text(main_article)
        
        # Extract text from all infinite-scroll containers
        infinite_divs = soup.find_all("div", class_="loaded-infinite-scroll-container qa-infinite-scroll-container")
        infinite_text_parts = []
        for div in infinite_divs:
            part_text = extract_text(div)
            if part_text:
                infinite_text_parts.append(part_text)
        infinite_scroll_text = "\n".join(infinite_text_parts).strip()
        
        # Combine all information into a single content string
        combined_text = (
            f"Title: {page_title}\n\n"
            f"Main Article:\n{main_article_text}\n\n"
            f"Infinite Scroll Content:\n{infinite_scroll_text}"
        )
        
        # Final output: { "url": "content" }
        output_data = { URL: combined_text }
        
        # Save to JSON
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
