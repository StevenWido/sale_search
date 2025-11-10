# Dick's Sporting Goods Scraper Setup Guide

This guide walks you through setting up and testing the Dick's Sporting Goods scraper for running shoes on sale.

**Target URL**: https://www.dickssportinggoods.com/f/shop-running-shoes?filterFacets=5004%3ASale

## Quick Start

```bash
# 1. Install Selenium
pip install selenium undetected-chromedriver

# 2. Test the scraper
python test_dicks_scraper.py

# 3. Enable in production (after testing)
# Edit src/scrapers/__init__.py and uncomment DicksScraper
```

## Step-by-Step Setup

### Step 1: Install Selenium

Dick's requires Selenium because:
- Uses heavy JavaScript (React) to render products
- Has Cloudflare bot protection
- Prices load dynamically after page load

```bash
pip install selenium undetected-chromedriver
```

**What this installs:**
- `selenium`: Browser automation framework
- `undetected-chromedriver`: Special Chrome driver that bypasses bot detection

### Step 2: Test the Scraper

Run the test script:

```bash
python test_dicks_scraper.py
```

**What happens:**
1. Chrome browser will open (you'll see it)
2. Navigates to Dick's running shoes sale page
3. Waits for products to load
4. Scrolls to load lazy-loaded images
5. Extracts product data
6. Shows results in console
7. Asks if you want to save to database

**Expected output:**
```
================================================================================
TESTING DICK'S SPORTING GOODS SCRAPER
================================================================================
Website: Dick's Sporting Goods
URLs to scrape: ['https://www.dickssportinggoods.com/f/shop-running-shoes?filterFacets=5004%3ASale']

Starting scrape...
INFO - Selenium driver initialized
INFO - Fetching with Selenium: https://...
INFO - Products loaded
INFO - Found 24 products using selector: div[class*="product-card"]
INFO - Price hidden for: Nike Air Zoom Structure 25
INFO - Successfully parsed 24 shoes from Dick's

================================================================================
SCRAPING COMPLETE - Found 24 shoes
================================================================================

Shoes with visible prices: 18
Shoes with hidden prices (manual review): 6

FIRST 5 SHOES WITH VISIBLE PRICES:
--------------------------------------------------------------------------------
1. Brooks Ghost 15
   Brand: Brooks
   Price: $89.99
   Original: $140.00 (35.7% off)
   URL: https://www.dickssportinggoods.com/p/brooks-ghost-15

...
```

### Step 3: Troubleshooting

#### Problem: "No products found"

**Cause**: Selectors might need updating

**Solution**: Enable HTML saving to inspect:

1. Edit `src/scrapers/dicks_scraper.py`
2. Uncomment lines 105-107:
   ```python
   with open('dicks_page_debug.html', 'w', encoding='utf-8') as f:
       f.write(page_source)
   self.logger.info("Saved page HTML to dicks_page_debug.html for inspection")
   ```
3. Run test again: `python test_dicks_scraper.py`
4. Open `dicks_page_debug.html` in browser
5. Right-click a product → Inspect
6. Update selectors in `parse_listing_page()`

#### Problem: "ChromeDriver not found"

**Solution**:
```bash
pip install --upgrade undetected-chromedriver
```

Or install Chrome if not already installed.

#### Problem: "Cloudflare blocked"

**Symptoms**: Page shows Cloudflare challenge

**Solutions**:
1. **Run non-headless first** (default in test mode)
2. **Add delays**: Increase `time.sleep()` in `fetch_page()`
3. **Use residential proxy** (advanced)

#### Problem: Browser opens but page doesn't load

Check:
- Internet connection
- Firewall settings
- VPN interference

### Step 4: Fine-Tune Selectors (If Needed)

If products aren't being extracted correctly:

1. **Save HTML** (see above)
2. **Inspect structure** in browser
3. **Update selectors** in `dicks_scraper.py`:

```python
# Line 137-144: Product container selectors
product_selectors = [
    'your-new-selector',  # Add your selector
    'div[class*="product-card"]',
    # ...
]

# Line 163-164: Product name selectors
for selector in ['h2', 'your-new-selector']:
    name_elem = container.select_one(selector)
    # ...
```

Common patterns for Dick's:
- Products: `div[class*="product"]`, `article`, `li[class*="product"]`
- Name: `h2`, `h3`, `.product-title`, `[class*="ProductTitle"]`
- Brand: `.brand`, `[class*="brand"]`
- Price: `.price`, `[class*="price"]`, `[data-price]`

### Step 5: Enable in Production

Once testing succeeds, enable the scraper:

1. Edit `src/scrapers/__init__.py`
2. Uncomment these lines:
   ```python
   from .dicks_scraper import DicksScraper

   SCRAPERS = [
       DemoScraper,
       DicksScraper,  # Uncomment this
   ]
   ```
3. Run full application:
   ```bash
   python main.py --mode once
   ```

### Step 6: Production Tips

#### Run Headless

For production, enable headless mode:

Edit `src/scrapers/dicks_scraper.py` line 40:
```python
options.add_argument('--headless')  # Uncomment this line
```

#### Handle Rate Limiting

Don't run too frequently:
```bash
# Good: Check every 2-4 hours
python main.py --mode schedule --interval 120

# Bad: Every 5 minutes (might get blocked)
python main.py --mode schedule --interval 5
```

#### Monitor Logs

Check logs regularly:
```bash
tail -f logs/shoe_tracker.log
```

Watch for:
- "Cloudflare" or "blocked" messages
- "No products found" warnings
- Timeout errors

## Advanced Configuration

### Custom Wait Times

If products load slowly, increase waits in `fetch_page()`:

```python
# Line 84-90: Wait for products
WebDriverWait(self.driver, 15).until(...)  # Increase from 15 to 30

# Line 93: Wait for prices
time.sleep(3)  # Increase from 3 to 5
```

### Handle Pagination

Dick's may paginate results. To scrape multiple pages:

```python
def get_search_urls(self) -> List[str]:
    urls = []
    # Add pagination
    for page in range(1, 5):  # First 4 pages
        urls.append(
            f"{self.base_url}/f/shop-running-shoes"
            f"?filterFacets=5004%3ASale&pageNumber={page}"
        )
    return urls
```

### Filter by Gender/Brand

Add more specific URLs:

```python
def get_search_urls(self) -> List[str]:
    return [
        # All running shoes on sale
        f"{self.base_url}/f/shop-running-shoes?filterFacets=5004%3ASale",

        # Men's only
        f"{self.base_url}/f/mens-running-shoes?filterFacets=5004%3ASale",

        # Women's only
        f"{self.base_url}/f/womens-running-shoes?filterFacets=5004%3ASale",

        # Specific brands (Nike example)
        f"{self.base_url}/f/shop-running-shoes?filterFacets=5004%3ASale%2C5005%3ANike",
    ]
```

### Use Proxy (If Blocked)

For stubborn blocking, use a proxy:

```python
def init_driver(self):
    options = uc.ChromeOptions()
    options.add_argument('--proxy-server=http://your-proxy:port')
    # ...
```

## Hidden Price Detection

The scraper automatically detects "See Price in Cart" text. Items with hidden prices:

- Saved to database with `requires_manual_review=True`
- Show in notifications
- Viewable with: `python main.py --mode review`

No need to configure - it just works!

## Performance

**Expected scraping time:**
- Initial load: 5-10 seconds
- Per product page: ~1 second
- Full page (20-50 products): 15-30 seconds

**Resource usage:**
- RAM: ~500MB (Chrome)
- CPU: Moderate during scraping
- Network: ~5-10MB per scrape

## Summary Checklist

- [ ] Install Selenium: `pip install selenium undetected-chromedriver`
- [ ] Test scraper: `python test_dicks_scraper.py`
- [ ] Verify products extracted correctly
- [ ] Fine-tune selectors if needed
- [ ] Enable in `src/scrapers/__init__.py`
- [ ] Run in production: `python main.py --mode once`
- [ ] Schedule regular checks: `python main.py --mode schedule --interval 120`
- [ ] Monitor logs for issues

## Getting Help

**Check logs first:**
```bash
cat dicks_scraper_test.log
cat logs/shoe_tracker.log
```

**Common issues:**
1. No products → Update selectors
2. Cloudflare block → Increase delays, use proxy
3. Chrome errors → Update `pip install --upgrade undetected-chromedriver`

**Still stuck?**
- Save HTML file and inspect structure
- Check Dick's website in regular browser
- Try Running Warehouse first (simpler site)

## Quick Reference

```bash
# Test scraper
python test_dicks_scraper.py

# Run once
python main.py --mode once

# View results
python main.py --mode show          # Sales with prices
python main.py --mode review        # Hidden prices needing manual check

# Run on schedule (every 2 hours)
python main.py --mode schedule --interval 120

# Check logs
tail -f logs/shoe_tracker.log
```

Good luck! The scraper is robust and ready to use once you verify it works in your environment.
