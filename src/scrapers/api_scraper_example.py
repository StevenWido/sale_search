"""
Example scraper for sites that require API calls to get prices.

This approach intercepts the API calls that happen when adding to cart
or loading product details, which often contain price information.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import requests
import json
from .base_scraper import BaseScraper


class APIScraper(BaseScraper):
    """
    Scraper that uses API endpoints to get product data.

    Use this when:
    - Prices are hidden until adding to cart
    - Product data loads via AJAX/fetch calls
    - The site has internal APIs you can access
    """

    @property
    def website_name(self) -> str:
        return "Example API Site"

    @property
    def base_url(self) -> str:
        return "https://example.com"

    def get_search_urls(self) -> List[str]:
        """Return API endpoints or listing pages."""
        return [
            f"{self.base_url}/api/products?category=running-shoes&on_sale=true",
        ]

    def get_product_price_from_api(self, product_id: str) -> Optional[Dict]:
        """
        Get product price by calling the add-to-cart or product detail API.

        Args:
            product_id: The product ID or SKU

        Returns:
            Dictionary with price information
        """
        try:
            # Method 1: Product details API
            response = self.session.get(
                f"{self.base_url}/api/products/{product_id}",
                timeout=self.config.REQUEST_TIMEOUT
            )

            if response.ok:
                data = response.json()
                return {
                    'current_price': data.get('price', {}).get('current'),
                    'original_price': data.get('price', {}).get('original'),
                    'is_on_sale': data.get('on_sale', False),
                }

            # Method 2: Simulate add-to-cart request (if product API doesn't work)
            # This makes a POST request as if adding to cart, but we just read the response
            cart_response = self.session.post(
                f"{self.base_url}/api/cart/add",
                json={
                    'product_id': product_id,
                    'quantity': 1,
                    'dry_run': True  # Some sites support this to not actually add
                },
                timeout=self.config.REQUEST_TIMEOUT
            )

            if cart_response.ok:
                cart_data = cart_response.json()
                # API responses vary, adjust based on actual structure
                return {
                    'current_price': cart_data.get('item', {}).get('price'),
                    'original_price': cart_data.get('item', {}).get('original_price'),
                    'is_on_sale': cart_data.get('item', {}).get('on_sale'),
                }

        except Exception as e:
            self.logger.error(f"Error getting price for {product_id}: {e}")

        return None

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse listing page or API response.

        If the URL is an API endpoint, soup will be the JSON response.
        Otherwise, get product IDs from HTML and fetch prices via API.
        """
        shoes = []

        # If this is an API endpoint returning JSON
        if url.endswith('.json') or '/api/' in url:
            try:
                # The "soup" in this case is actually the response text
                # You might need to override scrape() to handle this better
                products = json.loads(str(soup))

                for product in products.get('products', []):
                    shoe_data = {
                        'product_id': self.generate_product_id(
                            self.website_name,
                            product['id']
                        ),
                        'name': product['name'],
                        'brand': product.get('brand'),
                        'website': self.website_name,
                        'url': f"{self.base_url}/products/{product['id']}",
                        'current_price': product.get('price'),
                        'original_price': product.get('original_price', product.get('price')),
                        'discount_percentage': product.get('discount_percentage', 0),
                        'is_on_sale': product.get('on_sale', False),
                        'image_url': product.get('image_url')
                    }
                    shoes.append(shoe_data)

                return shoes

            except Exception as e:
                self.logger.error(f"Error parsing API response: {e}")
                return []

        # Otherwise, parse HTML to get product IDs, then fetch prices
        product_containers = soup.select('.product-card')

        for container in product_containers:
            try:
                # Extract basic info from HTML
                name_elem = container.select_one('.product-name')
                name = name_elem.get_text(strip=True) if name_elem else None

                link_elem = container.select_one('a[href]')
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = self.base_url + product_url

                # Get product ID
                product_id = (
                    container.get('data-product-id') or
                    link_elem.get('data-product-id') if link_elem else None
                )

                if not product_id:
                    continue

                # Fetch price via API
                price_data = self.get_product_price_from_api(product_id)

                if not price_data:
                    continue

                # Calculate discount
                discount = 0
                if (price_data['is_on_sale'] and
                    price_data['original_price'] and
                    price_data['current_price']):
                    discount = self.calculate_discount(
                        price_data['original_price'],
                        price_data['current_price']
                    )

                shoe_data = {
                    'product_id': self.generate_product_id(self.website_name, product_id),
                    'name': name,
                    'brand': None,  # Extract if available
                    'website': self.website_name,
                    'url': product_url,
                    'current_price': price_data['current_price'],
                    'original_price': price_data['original_price'],
                    'discount_percentage': discount,
                    'is_on_sale': price_data['is_on_sale'],
                    'image_url': None  # Extract if available
                }

                shoes.append(shoe_data)

                # Be extra polite when making individual API calls
                import time
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error parsing product: {e}")
                continue

        return shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse individual product page (optional)."""
        return None
