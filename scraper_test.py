import time
import os
import random
import urllib.parse
from playwright.sync_api import sync_playwright

# 1. THE URL SCRAPER (For Tab 2)
def scrape_amazon_reviews(url, max_reviews=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
        reviews = []
        try:
            # Navigate to the URL and wait for the network to settle
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Ensure review elements are actually present
            page.wait_for_selector("[data-hook='review-body']", timeout=10000)
            
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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        reviews = []
        try:
            # 1. Search Page
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(random.uniform(1, 3)) # Human mimicry
            
            # Wait for search results
            page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=10000)
            first_prod = page.locator('div[data-component-type="s-search-result"] a[href*="/dp/"]').first
            product_path = first_prod.get_attribute('href')
            
            # 2. THE SECRET WEAPON: Jump straight to the dedicated Reviews page
            # This is much harder for Amazon to block than the main product page
            review_url = f"https://www.amazon.in{product_path}".split('?')[0].replace("/dp/", "/product-reviews/")
            
            print(f"Jumping to Amazon Reviews: {review_url}")
            page.goto(review_url, wait_until="networkidle", timeout=60000)
            
            # 3. Wait for reviews to appear
            page.wait_for_selector("[data-hook='review-body']", timeout=10000)
            
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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        reviews = []
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Close login popup
            try:
                close_btn = page.locator("span:has-text('✕'), span[role='button']").first
                if close_btn.is_visible(timeout=3000):
                    close_btn.click()
            except:
                pass 
                
            # Click the product
            page.wait_for_selector("a[href*='/p/']", timeout=10000)
            first_prod = page.locator("a[href*='/p/']").first 
            product_href = first_prod.get_attribute('href')
            
            # Jump straight to reviews
            review_page_href = product_href.replace("/p/", "/product-reviews/")
            full_review_url = f"https://www.flipkart.com{review_page_href}"
            
            page.goto(full_review_url, wait_until="networkidle", timeout=60000)
            
            # Scroll to trigger lazy loading
            page.mouse.wheel(0, 1500)
            time.sleep(1)
            
            raw_texts = page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('div, p, span'))
                        .filter(el => el.children.length === 0 && el.innerText.trim().length > 20)
                        .map(el => el.innerText.trim());
                }
            """)
            
            junk_phrases = ["Everything in Minutes", "Notification", "Advertise", "Pincode", "Read More", "Certified Buyer"]
            
            for text in raw_texts:
                text = text.replace("READ MORE", "").strip()
                is_junk = any(junk.lower() in text.lower() for junk in junk_phrases)
                
                if not is_junk and len(text) > 25:
                    if text not in reviews:
                        reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
                    
        except Exception as e: 
            print(f"Flipkart Search Error: {e}")
        finally: 
            browser.close()
            
        return reviews
