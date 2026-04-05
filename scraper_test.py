import urllib.parse
import time
from playwright.sync_api import sync_playwright

# ==========================================
# 1. THE URL SCRAPER (For Tab 2)
# ==========================================
def scrape_amazon_reviews(url, max_reviews=20):
    with sync_playwright() as p:
       browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        reviews = []
        try:
            print(f"Scraping exact URL: {url}")
            page.goto(url, wait_until="load", timeout=60000)
            
            elements = page.query_selector_all("[data-hook='review-body']")
            for el in elements:
                text = el.inner_text().strip()
                if len(text) > 20 and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
        except Exception as e:
            print(f"URL Scrape Error: {e}")
        finally:
            browser.close()
        return reviews

# ==========================================
# 2. THE AMAZON PAGINATION SCRAPER (For Tab 3)
# ==========================================
def search_amazon(product_name, max_reviews=20):
    search_query = urllib.parse.quote_plus(product_name)
    url = f"https://www.amazon.in/s?k={search_query}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        reviews = []
        try:
            print(f"Searching Amazon for: {product_name}")
            page.goto(url, wait_until="load", timeout=60000)
            
            # Click first product
            first_prod = page.locator('div[data-component-type="s-search-result"] a[href*="/dp/"]').first
            prod_href = first_prod.get_attribute('href')
            
            # 🥷 URL REWRITE: Jump straight to the dedicated review page
            review_url = f"https://www.amazon.in{prod_href}".replace("/dp/", "/product-reviews/")
            
            # 🔄 PAGINATION LOOP: Scrape Page 1, then Page 2
            for page_num in range(1, 3):
                print(f"Scraping Amazon Page {page_num}...")
                page.goto(f"{review_url}?pageNumber={page_num}", wait_until="load", timeout=60000)
                time.sleep(1)
                
                elements = page.query_selector_all("[data-hook='review-body']")
                for el in elements:
                    text = el.inner_text().strip()
                    if len(text) > 20 and text not in reviews:
                        reviews.append(text)
                    if len(reviews) >= max_reviews:
                        break
                
                if len(reviews) >= max_reviews:
                    break 
                    
        except Exception as e: 
            print(f"\n🚨 AMAZON CRASH REPORT: {e}\n")
        finally: 
            browser.close()
            
        return reviews

# ==========================================
# 3. THE FLIPKART PAGINATION SCRAPER (For Tab 3)
# ==========================================
def search_flipkart(product_name, max_reviews=20):
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
                if close_btn.is_visible(): close_btn.click()
            except:
                pass 
                
            # Click the product
            first_prod = page.locator("a[href*='/p/']").first 
            product_href = first_prod.get_attribute('href')
            
            # 🥷 URL REWRITE: Jump straight to the dedicated review page
            review_page_href = product_href.replace("/p/", "/product-reviews/")
            base_review_url = f"https://www.flipkart.com{review_page_href}"
            
            # 🔄 PAGINATION LOOP: Scrape Page 1, then Page 2
            for page_num in range(1, 3):
                print(f"Scraping Flipkart Page {page_num}...")
                page.goto(f"{base_review_url}&page={page_num}", wait_until="load", timeout=60000)
                time.sleep(1)
                
                # 🥷 DOM DESTRUCTION
                raw_texts = page.evaluate("""
                    () => {
                        document.querySelectorAll('footer, header, a').forEach(el => el.remove());
                        return Array.from(document.querySelectorAll('div, p, span'))
                            .filter(el => el.children.length === 0 && el.innerText.trim().length > 30)
                            .map(el => el.innerText.trim());
                    }
                """)
                
                # 🧹 The Master Junk Filter
                junk_phrases = [
                    "Everything in Minutes", "Notification", "Pincode", "commonly asked", 
                    "Rate Product", "Submit Review", "Helpful", "Certified Buyer", 
                    "Flipkart Customer", "Delivery by", "Valid until", "Bank Offer", 
                    "ratings and", "Review for:"
                ]
                
                for text in raw_texts:
                    text = text.replace("READ MORE", "").strip()
                    is_junk = any(junk.lower() in text.lower() for junk in junk_phrases)
                    
                    if not is_junk and not text.endswith("?"):
                        if text not in reviews:
                            reviews.append(text)
                            
                    if len(reviews) >= max_reviews:
                        break
                
                if len(reviews) >= max_reviews:
                    break 
                    
        except Exception as e: 
            print(f"\n🚨 FLIPKART CRASH REPORT: {e}\n")
        finally: 
            browser.close()
            
        return reviews
