#scraping tenipo.com
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://tenipo.com/livescore")
    time.sleep(3)
    content = page.content()
    print(content)
    time.sleep(120)
    browser.close()