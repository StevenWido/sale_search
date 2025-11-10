"""Base scraper class that all specific scrapers inherit from."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
import logging
import re
from src.config import Config


class BaseScraper(ABC):
    """Abstract base class for all shoe website scrapers."""

    def __init__(self):
        """Initialize the scraper."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update(Config.get_headers())

    @property
    @abstractmethod
    def website_name(self) -> str:
        """Return the name of the website being scraped."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL of the website."""
        pass

    @abstractmethod
    def get_search_urls(self) -> List[str]:
        """Return list of URLs to scrape for running shoes."""
        pass

    @abstractmethod
    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse a product page and extract shoe information."""
        pass

    @abstractmethod
    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Parse a listing/search page and extract shoe information."""
        pass

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            self.logger.info(f"Fetching: {url}")
            response = self.session.get(
                url,
                timeout=Config.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()

            # Add delay to be polite
            time.sleep(Config.REQUEST_DELAY)

            return BeautifulSoup(response.content, 'lxml')

        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def scrape(self) -> List[Dict]:
        """Main scraping method that coordinates the scraping process."""
        all_shoes = []

        search_urls = self.get_search_urls()
        self.logger.info(f"Scraping {len(search_urls)} URLs from {self.website_name}")

        for url in search_urls:
            soup = self.fetch_page(url)
            if soup:
                try:
                    shoes = self.parse_listing_page(soup, url)
                    all_shoes.extend(shoes)
                    self.logger.info(f"Found {len(shoes)} shoes from {url}")
                except Exception as e:
                    self.logger.error(f"Error parsing {url}: {e}")

        # Filter shoes based on keywords
        filtered_shoes = self.filter_shoes(all_shoes)
        self.logger.info(f"Total shoes after filtering: {len(filtered_shoes)}")

        return filtered_shoes

    def filter_shoes(self, shoes: List[Dict]) -> List[Dict]:
        """Filter shoes based on keywords and minimum discount."""
        keywords = Config.get_keywords()
        filtered = []

        for shoe in shoes:
            # Check if name contains any of the keywords
            name_lower = shoe.get('name', '').lower()
            if any(keyword in name_lower for keyword in keywords):
                # Check minimum discount if on sale
                if shoe.get('is_on_sale'):
                    discount = shoe.get('discount_percentage', 0)
                    if discount >= Config.MIN_DISCOUNT_PERCENTAGE:
                        filtered.append(shoe)
                else:
                    # Include non-sale items too for price tracking
                    filtered.append(shoe)

        return filtered

    @staticmethod
    def extract_price(price_str: str) -> Optional[float]:
        """Extract numeric price from a string."""
        if not price_str:
            return None

        # Remove currency symbols and extract numbers
        price_str = re.sub(r'[^\d.,]', '', price_str)
        price_str = price_str.replace(',', '')

        try:
            return float(price_str)
        except ValueError:
            return None

    @staticmethod
    def calculate_discount(original_price: float, sale_price: float) -> float:
        """Calculate discount percentage."""
        if not original_price or not sale_price or original_price <= 0:
            return 0.0

        discount = ((original_price - sale_price) / original_price) * 100
        return round(discount, 2)

    @staticmethod
    def is_price_hidden(container) -> bool:
        """
        Detect if price is hidden (e.g., "See Price in Cart").

        Args:
            container: BeautifulSoup element (product container)

        Returns:
            True if price appears to be hidden
        """
        # Common patterns for hidden prices
        hidden_price_patterns = [
            'see price in cart',
            'price in cart',
            'add to cart to see price',
            'add to bag to see price',
            'login to see price',
            'sign in to see price',
            'view price in cart',
            'price available in cart',
            'cart price',
            'special price in cart',
            'member price',
            'members only',
        ]

        # Get all text from the container
        text = container.get_text(separator=' ').lower()

        # Check for any hidden price patterns
        return any(pattern in text for pattern in hidden_price_patterns)

    @staticmethod
    def generate_product_id(website: str, product_identifier: str) -> str:
        """Generate a unique product ID."""
        return f"{website}_{product_identifier}"

    def close(self):
        """Close the session."""
        self.session.close()
