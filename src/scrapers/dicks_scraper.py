"""
Dick's Sporting Goods scraper for running shoes.

NOTES:
- Dick's uses heavy JavaScript (React/similar) for product rendering
- The site has bot protection (likely Cloudflare)
- You'll need Selenium/Playwright for this to work properly

ALTERNATIVE APPROACHES:
1. Use Selenium with undetected-chromedriver
2. Use Playwright with stealth mode
3. Consider using their mobile site (sometimes less protected)

URL PATTERNS:
- Running shoes on sale: /f/running-shoes-on-sale
- Men's running: /f/mens-running-shoes
- Women's running: /f/womens-running-shoes
- You can add filters: ?filters=price:0-100

To implement:
1. Install selenium: pip install selenium undetected-chromedriver
2. Override fetch_page() to use Selenium
3. Update selectors after inspecting the rendered page
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class DicksScraper(BaseScraper):
    """Scraper for Dick's Sporting Goods."""

    @property
    def website_name(self) -> str:
        return "Dick's Sporting Goods"

    @property
    def base_url(self) -> str:
        return "https://www.dickssportinggoods.com"

    def get_search_urls(self) -> List[str]:
        """Return URLs to scrape."""
        return [
            f"{self.base_url}/f/running-shoes-on-sale",
            # Add more categories if needed:
            # f"{self.base_url}/f/mens-running-shoes?filters=price:0-100",
            # f"{self.base_url}/f/womens-running-shoes?filters=price:0-100",
        ]

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse Dick's Sporting Goods listing page.

        TO IMPLEMENT:
        1. Use Selenium to load the page (products are JavaScript-rendered)
        2. Wait for products to load
        3. Get the page source and parse with BeautifulSoup
        4. Update selectors below

        Dick's typically uses:
        - Product cards in a grid layout
        - Classes like 'product-card', 'product-tile', or similar
        - Prices might be in: .price, .product-price, or data attributes
        - Sale badges/indicators for discounted items
        """
        shoes = []

        # PLACEHOLDER SELECTORS - Update after inspecting with Selenium
        # Note: These won't work with basic requests - you need Selenium

        product_containers = soup.select('div[data-cmp="product"]')  # UPDATE THIS

        for container in product_containers:
            try:
                # Extract name - UPDATE SELECTOR
                name_elem = container.select_one('.product-name, h2, .dsg-product-title')
                name = name_elem.get_text(strip=True) if name_elem else None

                # Extract brand - UPDATE SELECTOR
                brand_elem = container.select_one('.brand, .product-brand')
                brand = brand_elem.get_text(strip=True) if brand_elem else None

                # Extract URL - UPDATE SELECTOR
                link_elem = container.select_one('a[href]')
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = self.base_url + product_url

                # Extract prices - UPDATE SELECTORS
                # Dick's often uses data attributes for prices
                sale_price_elem = container.select_one('.sale-price, [data-price-type="sale"]')
                regular_price_elem = container.select_one('.regular-price, [data-price-type="regular"]')

                current_price = None
                original_price = None

                # Try to extract from elements
                if sale_price_elem:
                    current_price = self.extract_price(sale_price_elem.get_text())
                if regular_price_elem:
                    original_price = self.extract_price(regular_price_elem.get_text())

                # Try data attributes if elements don't have text
                if not current_price and container.get('data-sale-price'):
                    current_price = self.extract_price(container.get('data-sale-price'))
                if not original_price and container.get('data-regular-price'):
                    original_price = self.extract_price(container.get('data-regular-price'))

                # Fallback to main price
                if not current_price:
                    price_elem = container.select_one('.price, .product-price')
                    current_price = self.extract_price(price_elem.get_text()) if price_elem else None

                if not original_price:
                    original_price = current_price

                # Extract product ID
                product_id = None
                if container.get('data-product-id'):
                    product_id = container.get('data-product-id')
                elif container.get('data-sku'):
                    product_id = container.get('data-sku')
                elif product_url:
                    # Extract from URL (often has product ID)
                    import re
                    match = re.search(r'/p/(\w+)', product_url)
                    if match:
                        product_id = match.group(1)
                    else:
                        product_id = product_url.split('/')[-1].split('?')[0]

                # Extract image - UPDATE SELECTOR
                img_elem = container.select_one('img')
                image_url = None
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                    if image_url and image_url.startswith('//'):
                        image_url = 'https:' + image_url

                # Check if on sale
                is_on_sale = bool(sale_price_elem) or bool(container.select_one('.sale, .clearance'))

                # Calculate discount
                discount = 0
                if is_on_sale and original_price and current_price:
                    discount = self.calculate_discount(original_price, current_price)

                # Create shoe data
                if name and product_url and current_price and product_id:
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
                        'image_url': image_url
                    }
                    shoes.append(shoe_data)

            except Exception as e:
                self.logger.error(f"Error parsing Dick's product: {e}")
                continue

        return shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse individual product page (optional)."""
        return None
