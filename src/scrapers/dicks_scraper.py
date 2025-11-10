"""
Dick's Sporting Goods scraper for running shoes on sale.

URL: https://www.dickssportinggoods.com/f/shop-running-shoes?filterFacets=5004%253ASale

IMPORTANT: This site requires Selenium due to:
- Heavy JavaScript rendering (React)
- Cloudflare bot protection
- Dynamic content loading

This scraper is ready to use with Selenium installed.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import time
import logging
from .base_scraper import BaseScraper


class DicksScraper(BaseScraper):
    """Scraper for Dick's Sporting Goods running shoes."""

    def __init__(self):
        super().__init__()
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def init_driver(self):
        """Initialize Selenium WebDriver with undetected-chromedriver."""
        if self.driver is None:
            try:
                options = uc.ChromeOptions()
                # Comment out headless for debugging - uncomment for production
                # options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--window-size=1920,1080')

                self.driver = uc.Chrome(options=options)
                self.driver.set_page_load_timeout(30)
                self.logger.info("Selenium driver initialized")
            except Exception as e:
                self.logger.error(f"Error initializing driver: {e}")
                raise

    @property
    def website_name(self) -> str:
        return "Dick's Sporting Goods"

    @property
    def base_url(self) -> str:
        return "https://www.dickssportinggoods.com"

    def get_search_urls(self) -> List[str]:
        """Return URLs to scrape - running shoes on sale."""
        return [
            # Running shoes on sale
            f"{self.base_url}/f/shop-running-shoes?filterFacets=5004%3ASale",
            # You can add more filters if needed:
            # f"{self.base_url}/f/mens-running-shoes?filterFacets=5004%3ASale",
            # f"{self.base_url}/f/womens-running-shoes?filterFacets=5004%3ASale",
        ]

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch page using Selenium and wait for products to load.
        """
        try:
            self.init_driver()
            self.logger.info(f"Fetching with Selenium: {url}")

            self.driver.get(url)

            # Wait for products to load - adjust selector if needed
            # Common selectors: '.product-card', '[data-cmp="product"]', '.dsg-product'
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                        "div[class*='product'], article[class*='product'], div[data-cmp='product']"))
                )
                self.logger.info("Products loaded")
            except TimeoutException:
                self.logger.warning("Timeout waiting for products, continuing anyway")

            # Additional wait for prices to load
            time.sleep(3)

            # Scroll to load lazy-loaded images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # Save HTML for debugging (optional - comment out in production)
            # with open('dicks_page_debug.html', 'w', encoding='utf-8') as f:
            #     f.write(page_source)
            # self.logger.info("Saved page HTML to dicks_page_debug.html for inspection")

            return soup

        except Exception as e:
            self.logger.error(f"Error fetching {url} with Selenium: {e}")
            return None

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse Dick's Sporting Goods listing page.

        STEP-BY-STEP SETUP:
        1. Run with Selenium once to save the HTML (see fetch_page)
        2. Open dicks_page_debug.html in a browser
        3. Inspect the HTML and update selectors below
        4. Test and refine

        Common Dick's patterns to look for:
        - Product cards: div[class*="product"], article, div[data-product-id]
        - Name: h2, h3, .product-title, .dsg-product-title
        - Brand: .brand, .product-brand, span[class*="brand"]
        - Price: .price, .product-price, span[class*="price"]
        - Sale price: .sale-price, .discount-price, [data-price-type="sale"]
        - URL: a[href*="/p/"], a[data-product-url]
        - Product ID: data-product-id, data-sku, in URL
        """
        shoes = []

        # Try multiple selectors for product containers
        product_selectors = [
            'div[class*="product-card"]',
            'article[class*="product"]',
            'div[data-cmp="product"]',
            'div[data-product-id]',
            'div.dsg-product',
            'li[class*="product"]',
        ]

        product_containers = []
        for selector in product_selectors:
            containers = soup.select(selector)
            if containers:
                product_containers = containers
                self.logger.info(f"Found {len(containers)} products using selector: {selector}")
                break

        if not product_containers:
            self.logger.warning("No product containers found. Check selectors!")
            # Print first 2000 chars of HTML for debugging
            self.logger.debug(f"Page HTML preview: {str(soup)[:2000]}")

        for container in product_containers:
            try:
                # Extract product name - try multiple selectors
                name = None
                for selector in ['h2', 'h3', '.product-title', '.dsg-product-title',
                                '[class*="product-title"]', '[class*="ProductTitle"]']:
                    name_elem = container.select_one(selector)
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        break

                if not name:
                    continue

                # Extract brand
                brand = None
                for selector in ['.brand', '.product-brand', '[class*="brand"]',
                                '[class*="Brand"]', 'span[data-cmp="brand"]']:
                    brand_elem = container.select_one(selector)
                    if brand_elem:
                        brand = brand_elem.get_text(strip=True)
                        break

                # Extract URL
                product_url = None
                link_elem = container.select_one('a[href]')
                if link_elem:
                    product_url = link_elem.get('href')
                    if product_url and not product_url.startswith('http'):
                        product_url = self.base_url + product_url

                if not product_url:
                    continue

                # Extract product ID
                product_id = (
                    container.get('data-product-id') or
                    container.get('data-sku') or
                    container.get('id')
                )

                # Try to extract from URL if not found
                if not product_id and product_url:
                    import re
                    # Dick's URLs often like: /p/product-name-ABC123
                    match = re.search(r'/p/[\w-]+-(\w+)', product_url)
                    if match:
                        product_id = match.group(1)
                    else:
                        # Fallback: use last part of URL
                        product_id = product_url.split('/')[-1].split('?')[0]

                if not product_id:
                    continue

                # Check for hidden prices FIRST
                if self.is_price_hidden(container):
                    self.logger.info(f"Price hidden for: {name}")

                    # Extract image
                    image_url = None
                    img_elem = container.select_one('img')
                    if img_elem:
                        image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                        if image_url and image_url.startswith('//'):
                            image_url = 'https:' + image_url

                    shoe_data = {
                        'product_id': self.generate_product_id(self.website_name, product_id),
                        'name': name,
                        'brand': brand,
                        'website': self.website_name,
                        'url': product_url,
                        'current_price': None,
                        'original_price': None,
                        'discount_percentage': 0,
                        'is_on_sale': False,
                        'price_hidden': True,
                        'requires_manual_review': True,
                        'image_url': image_url
                    }

                    shoes.append(shoe_data)
                    continue

                # Extract prices
                current_price = None
                original_price = None

                # Try multiple selectors for sale price
                for selector in ['.sale-price', '.discount-price', '[data-price-type="sale"]',
                                '[class*="sale-price"]', '[class*="SalePrice"]',
                                'span[class*="price"][class*="sale"]']:
                    sale_price_elem = container.select_one(selector)
                    if sale_price_elem:
                        current_price = self.extract_price(sale_price_elem.get_text())
                        if current_price:
                            break

                # Try data attributes if text extraction failed
                if not current_price:
                    if container.get('data-sale-price'):
                        current_price = self.extract_price(container.get('data-sale-price'))
                    elif container.get('data-price'):
                        current_price = self.extract_price(container.get('data-price'))

                # Try original price selectors
                for selector in ['.regular-price', '.original-price', '[data-price-type="regular"]',
                                '[class*="regular-price"]', '[class*="OriginalPrice"]',
                                'span[class*="price"][class*="original"]']:
                    orig_price_elem = container.select_one(selector)
                    if orig_price_elem:
                        original_price = self.extract_price(orig_price_elem.get_text())
                        if original_price:
                            break

                # Try data attribute for original price
                if not original_price and container.get('data-regular-price'):
                    original_price = self.extract_price(container.get('data-regular-price'))

                # Fallback: look for any price elements
                if not current_price:
                    for selector in ['.price', '.product-price', '[class*="price"]',
                                    'span[class*="Price"]']:
                        price_elem = container.select_one(selector)
                        if price_elem:
                            current_price = self.extract_price(price_elem.get_text())
                            if current_price:
                                break

                # If we still don't have a price, skip or flag for review
                if not current_price:
                    self.logger.warning(f"No price found for {name}, may need manual review")
                    # Could flag for manual review here too
                    continue

                if not original_price:
                    original_price = current_price

                # Extract image
                image_url = None
                img_elem = container.select_one('img')
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                    if image_url and image_url.startswith('//'):
                        image_url = 'https:' + image_url

                # Determine if on sale
                is_on_sale = (
                    bool(container.select_one('.sale, .clearance, [class*="sale"]')) or
                    bool(container.select_one('[class*="Sale"], [class*="Clearance"]')) or
                    (original_price and current_price and original_price > current_price)
                )

                # Calculate discount
                discount = 0
                if is_on_sale and original_price and current_price:
                    discount = self.calculate_discount(original_price, current_price)

                # Create shoe data
                shoe_data = {
                    'product_id': self.generate_product_id(self.website_name, product_id),
                    'name': name,
                    'brand': brand,
                    'website': self.website_name,
                    'url': product_url,
                    'current_price': current_price,
                    'original_price': original_price,
                    'discount_percentage': discount,
                    'is_on_sale': is_on_sale,
                    'price_hidden': False,
                    'requires_manual_review': False,
                    'image_url': image_url
                }

                shoes.append(shoe_data)
                self.logger.debug(f"Parsed: {name} - ${current_price}")

            except Exception as e:
                self.logger.error(f"Error parsing Dick's product: {e}", exc_info=True)
                continue

        # Deduplicate by product_id (handles color variants and nested elements)
        seen_ids = set()
        unique_shoes = []

        for shoe in shoes:
            # Remove color variant from product_id for deduplication
            base_id = shoe['product_id'].split('?')[0]

            if base_id not in seen_ids:
                seen_ids.add(base_id)
                unique_shoes.append(shoe)
            else:
                self.logger.debug(f"Skipping duplicate: {shoe['name']} ({shoe['product_id']})")

        self.logger.info(f"Successfully parsed {len(shoes)} shoes from Dick's ({len(shoes) - len(unique_shoes)} duplicates removed)")
        return unique_shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Not used - we parse from listing page."""
        return None

    def close(self):
        """Clean up Selenium driver."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Selenium driver closed")
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")
        super().close()
