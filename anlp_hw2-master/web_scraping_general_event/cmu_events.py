import time
import json
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Global list to store events
all_events = []

def get_text_by_class(driver, class_name):
    """
    Helper function to find an element by class name
    and return its text (or an empty string if not found).
    """
    try:
        elem = driver.find_element(By.CLASS_NAME, class_name)
        return elem.text.strip()
    except:
        return ""

def scrape_event_detail(driver, detail_url):
    """
    Opens the event detail page in a new tab, waits briefly,
    and scrapes text from several containers:
      - lw_cal_event_leftcol
      - lw_cal_event_rightcol
      - lw_calendar_event_description
      - lw_cal_event_group
    Returns a tuple (event_title, combined_text).
    """
    driver.execute_script("window.open(arguments[0]);", detail_url)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)  # Wait for the detail page to load

    try:
        event_title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        event_title = "No Title Found"

    leftcol_text = get_text_by_class(driver, "lw_cal_event_leftcol")
    rightcol_text = get_text_by_class(driver, "lw_cal_event_rightcol")
    desc_text = get_text_by_class(driver, "lw_calendar_event_description")
    group_text = get_text_by_class(driver, "lw_cal_event_group")

    combined_text = "\n".join([leftcol_text, rightcol_text, desc_text, group_text]).strip()

    # Close detail tab and return to the main window
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)

    return (event_title, combined_text)

def scrape_day_events(driver, day_url, day_str):
    """
    Loads the day URL (e.g. "https://events.cmu.edu/day/date/20250320"),
    finds the event list, and for each event opens the detail page to scrape text.
    Each event's information is appended to all_events.
    """
    driver.get(day_url)
    time.sleep(3)  # Allow the day page to load

    try:
        event_list_container = driver.find_element(By.CLASS_NAME, "lw_cal_event_list")
    except:
        print(f"No events found for {day_str}")
        return

    # Each event has a title element with class "lw_events_title" containing an <a> link.
    title_elements = event_list_container.find_elements(By.CLASS_NAME, "lw_events_title")
    for title_elem in title_elements:
        try:
            link_elem = title_elem.find_element(By.TAG_NAME, "a")
            detail_url = link_elem.get_attribute("href")
            day_view_title = title_elem.text.strip() or "No Title"
            
            # Scrape the event detail page
            event_title, detail_text = scrape_event_detail(driver, detail_url)
            
            # Append event data, including its detail URL in the content
            all_events.append({
                "date": day_str,
                "day_view_title": day_view_title,
                "event_title": event_title,
                "detail_url": detail_url,
                "details": detail_text
            })
        except Exception as e:
            print("Error scraping event link:", e)
            time.sleep(1)

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Date range: March 20, 2025 to September 30, 2025
    start_date = date(2025, 3, 20)
    end_date = date(2025, 9, 30)
    current_date = start_date

    while current_date <= end_date:
        day_str = current_date.strftime("%Y%m%d")
        day_url = f"https://events.cmu.edu/day/date/{day_str}"
        print(f"Scraping {day_url}")
        scrape_day_events(driver, day_url, day_str)
        current_date += timedelta(days=1)

    driver.quit()

    # Combine all events into a single content string
    final_content = ""
    for event in all_events:
        final_content += f"Date: {event['date']}\n"
        final_content += f"Day View Title: {event['day_view_title']}\n"
        final_content += f"Event Title: {event['event_title']}\n"
        final_content += f"Detail URL: {event['detail_url']}\n"
        final_content += f"Details:\n{event['details']}\n"
        final_content += "-" * 40 + "\n"

    # Use the main URL as the key and store the combined content as its value.
    final_output = {
        "https://events.cmu.edu": final_content
    }

    with open("cmu_events.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"Done. Collected {len(all_events)} events.")

if __name__ == "__main__":
    main()
