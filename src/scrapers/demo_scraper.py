"""
Demo scraper that generates sample data for testing the application.

This scraper doesn't actually scrape any website - it generates random
running shoe data to demonstrate how the application works.

Use this to test the application before implementing real scrapers.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import random


class DemoScraper(BaseScraper):
    """Demo scraper that generates sample running shoe data."""

    @property
    def website_name(self) -> str:
        return "Demo Store"

    @property
    def base_url(self) -> str:
        return "https://demo.example.com"

    def get_search_urls(self) -> List[str]:
        """Return dummy URLs."""
        return ["demo://sample"]

    def scrape(self) -> List[Dict]:
        """Generate sample shoe data instead of actually scraping."""
        self.logger.info(f"Generating demo data from {self.website_name}")

        shoes = self._generate_sample_shoes()

        # Apply normal filtering
        filtered_shoes = self.filter_shoes(shoes)
        self.logger.info(f"Generated {len(filtered_shoes)} demo shoes")

        return filtered_shoes

    def _generate_sample_shoes(self) -> List[Dict]:
        """Generate sample running shoe data."""
        brands = ["Nike", "Adidas", "Brooks", "Asics", "New Balance", "Hoka", "Saucony"]
        models = [
            "Air Zoom Pegasus", "Ultraboost", "Ghost", "Gel-Kayano", "Fresh Foam",
            "Clifton", "Kinvara", "Vaporfly", "Boston", "Adrenaline GTS"
        ]
        versions = ["15", "16", "17", "18", "19", "20"]

        shoes = []

        # Generate 15-25 random shoes
        num_shoes = random.randint(15, 25)

        for i in range(num_shoes):
            brand = random.choice(brands)
            model = random.choice(models)
            version = random.choice(versions)

            name = f"{brand} {model} {version}"

            # Random prices
            original_price = round(random.uniform(100, 200), 2)

            # 40% chance of being on sale
            is_on_sale = random.random() < 0.4

            if is_on_sale:
                # Discount between 10% and 50%
                discount_pct = round(random.uniform(10, 50), 2)
                current_price = round(original_price * (1 - discount_pct / 100), 2)
            else:
                current_price = original_price
                discount_pct = 0

            product_id = self.generate_product_id(self.website_name, f"DEMO{i:04d}")

            shoe_data = {
                'product_id': product_id,
                'name': name,
                'brand': brand,
                'website': self.website_name,
                'url': f"{self.base_url}/products/demo-{i}",
                'current_price': current_price,
                'original_price': original_price,
                'discount_percentage': discount_pct,
                'is_on_sale': is_on_sale,
                'image_url': f"{self.base_url}/images/demo-shoe-{i}.jpg"
            }

            shoes.append(shoe_data)

        return shoes

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Not used in demo scraper."""
        return []

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Not used in demo scraper."""
        return None
