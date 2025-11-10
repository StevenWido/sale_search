"""
Example scraper showing how to detect and flag hidden prices.

This scraper demonstrates how to:
1. Detect "See Price in Cart" or similar text
2. Flag items for manual review
3. Still track these items in the database

Use this pattern in your real scrapers to handle hidden prices.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class HiddenPriceExampleScraper(BaseScraper):
    """
    Example scraper that detects and flags hidden prices.

    Copy this pattern into your real scrapers (Adidas, Running Warehouse, etc.)
    """

    @property
    def website_name(self) -> str:
        return "Example Site"

    @property
    def base_url(self) -> str:
        return "https://example.com"

    def get_search_urls(self) -> List[str]:
        return [f"{self.base_url}/running-shoes-sale"]

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse listing page and detect hidden prices.

        This is the key method - shows how to detect and flag hidden prices.
        """
        shoes = []

        # Replace with actual selector for your site
        product_containers = soup.select('.product-card, .product-item')

        for container in product_containers:
            try:
                # Extract basic info
                name_elem = container.select_one('.product-name, h3, .title')
                name = name_elem.get_text(strip=True) if name_elem else None

                link_elem = container.select_one('a[href]')
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = self.base_url + product_url

                product_id = (
                    container.get('data-product-id') or
                    container.get('data-sku') or
                    (product_url.split('/')[-1] if product_url else None)
                )

                if not (name and product_url and product_id):
                    continue

                # ===== KEY PART: Check if price is hidden =====
                price_is_hidden = self.is_price_hidden(container)

                if price_is_hidden:
                    # Price is hidden - flag for manual review
                    self.logger.info(f"Price hidden for: {name}")

                    shoe_data = {
                        'product_id': self.generate_product_id(self.website_name, product_id),
                        'name': name,
                        'brand': None,  # Extract if available
                        'website': self.website_name,
                        'url': product_url,
                        'current_price': None,  # No price available
                        'original_price': None,
                        'discount_percentage': 0,
                        'is_on_sale': False,  # We don't know if it's on sale
                        'price_hidden': True,  # Flag that price is hidden
                        'requires_manual_review': True,  # Flag for manual review
                        'image_url': container.select_one('img').get('src') if container.select_one('img') else None
                    }

                    shoes.append(shoe_data)

                else:
                    # Normal price extraction
                    sale_price_elem = container.select_one('.sale-price, .price-sale')
                    regular_price_elem = container.select_one('.regular-price, .price-regular')

                    current_price = None
                    original_price = None

                    if sale_price_elem:
                        current_price = self.extract_price(sale_price_elem.get_text())
                    if regular_price_elem:
                        original_price = self.extract_price(regular_price_elem.get_text())

                    # Fallback to main price
                    if not current_price:
                        price_elem = container.select_one('.price')
                        current_price = self.extract_price(price_elem.get_text()) if price_elem else None

                    if not original_price:
                        original_price = current_price

                    # Only add if we have a price
                    if current_price:
                        is_on_sale = bool(sale_price_elem) or bool(container.select_one('.sale-badge'))
                        discount = 0

                        if is_on_sale and original_price and current_price:
                            discount = self.calculate_discount(original_price, current_price)

                        shoe_data = {
                            'product_id': self.generate_product_id(self.website_name, product_id),
                            'name': name,
                            'brand': None,
                            'website': self.website_name,
                            'url': product_url,
                            'current_price': current_price,
                            'original_price': original_price,
                            'discount_percentage': discount,
                            'is_on_sale': is_on_sale,
                            'price_hidden': False,
                            'requires_manual_review': False,
                            'image_url': container.select_one('img').get('src') if container.select_one('img') else None
                        }

                        shoes.append(shoe_data)

            except Exception as e:
                self.logger.error(f"Error parsing product: {e}")
                continue

        return shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse individual product page (optional)."""
        return None
