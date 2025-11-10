# Scraper Implementation Guide

This guide will help you implement the scrapers for Adidas, Running Warehouse, and Dick's Sporting Goods.

## The Challenge

Modern e-commerce websites use:
- **JavaScript rendering** (React, Next.js, etc.) - content loads after page loads
- **Bot protection** (Cloudflare, PerimeterX) - blocks automated requests
- **Dynamic content** - prices and products load via AJAX/API calls

This means **basic HTTP requests with BeautifulSoup won't work** for most sites.

## Solution: Use Selenium

Selenium automates a real browser, which renders JavaScript and appears more human-like.

### Step 1: Install Selenium

```bash
pip install selenium undetected-chromedriver
```

Update `requirements.txt`:
```bash
echo "selenium==4.16.0" >> requirements.txt
echo "undetected-chromedriver==3.5.5" >> requirements.txt
```

### Step 2: Create a Selenium Helper

I'll create a helper class that uses Selenium instead of requests.

Create `src/scrapers/selenium_scraper.py`:

```python
"""Base scraper using Selenium for JavaScript-heavy sites."""

from typing import Optional
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from .base_scraper import BaseScraper


class SeleniumScraper(BaseScraper):
    """Base scraper that uses Selenium for JavaScript-rendered sites."""

    def __init__(self):
        super().__init__()
        self.driver = None

    def init_driver(self):
        """Initialize the Selenium WebDriver."""
        if self.driver is None:
            options = uc.ChromeOptions()
            options.add_argument('--headless')  # Run without GUI
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')

            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch page using Selenium."""
        try:
            self.init_driver()
            self.logger.info(f"Fetching with Selenium: {url}")

            self.driver.get(url)

            # Wait for products to load (adjust selector as needed)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div"))
            )

            # Additional wait for dynamic content
            time.sleep(3)

            # Get the rendered HTML
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # Be polite - add delay
            time.sleep(2)

            return soup

        except Exception as e:
            self.logger.error(f"Error fetching {url} with Selenium: {e}")
            return None

    def close(self):
        """Close the Selenium driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        super().close()
```

### Step 3: Update Your Scrapers to Inherit from SeleniumScraper

Change the scraper classes from:
```python
class AdidasScraper(BaseScraper):
```

To:
```python
from .selenium_scraper import SeleniumScraper

class AdidasScraper(SeleniumScraper):
```

### Step 4: Find the Correct CSS Selectors

For each website, you need to inspect the HTML and find the right selectors:

#### Method 1: Manual Inspection (Recommended)

1. **Open the website in Chrome**
   ```
   https://www.adidas.com/us/running-shoes-sale
   ```

2. **Open Developer Tools** (F12 or Right-click → Inspect)

3. **Find a product card**
   - Right-click on a product → "Inspect Element"
   - Look at the HTML structure
   - Note the container div class/attributes

4. **Find each element:**
   - Product name
   - Price (regular and sale)
   - Product URL
   - Image URL
   - Product ID (often in data-product-id or similar)

5. **Update the selectors in the scraper**

Example for Adidas (you need to verify):
```python
# If products are in: <div class="glass-product-card">
product_containers = soup.select('div.glass-product-card')

# If name is in: <p class="glass-product-card__title">
name_elem = container.select_one('p.glass-product-card__title')

# If sale price is in: <div class="gl-price-item gl-price-item--sale">
sale_price_elem = container.select_one('.gl-price-item--sale')
```

#### Method 2: Use Selenium to Save the Page

```python
# Run this script to save rendered HTML for inspection
import undetected_chromedriver as uc

driver = uc.Chrome()
driver.get('https://www.adidas.com/us/running-shoes-sale')
import time
time.sleep(5)  # Wait for page to load

with open('adidas_page.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)

driver.quit()

# Now open adidas_page.html and inspect it
```

### Step 5: Test Your Scraper

Create a test script `test_scraper.py`:

```python
#!/usr/bin/env python3
"""Test individual scrapers."""

import logging
from src.scrapers.adidas_scraper import AdidasScraper

# Setup logging
logging.basicConfig(level=logging.INFO)

# Test Adidas scraper
scraper = AdidasScraper()
shoes = scraper.scrape()

print(f"\nFound {len(shoes)} shoes")
for shoe in shoes[:5]:  # Show first 5
    print(f"\n{shoe['name']}")
    print(f"  Price: ${shoe['current_price']}")
    if shoe['is_on_sale']:
        print(f"  Original: ${shoe['original_price']} ({shoe['discount_percentage']}% off)")
    print(f"  URL: {shoe['url']}")

scraper.close()
```

Run it:
```bash
python test_scraper.py
```

## Alternative: API Endpoints

Some sites expose internal APIs that are easier to work with:

### Finding API Endpoints

1. Open Developer Tools → Network tab
2. Filter by "Fetch/XHR"
3. Browse the website
4. Look for API calls returning JSON with product data
5. Use those endpoints directly (might need API keys/tokens)

Example for a hypothetical API:
```python
import requests

response = requests.get(
    'https://www.example.com/api/products',
    params={'category': 'running-shoes', 'on_sale': 'true'},
    headers={'User-Agent': 'Mozilla/5.0...'}
)

products = response.json()
```

## Specific Tips for Each Site

### Adidas
- Uses React/Next.js heavily
- Product data might be in `<script id="__NEXT_DATA__">` as JSON
- Consider extracting from that JSON instead of HTML

### Running Warehouse
- Older site, might work with basic requests
- Try the basic scraper first before Selenium
- Check robots.txt: https://www.runningwarehouse.com/robots.txt

### Dick's Sporting Goods
- Heavy bot protection
- Definitely needs Selenium
- Mobile site might be easier: m.dickssportinggoods.com

## Ethical Considerations

1. **Respect robots.txt**
   ```bash
   curl https://www.adidas.com/robots.txt
   ```

2. **Use appropriate delays**
   - Don't overwhelm servers
   - 2-5 seconds between requests minimum

3. **Check Terms of Service**
   - Some sites explicitly forbid scraping
   - Consider reaching out for permission or API access

4. **Use for personal purposes only**
   - Don't redistribute data
   - Don't use for commercial purposes without permission

## Troubleshooting

### Selenium Not Working
```bash
# Update Chrome and undetected-chromedriver
pip install --upgrade undetected-chromedriver
```

### Bot Detection
- Use residential proxies (services like Bright Data)
- Rotate user agents
- Add random delays
- Use Playwright instead of Selenium

### No Products Found
- Check if selectors are correct
- Increase wait times for JavaScript
- Check if you're being blocked (save HTML to file and inspect)

## Next Steps

1. ✅ Install Selenium
2. ✅ Create selenium_scraper.py helper
3. ⬜ Manually inspect each website
4. ⬜ Update CSS selectors in each scraper
5. ⬜ Test each scraper individually
6. ⬜ Enable scrapers in `src/scrapers/__init__.py`
7. ⬜ Run full application: `python main.py --mode once`

Good luck! Start with Running Warehouse as it might be the easiest.
