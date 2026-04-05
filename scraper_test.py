import time
import os
import subprocess
import urllib.parse
from playwright.sync_api import sync_playwright

# 1. THE URL SCRAPER (For Tab 2)
def scrape_amazon_reviews(url, max_reviews=10):
    with sync_playwright() as p:
        # Changed to headless=True for Cloud Compatibility
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
        reviews = []
        try:
            page.goto(url, wait_until="load", timeout=60000)
            elements = page.query_selector_all("[data-hook='review-body']")
            reviews = [el.inner_text().strip() for el in elements][:max_reviews]
        except Exception as e:
            print(f"Scrape Error: {e}")
        finally:
            browser.close()
        return reviews

# 2. THE AMAZON SEARCH SCRAPER (For Tab 3)
def search_amazon(product_name, max_reviews=10):
    search_query = urllib.parse.quote_plus(product_name)
    url = f"https://www.amazon.in/s?k={search_query}"
    with sync_playwright() as p:
        # FIX: Changed headless=False to True and removed slow_mo
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        reviews = []
        try:
            page.goto(url, wait_until="load", timeout=60000)
            first_prod = page.locator('div[data-component-type="s-search-result"] a[href*="/dp/"]').first
            product_link = f"https://www.amazon.in{first_prod.get_attribute('href')}"
            page.goto(product_link, wait_until="load", timeout=60000)
            elements = page.query_selector_all("[data-hook='review-body']")
            reviews = [el.inner_text().strip() for el in elements][:max_reviews]
        except Exception as e: 
            print(f"Amazon Search Error: {e}")
        finally: 
            browser.close()
        return reviews

# 3. THE FLIPKART SEARCH SCRAPER (For Tab 3)
def search_flipkart(product_name, max_reviews=10):
    search_query = urllib.parse.quote_plus(product_name)
    url = f"https://www.flipkart.com/search?q={search_query}"
    
    with sync_playwright() as p:
        # FIX: Changed headless=False to True and removed slow_mo
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        reviews = []
        try:
            page.goto(url, wait_until="load", timeout=60000)
            
            # Close login popup if it appears
            try:
                close_btn = page.locator("span:has-text('✕'), span[role='button']").first
                if close_btn.is_visible(timeout=3000):
                    close_btn.click()
            except:
                pass 
                
            # Click the product
            first_prod = page.locator("a[href*='/p/']").first 
            product_href = first_prod.get_attribute('href')
            
            # Rewrite URL to jump directly to reviews
            review_page_href = product_href.replace("/p/", "/product-reviews/")
            full_review_url = f"https://www.flipkart.com{review_page_href}"
            
            page.goto(full_review_url, wait_until="load", timeout=60000)
            
            # Minor scroll for rendering
            page.mouse.wheel(0, 1000)
            time.sleep(1)
            
            # Extract review text using your optimized Evaluate script
            raw_texts = page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('div, p, span'))
                        .filter(el => el.children.length === 0 && el.innerText.trim().length > 20)
                        .map(el => el.innerText.trim());
                }
            """)
            
            junk_phrases = [
                "Everything in Minutes", "Notification", "Advertise", "Pincode", 
                "commonly asked", "ratings by", "Read More", "Rate Product", 
                "Submit Review", "Helpful", "Certified Buyer"
            ]
            
            for text in raw_texts:
                text = text.replace("READ MORE", "").strip()
                is_junk = any(junk.lower() in text.lower() for junk in junk_phrases)
                
                if not is_junk and not text.endswith("?") and len(text) > 25:
                    if text not in reviews:
                        reviews.append(text)
                        
                if len(reviews) >= max_reviews:
                    break
                    
        except Exception as e: 
            print(f"Flipkart Search Error: {e}")
        finally: 
            browser.close()
            
        return reviews
