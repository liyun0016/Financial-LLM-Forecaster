import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URL
BASE_URL = "https://pittsburgh.events"

# Set up Selenium WebDriver (Headless Mode)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run without opening browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the webpage
driver.get(BASE_URL)
time.sleep(3)  # Allow JavaScript to load content

# Click "Show More" button until all events are loaded
while True:
    try:
        show_more_button = driver.find_element(By.CLASS_NAME, "ldm")  # Locate the button
        if show_more_button.is_displayed():
            show_more_button.click()
            time.sleep(2)  # Wait for new events to load
        else:
            break  # Stop when button is no longer visible
    except:
        break  # Stop when button is no longer found

# Get the updated HTML after all events are loaded
page_source = driver.page_source
soup = BeautifulSoup(page_source, "html.parser")

# Close Selenium WebDriver
driver.quit()

# Scrape all events from the fully loaded page
events = []
event_containers = soup.find_all("li", class_="date-row")

for event in event_containers:
    try:
        # Extract date, time, title, location, and ticket price
        date = event.find("div", class_="date").text.strip() if event.find("div", class_="date") else "No date"
        time_ = event.find("div", class_="time").text.strip() if event.find("div", class_="time") else "No time"
        title = event.find("div", class_="venue").text.strip() if event.find("div", class_="venue") else "No title"
        location = event.find("span", class_="location").text.strip() if event.find("span", class_="location") else "No location"

        # Extract event link
        event_link_tag = event.find("a", href=True)
        event_link = urljoin(BASE_URL, event_link_tag["href"]) if event_link_tag else "No link"

        # Extract ticket price (if available)
        price_tag = event.find("div", class_="from-price")
        ticket_price = price_tag.text.replace("Prices from", "").strip() if price_tag else "No price"

        # Store event details
        events.append({
            "date": date,
            "time": time_,
            "title": title,
            "location": location,
            "ticket_price": ticket_price,
            "event_link": event_link,
        })

    except Exception as e:
        print(f"Error parsing an event: {e}")

print(f"Found {len(events)} events.")

# Save to JSON file
with open("pittsburgh_events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, indent=4, ensure_ascii=False)
