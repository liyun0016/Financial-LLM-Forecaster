import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def scrape_pgh_citypaper_events():
    """
    Scrapes events from Pittsburgh City Paper for the date range
    2025-03-20 to 2025-12-31 across 20 pages.
    Each event is listed under:
      <ul class="pres-EventSearchRectangle uk-list uk-list-divider uk-flex@show-grid">
    and each event is in:
      <li class="fdn-pres-item uk-child-width-1-1@show-grid">
    For each event, the detail page URL is extracted from an <a> tag (preferring one inside an <h1> if present).
    On the event detail page, all text under elements with class "ev-grid-col" is scraped.
    The final JSON output is in the format { "url": "content" } using one key.
    """
    
    # Set up Selenium WebDriver in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(5)  # Implicit wait
    
    # Base URL for the date range (used later as the key)
    base_url = ("https://www.pghcitypaper.com/pittsburgh/"
                "EventSearch?narrowByDate=2025-03-20-to-2025-12-31&sortType=date&v=d")
    
    total_pages = 20
    all_events = []
    
    # Loop over pages 1 to 20
    for page_num in range(1, total_pages + 1):
        page_url = f"{base_url}&page={page_num}"
        print(f"Visiting page {page_num} of {total_pages}: {page_url}")
        driver.get(page_url)
        time.sleep(3)  # Allow page to render
        
        # Parse the listing page using BeautifulSoup
        listing_html = driver.page_source
        soup = BeautifulSoup(listing_html, "html.parser")
        
        ul_element = soup.find("ul", class_="pres-EventSearchRectangle")
        if not ul_element:
            print(f"Could not find the event list on page {page_num}.")
            continue
        
        li_elements = ul_element.find_all("li", class_="fdn-pres-item")
        print(f"Found {len(li_elements)} events on page {page_num}.")
        
        for idx, li_elem in enumerate(li_elements, start=1):
            try:
                listing_text = li_elem.get_text(separator=" ", strip=True)
                
                # Attempt to find the event link from an <h1>; if not, fallback to first <a>
                h1_elem = li_elem.find("h1")
                if h1_elem:
                    a_tag = h1_elem.find("a", href=True)
                else:
                    a_tag = li_elem.find("a", href=True)
                    
                if not a_tag:
                    print(f"No event link found for event {idx} on page {page_num}.")
                    continue
                
                detail_url = a_tag["href"]
                
                # Open the event detail page in a new tab
                driver.execute_script("window.open(arguments[0]);", detail_url)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)
                
                # Parse the event detail page
                detail_html = driver.page_source
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                
                # Extract text from all elements with class "ev-grid-col"
                ev_grid_divs = detail_soup.find_all("div", class_="ev-grid-col")
                detail_text_parts = [div.get_text(separator="\n", strip=True) for div in ev_grid_divs]
                detail_text = "\n".join(detail_text_parts).strip()
                
                event_data = {
                    "page_number": page_num,
                    "index_on_page": idx,
                    "listing_text": listing_text,
                    "detail_url": detail_url,
                    "detail_text": detail_text
                }
                all_events.append(event_data)
                
                # Close the detail tab and return to the listing page
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
            
            except Exception as e:
                print(f"Error scraping event on page {page_num}, item {idx}: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                continue
    
    driver.quit()
    
    # Combine all events into one content string
    combined_content = ""
    for event in all_events:
        combined_content += f"Page Number: {event.get('page_number', 'N/A')}\n"
        combined_content += f"Index on Page: {event.get('index_on_page', 'N/A')}\n"
        combined_content += f"Listing Text: {event.get('listing_text', '')}\n"
        combined_content += f"Detail URL: {event.get('detail_url', 'No link')}\n"
        combined_content += f"Detail Text: {event.get('detail_text', '')}\n"
        combined_content += "-" * 40 + "\n"
    
    # Use the main search URL as the key for the final output
    final_output = { base_url: combined_content }
    
    with open("citypaper_events.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)
    
    print(f"Scraping complete. Total events scraped: {len(all_events)}")

if __name__ == "__main__":
    scrape_pgh_citypaper_events()
