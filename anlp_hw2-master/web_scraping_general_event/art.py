import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_body_text(driver):
    """Return the entire visible text of <body>."""
    return driver.find_element(By.TAG_NAME, "body").text.strip()

def get_mashup_blocks(driver):
    """
    Locate the container with class="mashup__grid" and then find all items with class="mashup__item".
    Return a list of these elements.
    """
    try:
        mashup_grid = driver.find_element(By.CSS_SELECTOR, "div.mashup__grid")
    except Exception as e:
        print("Could not find mashup__grid:", e)
        return []
    items = mashup_grid.find_elements(By.CSS_SELECTOR, "div.mashup__item")
    return items

def gather_listings(driver, results):
    """
    If there's an element with class="cards__inner", gather text from each
    "div.card.card--common.card--has-image.card--listing".
    """
    try:
        cards_inner = driver.find_element(By.CLASS_NAME, "cards__inner")
    except Exception as e:
        # No listing found on this page
        return

    listing_cards = cards_inner.find_elements(By.CSS_SELECTOR, "div.card.card--common.card--has-image.card--listing")
    for card in listing_cards:
        try:
            listing_text = card.text.strip()
            if listing_text:
                results.append({
                    "type": "listing_card",
                    "listing_text": listing_text
                })
        except Exception as e:
            print("Error processing a listing card:", e)

def handle_pagination_and_listings(driver, results):
    """
    Gather listing items on the current page and then, if available, click the next page in the pagination.
    """
    while True:
        gather_listings(driver, results)
        try:
            pagination = driver.find_element(By.CLASS_NAME, "ais-Pagination")
            next_page_li = pagination.find_element(By.CSS_SELECTOR, "li.ais-Pagination-item.ais-Pagination--nextPage")
            # If the next page button is disabled, break out of the loop
            if "ais-Pagination-item--disabled" in next_page_li.get_attribute("class"):
                break
            next_page_li.click()
            time.sleep(3)
        except Exception as e:
            break

def scrape_subpage(driver, url, block_index, results):
    """
    Open the subpage in a new tab, gather:
      - the entire page text
      - any listing information (with pagination)
    """
    driver.execute_script("window.open(arguments[0]);", url)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)

    # Option A: Entire subpage text
    subpage_text = get_body_text(driver)
    results.append({
        "type": "subpage_text",
        "block_index": block_index,
        "subpage_url": url,
        "content": subpage_text
    })

    # Option B: Listings with pagination (if any)
    handle_pagination_and_listings(driver, results)

    # Close the subpage tab and return to the main window
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)

def main():
    # Set up the headless browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    base_url = "https://www.visitpittsburgh.com"
    driver.get(base_url)
    time.sleep(3)

    all_data = []

    # 1) Get main page text
    main_page_text = get_body_text(driver)
    all_data.append({
        "type": "main_page_text",
        "url": base_url,
        "content": main_page_text
    })

    # 2) Get mashup blocks
    mashup_items = get_mashup_blocks(driver)
    print(f"Found {len(mashup_items)} blocks in mashup__grid.")

    for idx, item in enumerate(mashup_items, start=1):
        block_text = item.text.strip()
        # Save the block text too
        all_data.append({
            "type": "mashup_block",
            "block_index": idx,
            "block_text": block_text
        })

        # 3) Within each block, find all <a> links and scrape their subpages
        a_tags = item.find_elements(By.TAG_NAME, "a")
        for link_elem in a_tags:
            link_url = link_elem.get_attribute("href")
            if not link_url:
                continue
            # Scrape each subpage
            scrape_subpage(driver, link_url, idx, all_data)

    driver.quit()

    # Now combine all collected text into one large content string.
    combined_content = ""
    for entry in all_data:
        if entry["type"] == "main_page_text":
            combined_content += f"Main Page ({entry.get('url')}):\n{entry.get('content', '')}\n\n"
        elif entry["type"] == "mashup_block":
            combined_content += f"Mashup Block {entry.get('block_index')}: {entry.get('block_text', '')}\n\n"
        elif entry["type"] == "subpage_text":
            combined_content += (f"Subpage (Block {entry.get('block_index')}, URL: {entry.get('subpage_url', '')}):\n"
                                 f"{entry.get('content', '')}\n\n")
        elif entry["type"] == "listing_card":
            combined_content += f"Listing Card: {entry.get('listing_text', '')}\n\n"
    
    # Use the base URL as the single key for the final JSON
    final_output = { base_url: combined_content }

    # Save the aggregated data to a JSON file
    with open("visitpittsburgh_all_combined.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"Scraping complete. Total entries collected: {len(all_data)}")
    print("Combined data saved to 'visitpittsburgh_all_combined.json'.")

if __name__ == "__main__":
    main()
