import time
import os
import subprocess
import urllib.parse
from playwright.sync_api import sync_playwright

# 1. THE URL SCRAPER (For Tab 2)
def scrape_amazon_reviews(url, max_reviews=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") # Stealth Fix
        reviews = []
        try:
            page.goto(url, wait_until="load")
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
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        reviews = []
        try:
            page.goto(url, wait_until="load")
            first_prod = page.locator('div[data-component-type="s-search-result"] a[href*="/dp/"]').first
            page.goto(f"https://www.amazon.in{first_prod.get_attribute('href')}", wait_until="load")
            elements = page.query_selector_all("[data-hook='review-body']")
            reviews = [el.inner_text().strip() for el in elements][:max_reviews]
        except Exception as e: print(f"Amazon Error: {e}")
        finally: browser.close()
        return reviews

# 3. THE FLIPKART SEARCH SCRAPER (For Tab 3)

def search_flipkart(product_name, max_reviews=10):
    search_query = urllib.parse.quote_plus(product_name)
    url = f"https://www.flipkart.com/search?q={search_query}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        reviews = []
        try:
            print(f"Searching Flipkart for: {product_name}")
            page.goto(url, wait_until="load", timeout=60000)
            time.sleep(2) 

            # Smash the Login Popup
            try:
                close_btn = page.locator("span[role='button']").first
                if close_btn.is_visible():
                    close_btn.click()
            except:
                pass 
                
            # Click the product
            first_prod = page.locator("a[href*='/p/']").first 
            product_href = first_prod.get_attribute('href')
            
            # 🥷 THE ULTIMATE TRICK: The URL Rewrite
            # We replace "/p/" with "/product-reviews/" to jump straight to the clean review page!
            review_page_href = product_href.replace("/p/", "/product-reviews/")
            full_review_url = f"https://www.flipkart.com{review_page_href}"
            
            print(f"Bypassing main page. Navigating directly to Reviews: {full_review_url}")
            page.goto(full_review_url, wait_until="load", timeout=60000)
            
            # Scroll down just slightly to make sure they render
            for _ in range(3): 
                page.keyboard.press("PageDown")
                time.sleep(0.5)
            
            # Extract raw text from the clean review page
            print("Extracting text from Dedicated Review Page...")
            raw_texts = page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('div, p, span'))
                        .filter(el => el.children.length === 0 && el.innerText.trim().length > 20)
                        .map(el => el.innerText.trim());
                }
            """)
            
            # 🧹 Because the page is clean, our junk filter can be much smaller!
            junk_phrases = [
                "Everything in Minutes", "Notification", "Advertise", "Pincode", 
                "commonly asked", "ratings by", "Read More", "Rate Product", 
                "Submit Review", "Helpful", "Certified Buyer"
            ]
            
            for text in raw_texts:
                text = text.replace("READ MORE", "").strip()
                
                is_junk = any(junk.lower() in text.lower() for junk in junk_phrases)
                
                # Lowered the length to 25 so we get normal-sized reviews back!
                if not is_junk and not text.endswith("?") and len(text) > 25:
                    if text not in reviews:
                        reviews.append(text)
                        
                if len(reviews) >= max_reviews:
                    break
                    
        except Exception as e: 
            print("\n🚨 FLIPKART CRASH REPORT 🚨")
            print(f"Error Message: {e}\n")
        finally: 
            browser.close()
            
        return reviews
