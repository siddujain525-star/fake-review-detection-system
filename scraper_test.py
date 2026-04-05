import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync  # Corrected Import

# 1. THE URL SCRAPER (For Tab 2)
def scrape_amazon_reviews(url, max_reviews=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page) # Apply stealth
        
        reviews = []
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("[data-hook='review-body']", timeout=15000)
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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)
        
        reviews = []
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(random.uniform(2, 4))
            
            # Find the first product link
            product_link_element = page.locator('a[href*="/dp/"]').first
            if product_link_element.count() == 0:
                return []
                
            raw_href = product_link_element.get_attribute('href')
            
            # Extract ASIN (Product ID) to build a clean Review URL
            # This bypasses the heavy main page which often triggers CAPTCHAs
            if "/dp/" in raw_href:
                asin = raw_href.split("/dp/")[1].split("/")[0].split("?")[0]
                review_url = f"https://www.amazon.in/product-reviews/{asin}/"
                
                print(f"Jumping to Amazon Reviews: {review_url}")
                page.goto(review_url, wait_until="networkidle", timeout=60000)
                
                page.wait_for_selector("[data-hook='review-body']", timeout=15000)
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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)
        
        reviews = []
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Close popup
            try:
                close_btn = page.locator("span:has-text('✕'), span[role='button']").first
                if close_btn.is_visible(timeout=3000):
                    close_btn.click()
            except:
                pass 
                
            page.wait_for_selector("a[href*='/p/']", timeout=10000)
            first_prod = page.locator("a[href*='/p/']").first 
            product_href = first_prod.get_attribute('href')
            
            review_page_href = product_href.replace("/p/", "/product-reviews/")
            full_review_url = f"https://www.flipkart.com{review_page_href}"
            
            page.goto(full_review_url, wait_until="networkidle", timeout=60000)
            page.mouse.wheel(0, 1500)
            time.sleep(1)
            
            raw_texts = page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('div, p, span'))
                        .filter(el => el.children.length === 0 && el.innerText.trim().length > 20)
                        .map(el => el.innerText.trim());
                }
            """)
            
            junk_phrases = ["Minutes", "Notification", "Advertise", "Pincode", "Read More", "Buyer"]
            
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
