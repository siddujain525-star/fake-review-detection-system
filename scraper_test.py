import time
import os
import subprocess
from playwright.sync_api import sync_playwright

def scrape_amazon_reviews(url, max_reviews=20):
    # 1. Ensure Playwright is installed on the server
    try:
        if not os.path.exists("/tmp/playwright_installed"):
            subprocess.run(["playwright", "install", "chromium"], check=True)
            with open("/tmp/playwright_installed", "w") as f:
                f.write("done")
    except Exception as e:
        print(f"Playwright install note: {e}")

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        
        # 2. Mimic a real laptop browser (Crucial to avoid blocks)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = context.new_page()
        
        reviews = []
        try:
            # 3. Use 'domcontentloaded' to speed up initial hit
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 4. Scroll down to trigger lazy-loaded reviews (Very important)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(3) 

            # 5. Use multiple possible selectors (Amazon changes these often)
            # This checks for the main review body and common fallbacks
            selectors = [
                "[data-hook='review-body']", 
                ".review-text-content", 
                "span.a-size-base.review-text"
            ]
            
            # Combine selectors for a "wide net" search
            combined_selector = ", ".join(selectors)
            elements = page.query_selector_all(combined_selector)
            
            for el in elements:
                text = el.inner_text().strip()
                # Filter out very short text (likely buttons or labels)
                if len(text) > 15 and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
                    
        except Exception as e:
            print(f"Scraping error: {e}")
        finally:
            browser.close()
            
        return reviews
