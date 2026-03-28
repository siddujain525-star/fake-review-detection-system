def scrape_flipkart_reviews(url, max_reviews=10):
    # (The Playwright install logic at the top of your file handles the server setup)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a real user agent to prevent being blocked
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = context.new_page()
        
        reviews = []
        try:
            # Flipkart pages can be heavy; we wait for the network to be quiet
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(2)

            # --- FLIPKART MULTI-SELECTORS ---
            # These are the most common classes Flipkart uses for review text
            selectors = [
                "div.ZmyHeo",            # Common for full review text
                "div.t-ZTKy",            # Older but still active class
                "div._6K-7S8",           # Found in some mobile views
                "div.row._3wYu6I"        # Container based selector
            ]
            
            # Combine selectors into one string for Playwright
            combined_selector = ", ".join(selectors)
            elements = page.query_selector_all(combined_selector)
            
            for el in elements:
                text = el.inner_text().strip()
                # Flipkart often adds a "READ MORE" button inside the text; we clean it
                if "READ MORE" in text:
                    text = text.replace("READ MORE", "").strip()
                
                if len(text) > 15 and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
                    
        except Exception as e:
            print(f"Flipkart Scrape Error: {e}")
        finally:
            browser.close()
            
        return reviews
import time
import os
import subprocess
from playwright.sync_api import sync_playwright

def scrape_amazon_reviews(url, max_reviews=10):
    # 1. Quick Install Check
    try:
        if not os.path.exists("/tmp/playwright_installed"):
            subprocess.run(["playwright", "install", "chromium"], check=True)
            with open("/tmp/playwright_installed", "w") as f:
                f.write("done")
    except Exception as e:
        print(f"Install note: {e}")

    # 2. Simple Scrape (Stay on main page)
    with sync_playwright() as p:
        # Launch with no extra plugins to keep it simple
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        reviews = []
        try:
            # Go directly to the product page
            page.goto(url, wait_until="load", timeout=60000)
            time.sleep(2) # Wait for reviews to render

            # Use the most common Amazon review selector
            elements = page.query_selector_all("[data-hook='review-body']")
            
            for el in elements:
                text = el.inner_text().strip()
                if text and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
        except Exception as e:
            print(f"Scrape Error: {e}")
        finally:
            browser.close()
            
        return reviews
