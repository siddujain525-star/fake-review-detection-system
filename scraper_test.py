import time
from playwright.sync_api import sync_playwright
import os
import subprocess

def scrape_amazon_reviews(url, max_reviews=50):
    # --- ADD THIS START ---
    # This checks if the browser is installed; if not, it installs it on the server
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Playwright install note: {e}")
    # --- ADD THIS END ---

    with sync_playwright() as p:
        # rest of your code...
def scrape_amazon_reviews(url, max_reviews=50):
    with sync_playwright() as p:
        # 1. Launch Browser (Stealthy)
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent="Mozilla/5.0...").new_page()
        
        # 2. Go to Product Page
        page.goto(url)
        time.sleep(2)

        # 3. Click "See all reviews" to get more than just the Top 8
        try:
            all_reviews_link = page.query_selector("a[data-hook='see-all-reviews-link-foot']")
            if all_reviews_link:
                all_reviews_link.click()
                page.wait_for_load_state("networkidle")
        except:
            pass # Stay on main page if link isn't found

        reviews = []
        
        # 4. Loop through pages until we hit max_reviews
        while len(reviews) < max_reviews:
            # Find all review bodies on current page
            elements = page.query_selector_all("[data-hook='review-body']")
            for el in elements:
                text = el.inner_text().strip()
                if text and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
            
            # Try to click "Next Page"
            next_button = page.query_selector("li.a-last a")
            if next_button and len(reviews) < max_reviews:
                next_button.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1) # Small delay to avoid bot detection
            else:
                break # No more pages

        browser.close()
        return reviews[:max_reviews]
