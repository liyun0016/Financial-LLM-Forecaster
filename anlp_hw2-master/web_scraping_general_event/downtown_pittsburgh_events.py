import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# We'll scrape from March 20, 2025, through December 31, 2025
START_MONTH = 3
END_MONTH = 12
YEAR = 2025
START_DAY_MARCH = 20  # For March, skip days < 20

def month_name(m):
    import calendar
    return calendar.month_name[m]  # e.g. 3 -> "March"

def get_displayed_month_year(driver):
    """
    Return the current month-year string displayed by the site's calendar,
    e.g. 'March 2025'. Adjust the selector as needed.
    """
    try:
        month_elem = driver.find_element(By.ID, "month_button")
        return month_elem.text.strip()  # or month_elem.get_attribute("value")
    except:
        return ""

def click_next_month(driver):
    """Click the 'next month' button to advance the calendar."""
    try:
        next_btn = driver.find_element(By.CLASS_NAME, "monthpicker-next")
        next_btn.click()
        time.sleep(2)
    except:
        pass

def select_month(driver, target_month, target_year):
    """
    Clicks 'next month' until the displayed calendar matches
    something like 'March 2025'.
    """
    import calendar
    desired_text = f"{calendar.month_name[target_month]} {target_year}".lower()
    for _ in range(24):  # safety limit
        displayed = get_displayed_month_year(driver).lower()
        if desired_text in displayed:
            return
        click_next_month(driver)

def scrape_day_events(driver, month_num, day_num, all_events):
    """
    For a given month/day, find that day's block, click it,
    gather event links, open each event page, scrape text,
    then return to the month view.
    """
    # 1) Find the day block with text matching day_num
    day_blocks = driver.find_elements(By.CSS_SELECTOR, "div.calDayIcon.eventDay")
    day_block = None
    for db in day_blocks:
        txt = db.text.strip()
        if txt.isdigit() and int(txt) == day_num:
            day_block = db
            break

    if not day_block:
        # Possibly the day is out-of-month or there's no events
        return

    # 2) Click the day block
    day_block.click()
    time.sleep(2)

    # 3) Gather event links from the day page
    event_link_elems = driver.find_elements(By.CSS_SELECTOR, "div.eventitem h1 a")
    event_links = [elem.get_attribute("href") for elem in event_link_elems]

    # 4) For each event link, open the page, scrape text from "div.eventitem"
    for link in event_links:
        try:
            driver.get(link)
            time.sleep(2)

            # Gather all text from any <div class="eventitem"> on this page
            event_divs = driver.find_elements(By.CSS_SELECTOR, "div.eventitem")
            text_parts = [div.text.strip() for div in event_divs]
            full_text = "\n".join(text_parts).strip()

            data = {
                "date": f"{YEAR}-{month_num:02d}-{day_num:02d}",
                "event_page_url": link,
                "details": full_text
            }
            all_events.append(data)

            # Go back to the day page
            driver.back()
            time.sleep(2)

        except Exception as e:
            print(f"Error scraping event detail on {YEAR}-{month_num:02d}-{day_num:02d}: {e}")
            try:
                driver.back()
            except:
                pass
            time.sleep(2)

    # 5) Return to the month view
    driver.back()
    time.sleep(2)

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 1) Open the main events page
    main_url = "https://downtownpittsburgh.com/events/"
    driver.get(main_url)
    time.sleep(3)

    all_events = []

    # 2
