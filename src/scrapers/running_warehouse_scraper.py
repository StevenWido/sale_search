"""
Running Warehouse scraper for running shoes.

NOTES:
- Running Warehouse may have better compatibility with basic scraping
- They have separate pages for men's and women's running shoes
- Check robots.txt: https://www.runningwarehouse.com/robots.txt

URL PATTERNS:
- Men's Sale: https://www.runningwarehouse.com/catpage-MRSALE.html
- Women's Sale: https://www.runningwarehouse.com/catpage-WRSALE.html
- Men's Running: https://www.runningwarehouse.com/catpage-MRUNNING.html
- Women's Running: https://www.runningwarehouse.com/catpage-WRUNNING.html

To implement this scraper:
1. Visit the URLs in a browser
2. Inspect the HTML to find product containers
3. Update the CSS selectors below
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class RunningWarehouseScraper(BaseScraper):
    """Scraper for Running Warehouse."""

    @property
    def website_name(self) -> str:
        return "Running Warehouse"

    @property
    def base_url(self) -> str:
        return "https://www.runningwarehouse.com"

    def get_search_urls(self) -> List[str]:
        """Return URLs to scrape."""
        return [
            f"{self.base_url}/catpage-MRSALE.html",  # Men's running shoes on sale
            f"{self.base_url}/catpage-WRSALE.html",  # Women's running shoes on sale
            # You can add more:
            # f"{self.base_url}/catpage-MRUNNING.html",  # All men's running
            # f"{self.base_url}/catpage-WRUNNING.html",  # All women's running
        ]

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse Running Warehouse listing page.

        TO IMPLEMENT:
        1. Visit https://www.runningwarehouse.com/catpage-MRSALE.html
        2. Inspect a product element
        3. Update selectors below

        Running Warehouse typically uses:
        - Product containers might be: div.product, div.productbox, or similar
        - They often show brand, model name, price clearly
        - Look for elements with classes like 'brand', 'model', 'price', 'sale-price'
        """
        shoes = []

        # PLACEHOLDER SELECTORS - Update after inspecting the actual page
        # Common patterns for Running Warehouse:
        product_containers = soup.select('div.productbox')  # UPDATE THIS

        for container in product_containers:
            try:
                # Extract brand - UPDATE SELECTOR
                brand_elem = container.select_one('.brand, .brandname')
                brand = brand_elem.get_text(strip=True) if brand_elem else None

                # Extract model name - UPDATE SELECTOR
                model_elem = container.select_one('.model, .modelname, .productname')
                model = model_elem.get_text(strip=True) if model_elem else None

                # Combine for full name
                name = f"{brand} {model}".strip() if brand and model else (model or brand)

                # Extract URL - UPDATE SELECTOR
                link_elem = container.select_one('a[href]')
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = self.base_url + product_url

                # Extract prices - UPDATE SELECTORS
                # Running Warehouse often shows regular and sale prices
                sale_price_elem = container.select_one('.saleprice, .price-sale')
                regular_price_elem = container.select_one('.regularprice, .price-regular')

                current_price = None
                original_price = None

                if sale_price_elem:
                    current_price = self.extract_price(sale_price_elem.get_text())
                if regular_price_elem:
                    original_price = self.extract_price(regular_price_elem.get_text())

                # If no sale price, use the main price
                if not current_price:
                    price_elem = container.select_one('.price')
                    current_price = self.extract_price(price_elem.get_text()) if price_elem else None

                if not original_price:
                    original_price = current_price

                # Extract product ID
                # Running Warehouse often has product codes
                product_id = None
                if link_elem:
                    # Try data attributes
                    product_id = (link_elem.get('data-product-id') or
                                link_elem.get('data-sku') or
                                link_elem.get('id'))

                # Try to extract from URL if not found
                if not product_id and product_url:
                    # URLs often like: /productname-SKU123.html
                    import re
                    match = re.search(r'-([A-Z0-9]+)\.html', product_url)
                    if match:
                        product_id = match.group(1)
                    else:
                        product_id = product_url.split('/')[-1].replace('.html', '')

                # Extract image - UPDATE SELECTOR
                img_elem = container.select_one('img')
                image_url = None
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src')
                    if image_url and not image_url.startswith('http'):
                        image_url = self.base_url + image_url

                # Determine if on sale
                is_on_sale = bool(sale_price_elem)

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
                self.logger.error(f"Error parsing Running Warehouse product: {e}")
                continue

        return shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse individual product page (optional)."""
        return None
