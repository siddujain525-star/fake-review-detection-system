import time
import os
import subprocess
from playwright.sync_api import sync_playwright

def scrape_amazon_reviews(url, max_reviews=50):
    # 1. Install the browser on the Streamlit server if missing
    try:
        if not os.path.exists("/tmp/playwright_installed"):
            subprocess.run(["playwright", "install", "chromium"], check=True)
            with open("/tmp/playwright_installed", "w") as f:
                f.write("done")
    except Exception as e:
        print(f"Playwright install note: {e}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 2. ADDED: Real headers and viewport to look like a real laptop
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = context.new_page()
        
        try:
            # 3. UPDATED: Wait for the page to actually load
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            # Click "See all reviews"
            all_reviews_link = page.query_selector("a[data-hook='see-all-reviews-link-foot']")
            if all_reviews_link:
                all_reviews_link.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)
        except Exception as e:
            print(f"Navigation error: {e}")

        reviews = []
        
        while len(reviews) < max_reviews:
            # 4. UPDATED: Multi-selector (checks 3 different ways Amazon hides reviews)
            elements = page.query_selector_all("[data-hook='review-body'], .review-text-content, span.a-size-base.review-text")
            
            for el in elements:
                text = el.inner_text().strip()
                # Filter out very short or duplicate text
                if len(text) > 15 and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
            
            # Check for "Next Page"
            next_button = page.query_selector("li.a-last a")
            if next_button and len(reviews) < max_reviews:
                try:
                    next_button.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(2) # Increased delay to avoid bot detection
                except:
                    break
            else:
                break 

        browser.close()
        return reviews[:max_reviews]
