"""
Example scraper template showing how to implement a scraper for a specific website.

This is a template/example. To create a real scraper:
1. Copy this file and rename it (e.g., nike_scraper.py)
2. Update the class name, website_name, and base_url
3. Implement get_search_urls() to return the URLs to scrape
4. Implement parse_listing_page() to extract shoes from listing pages
5. Optionally implement parse_product_page() for individual product pages
6. Add your scraper to the SCRAPERS list in __init__.py

Note: Web scraping requires understanding the HTML structure of the target site.
You may need to inspect the website using browser developer tools to identify
the correct CSS selectors or XPath expressions.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class ExampleScraper(BaseScraper):
    """
    Example scraper template.

    Replace this with actual implementation for a specific website.
    """

    @property
    def website_name(self) -> str:
        """Return the name of the website."""
        return "Example Website"

    @property
    def base_url(self) -> str:
        """Return the base URL."""
        return "https://example.com"

    def get_search_urls(self) -> List[str]:
        """
        Return list of URLs to scrape.

        Examples:
        - Running shoe category pages
        - Sale/clearance pages filtered for running shoes
        - Search results pages

        Returns:
            List of URLs to scrape
        """
        # Example URLs - replace with actual URLs
        return [
            # f"{self.base_url}/running-shoes/sale",
            # f"{self.base_url}/athletic/mens-running",
            # f"{self.base_url}/athletic/womens-running",
        ]

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse a product listing page and extract shoe information.

        Steps:
        1. Find all product containers (usually div or article elements)
        2. For each product, extract:
           - Product name
           - Brand (if available)
           - Current price
           - Original price (if on sale)
           - Product URL
           - Image URL
           - Any unique product identifier

        Args:
            soup: BeautifulSoup object of the page
            url: The URL that was scraped

        Returns:
            List of dictionaries containing shoe information
        """
        shoes = []

        # Example implementation (replace with actual selectors):
        #
        # product_containers = soup.select('.product-card')  # Update selector
        #
        # for container in product_containers:
        #     try:
        #         # Extract product information
        #         name_elem = container.select_one('.product-name')
        #         name = name_elem.get_text(strip=True) if name_elem else None
        #
        #         # Extract prices
        #         sale_price_elem = container.select_one('.sale-price')
        #         original_price_elem = container.select_one('.original-price')
        #
        #         current_price = self.extract_price(
        #             sale_price_elem.get_text() if sale_price_elem else None
        #         )
        #         original_price = self.extract_price(
        #             original_price_elem.get_text() if original_price_elem else None
        #         )
        #
        #         # If no sale price, use regular price
        #         if not current_price:
        #             price_elem = container.select_one('.price')
        #             current_price = self.extract_price(
        #                 price_elem.get_text() if price_elem else None
        #             )
        #
        #         # Extract product URL
        #         link_elem = container.select_one('a[href]')
        #         product_url = link_elem['href'] if link_elem else None
        #         if product_url and not product_url.startswith('http'):
        #             product_url = self.base_url + product_url
        #
        #         # Extract product ID from URL or data attribute
        #         product_id = link_elem.get('data-product-id') if link_elem else None
        #         if not product_id and product_url:
        #             # Try to extract from URL
        #             import re
        #             match = re.search(r'/product/(\d+)', product_url)
        #             product_id = match.group(1) if match else product_url.split('/')[-1]
        #
        #         # Check if on sale
        #         is_on_sale = bool(sale_price_elem) or bool(container.select_one('.sale-badge'))
        #
        #         # Calculate discount
        #         discount = 0
        #         if is_on_sale and original_price and current_price:
        #             discount = self.calculate_discount(original_price, current_price)
        #
        #         # Extract image
        #         img_elem = container.select_one('img')
        #         image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
        #
        #         # Create shoe data
        #         shoe_data = {
        #             'product_id': self.generate_product_id(self.website_name, product_id),
        #             'name': name,
        #             'brand': None,  # Extract if available
        #             'website': self.website_name,
        #             'url': product_url,
        #             'current_price': current_price,
        #             'original_price': original_price if is_on_sale else current_price,
        #             'discount_percentage': discount,
        #             'is_on_sale': is_on_sale,
        #             'image_url': image_url
        #         }
        #
        #         # Only add if we have minimum required info
        #         if name and product_url and current_price:
        #             shoes.append(shoe_data)
        #
        #     except Exception as e:
        #         self.logger.error(f"Error parsing product: {e}")
        #         continue

        return shoes

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """
        Parse an individual product page (optional).

        Use this if you need to visit individual product pages for more details.
        Most of the time, listing pages have enough information.

        Args:
            soup: BeautifulSoup object of the product page
            url: The product URL

        Returns:
            Dictionary containing shoe information, or None if parsing fails
        """
        # Implementation similar to parse_listing_page but for a single product
        return None
