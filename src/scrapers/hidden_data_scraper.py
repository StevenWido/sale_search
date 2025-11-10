"""
Scraper that extracts prices from hidden data in HTML.

Many sites embed product data in:
- JavaScript variables (window.productData = {...})
- JSON-LD structured data (<script type="application/ld+json">)
- Hidden data attributes (data-price="99.99")
- React/Next.js data (<script id="__NEXT_DATA__">)

This approach is fast because it doesn't require cart interaction.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import json
import re
from .base_scraper import BaseScraper


class HiddenDataScraper(BaseScraper):
    """Extract prices from hidden data in HTML."""

    @property
    def website_name(self) -> str:
        return "Hidden Data Site"

    @property
    def base_url(self) -> str:
        return "https://example.com"

    def get_search_urls(self) -> List[str]:
        return [f"{self.base_url}/running-shoes-sale"]

    def extract_json_ld_data(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract structured data from JSON-LD scripts.

        Many sites include product information in JSON-LD format for SEO.
        This often includes prices even if they're hidden in the UI.
        """
        products = []

        # Find all JSON-LD scripts
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                data = json.loads(script.string)

                # Handle single product
                if data.get('@type') == 'Product':
                    products.append(data)

                # Handle product list
                elif data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    for item in items:
                        if item.get('@type') == 'Product':
                            products.append(item)

                # Handle nested structures
                elif isinstance(data, dict) and 'product' in data:
                    if isinstance(data['product'], list):
                        products.extend(data['product'])
                    else:
                        products.append(data['product'])

            except json.JSONDecodeError as e:
                self.logger.debug(f"Error parsing JSON-LD: {e}")
                continue

        return products

    def extract_next_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract data from Next.js __NEXT_DATA__ script.

        Next.js sites embed page data in a script tag with id="__NEXT_DATA__"
        """
        script = soup.find('script', id='__NEXT_DATA__')
        if script and script.string:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError:
                pass
        return None

    def extract_from_data_attributes(self, container) -> Optional[Dict]:
        """
        Extract price from data attributes.

        Many sites hide prices in data attributes like:
        - data-price="99.99"
        - data-sale-price="79.99"
        - data-product-data='{"price": 99.99}'
        """
        try:
            # Method 1: Direct data attributes
            current_price = container.get('data-price') or container.get('data-sale-price')
            original_price = container.get('data-original-price') or container.get('data-regular-price')

            if current_price:
                current_price = self.extract_price(current_price)
                original_price = self.extract_price(original_price) if original_price else current_price

                return {
                    'current_price': current_price,
                    'original_price': original_price,
                    'is_on_sale': original_price != current_price
                }

            # Method 2: JSON in data attribute
            product_data_str = container.get('data-product') or container.get('data-product-data')
            if product_data_str:
                product_data = json.loads(product_data_str)
                return {
                    'current_price': product_data.get('price') or product_data.get('salePrice'),
                    'original_price': product_data.get('originalPrice') or product_data.get('regularPrice'),
                    'is_on_sale': product_data.get('onSale', False)
                }

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            self.logger.debug(f"Error extracting from data attributes: {e}")

        return None

    def extract_from_javascript(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract product data from JavaScript variables.

        Look for patterns like:
        - var productData = {...}
        - window.products = [...]
        - const PRODUCT_INFO = {...}
        """
        products = []

        scripts = soup.find_all('script', type='text/javascript')

        for script in scripts:
            if not script.string:
                continue

            # Pattern 1: var/let/const productData = {...}
            match = re.search(r'(?:var|let|const)\s+(?:productData|products|PRODUCTS)\s*=\s*(\{.*?\}|\[.*?\]);',
                            script.string, re.DOTALL)

            if match:
                try:
                    json_str = match.group(1)
                    data = json.loads(json_str)

                    if isinstance(data, list):
                        products.extend(data)
                    else:
                        products.append(data)

                except json.JSONDecodeError:
                    pass

            # Pattern 2: window.productData = {...}
            match = re.search(r'window\.(?:productData|products)\s*=\s*(\{.*?\}|\[.*?\]);',
                            script.string, re.DOTALL)

            if match:
                try:
                    json_str = match.group(1)
                    data = json.loads(json_str)

                    if isinstance(data, list):
                        products.extend(data)
                    else:
                        products.append(data)

                except json.JSONDecodeError:
                    pass

        return products

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Parse listing page looking for hidden data."""
        shoes = []

        # Method 1: Try JSON-LD first (most reliable)
        json_ld_products = self.extract_json_ld_data(soup)
        for product in json_ld_products:
            try:
                offers = product.get('offers', {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                current_price = self.extract_price(str(offers.get('price', '')))
                original_price = self.extract_price(str(offers.get('highPrice', ''))) or current_price

                shoe_data = {
                    'product_id': self.generate_product_id(
                        self.website_name,
                        product.get('sku') or product.get('productID') or product.get('url', '').split('/')[-1]
                    ),
                    'name': product.get('name'),
                    'brand': product.get('brand', {}).get('name') if isinstance(product.get('brand'), dict) else product.get('brand'),
                    'website': self.website_name,
                    'url': product.get('url') or product.get('offers', {}).get('url'),
                    'current_price': current_price,
                    'original_price': original_price,
                    'discount_percentage': self.calculate_discount(original_price, current_price) if original_price and current_price else 0,
                    'is_on_sale': original_price != current_price if original_price and current_price else False,
                    'image_url': product.get('image')
                }

                if shoe_data['name'] and shoe_data['url'] and shoe_data['current_price']:
                    shoes.append(shoe_data)

            except Exception as e:
                self.logger.error(f"Error parsing JSON-LD product: {e}")
                continue

        # Method 2: Try Next.js data
        if not shoes:
            next_data = self.extract_next_data(soup)
            if next_data:
                # Structure varies by site - you'll need to inspect
                # Common path: next_data['props']['pageProps']['products']
                try:
                    products = next_data.get('props', {}).get('pageProps', {}).get('products', [])
                    for product in products:
                        # Parse product data (structure varies)
                        # Similar to JSON-LD parsing above
                        pass
                except:
                    pass

        # Method 3: Try data attributes on product containers
        if not shoes:
            product_containers = soup.select('.product-card, .product-item')  # UPDATE SELECTOR

            for container in product_containers:
                try:
                    # Extract from data attributes
                    price_data = self.extract_from_data_attributes(container)

                    if not price_data:
                        continue

                    name_elem = container.select_one('.product-name')
                    name = name_elem.get_text(strip=True) if name_elem else None

                    link_elem = container.select_one('a[href]')
                    product_url = link_elem['href'] if link_elem else None
                    if product_url and not product_url.startswith('http'):
                        product_url = self.base_url + product_url

                    product_id = container.get('data-product-id') or container.get('data-sku')

                    if not (name and product_url and product_id):
                        continue

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
                        'brand': None,
                        'website': self.website_name,
                        'url': product_url,
                        'current_price': price_data['current_price'],
                        'original_price': price_data['original_price'],
                        'discount_percentage': discount,
                        'is_on_sale': price_data['is_on_sale'],
                        'image_url': None
                    }

                    shoes.append(shoe_data)

                except Exception as e:
                    self.logger.error(f"Error parsing product container: {e}")
                    continue

        return shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse individual product page (optional)."""
        # Same techniques apply - check JSON-LD, __NEXT_DATA__, data attributes
        return None
