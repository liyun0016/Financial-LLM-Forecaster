import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def main():
    # 1. Configure Selenium WebDriver (headless mode)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 2. Load the main page
    base_url = "https://www.cmu.edu/engage/alumni/events/campus/index.html"
    driver.get(base_url)
    time.sleep(3)  # Allow the page to load
    
    all_events = []
    
    try:
        # 3. Locate the container with class="grid column3 darkgrey boxes js-list"
        container = driver.find_element(By.CSS_SELECTOR, "div.grid.column3.darkgrey.boxes.js-list")
    except Exception as e:
        print("Could not find the container:", e)
        driver.quit()
        return
    
    # 4. Extract all <a> links from that container
    link_elems = container.find_elements(By.TAG_NAME, "a")
    print(f"Found {len(link_elems)} links in the container.")
    
    for idx, link_elem in enumerate(link_elems, start=1):
        try:
            link_url = link_elem.get_attribute("href")
            link_text = link_elem.text.strip() or f"Event {idx}"
            if not link_url:
                continue
            
            # 5. Open each link in a new tab
            driver.execute_script("window.open(arguments[0]);", link_url)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            
            # 6. Scrape text from element with class "content"
            try:
                content_elem = driver.find_element(By.CLASS_NAME, "content")
                content_text = content_elem.text.strip()
            except:
                content_text = "No Content Found"
            
            # Optionally get the page title from the detail page
            try:
                page_title = driver.title.strip()
            except:
                page_title = link_text
            
            # 7. Append the event details to the list
            all_events.append({
                "link_text": link_text,
                "page_title": page_title,
                "detail_url": link_url,
                "content": content_text
            })
            
            # Close the detail tab and switch back to the main page
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
        except Exception as e:
            print(f"Error scraping link {idx}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
    
    driver.quit()
    
    # Combine all events into one content string
    final_content = ""
    for event in all_events:
        final_content += f"Link Text: {event['link_text']}\n"
        final_content += f"Page Title: {event['page_title']}\n"
        final_content += f"Detail URL: {event['detail_url']}\n"
        final_content += f"Content:\n{event['content']}\n"
        final_content += "-" * 40 + "\n"
    
    # Use the main URL as the key, and combined events as the value
    final_output = { base_url: final_content }
    
    # Save results to JSON
    with open("cmu_alumni_events.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)
    
    print(f"Scraping complete. Combined content for {len(all_events)} events saved under key '{base_url}'.")

if __name__ == "__main__":
    main()
