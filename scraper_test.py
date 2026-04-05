import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync # Added stealth

def search_amazon(product_name, max_reviews=10):
    search_query = urllib.parse.quote_plus(product_name)
    # 1. Use a more direct search URL
    url = f"https://www.amazon.in/s?k={search_query}&ref=nb_sb_noss"
    
    with sync_playwright() as p:
        # CRITICAL: Must be headless=True
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page) # Enable stealth to bypass bot detection
        
        reviews = []
        try:
            # Navigate with a longer timeout
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(random.uniform(2, 4)) # Wait for lazy elements
            
            # 2. Flexible selector: look for ANY link that contains '/dp/' (product link)
            # This is more reliable than the complex 's-search-result' div
            product_link_element = page.locator('a[href*="/dp/"]').first
            
            if product_link_element.count() == 0:
                print("Amazon blocked search results or no products found.")
                return []
                
            raw_href = product_link_element.get_attribute('href')
            # Build the direct Review Page URL immediately
            # This bypasses the heavy product page entirely
            product_id = raw_href.split('/dp/')[1].split('/')[0].split('?')[0]
            review_url = f"https://www.amazon.in/product-reviews/{product_id}/"
            
            print(f"Jumping straight to Review Page: {review_url}")
            page.goto(review_url, wait_until="networkidle", timeout=60000)
            
            # 3. Wait for the review body
            page.wait_for_selector("[data-hook='review-body']", timeout=15000)
            
            elements = page.query_selector_all("[data-hook='review-body']")
            reviews = [el.inner_text().strip() for el in elements][:max_reviews]
            
        except Exception as e: 
            print(f"Amazon Search Error: {e}")
        finally: 
            browser.close()
        return reviews
