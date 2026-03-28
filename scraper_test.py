from playwright.sync_api import sync_playwright

def scrape_amazon_reviews(url):
    """Scrapes reviews from an Amazon product URL and returns them as a list."""
    scraped_reviews = []
    
    with sync_playwright() as p:
        # headless=True so it runs invisibly in the background
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        try:
            page.goto(url)
            page.wait_for_selector('[data-hook="review-body"]', timeout=8000)
            
            # Get the text and clean up whitespace
            raw_reviews = page.locator('[data-hook="review-body"]').all_inner_texts()
            scraped_reviews = [rev.strip() for rev in raw_reviews if rev.strip()]
            
        except Exception as e:
            print(f"Scraping failed: {e}")
            
        finally:
            browser.close()
            
    return scraped_reviews
