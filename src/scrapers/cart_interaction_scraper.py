"""
Example scraper that interacts with shopping carts to reveal prices.

This scraper uses Selenium to:
1. Click "Add to Cart" buttons
2. Extract prices from cart modals/pages
3. Clear the cart and continue

Use this when prices are only shown after adding items to cart.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import undetected_chromedriver as uc
from .base_scraper import BaseScraper


class CartInteractionScraper(BaseScraper):
    """
    Scraper that adds items to cart to reveal prices.

    WARNING: This is slower and more resource-intensive as it interacts
    with the cart for each product.
    """

    def __init__(self):
        super().__init__()
        self.driver = None

    def init_driver(self):
        """Initialize Selenium WebDriver."""
        if self.driver is None:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)

    @property
    def website_name(self) -> str:
        return "Cart Required Site"

    @property
    def base_url(self) -> str:
        return "https://example.com"

    def get_search_urls(self) -> List[str]:
        return [f"{self.base_url}/running-shoes-sale"]

    def get_price_from_cart(self, product_url: str, add_to_cart_selector: str) -> Optional[Dict]:
        """
        Add product to cart and extract price.

        Args:
            product_url: URL of the product page
            add_to_cart_selector: CSS selector for the "Add to Cart" button

        Returns:
            Dictionary with price information
        """
        try:
            self.init_driver()
            self.driver.get(product_url)

            # Wait for page to load
            time.sleep(2)

            # Find and click "Add to Cart" button
            add_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, add_to_cart_selector))
            )
            add_button.click()

            # Wait for cart modal/page to appear
            time.sleep(2)

            # Method 1: Price appears in a cart modal
            try:
                price_elem = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.cart-item-price'))
                )
                price_text = price_elem.text
                current_price = self.extract_price(price_text)

                # Check for original price
                original_price_elem = self.driver.find_element(By.CSS_SELECTOR, '.cart-item-original-price')
                original_price = self.extract_price(original_price_elem.text) if original_price_elem else current_price

                # Close modal (if applicable)
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, '.modal-close, .close-cart')
                    close_button.click()
                    time.sleep(1)
                except:
                    pass

                return {
                    'current_price': current_price,
                    'original_price': original_price,
                    'is_on_sale': original_price != current_price if original_price else False
                }

            except TimeoutException:
                # Method 2: Navigate to cart page
                self.driver.get(f"{self.base_url}/cart")
                time.sleep(2)

                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')

                # Extract price from cart page
                price_elem = soup.select_one('.cart-item-price, .item-price')
                if price_elem:
                    current_price = self.extract_price(price_elem.get_text())

                    # Check for sale price
                    original_price_elem = soup.select_one('.cart-item-original-price, .original-price')
                    original_price = self.extract_price(original_price_elem.get_text()) if original_price_elem else current_price

                    # Clear the cart before continuing
                    self.clear_cart()

                    return {
                        'current_price': current_price,
                        'original_price': original_price,
                        'is_on_sale': original_price != current_price if original_price else False
                    }

        except Exception as e:
            self.logger.error(f"Error getting price from cart for {product_url}: {e}")

        return None

    def clear_cart(self):
        """Clear the shopping cart."""
        try:
            # Method 1: Click remove buttons
            remove_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.remove-item, .delete-item')
            for button in remove_buttons:
                button.click()
                time.sleep(0.5)

            # Method 2: Navigate to clear cart endpoint (if available)
            # self.driver.get(f"{self.base_url}/cart/clear")

        except Exception as e:
            self.logger.error(f"Error clearing cart: {e}")

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Parse listing page and get prices by adding to cart.

        NOTE: This is slow as it visits each product page individually.
        """
        shoes = []

        product_containers = soup.select('.product-card')  # UPDATE SELECTOR

        for container in product_containers:
            try:
                # Extract basic info
                name_elem = container.select_one('.product-name')
                name = name_elem.get_text(strip=True) if name_elem else None

                link_elem = container.select_one('a[href]')
                product_url = link_elem['href'] if link_elem else None
                if product_url and not product_url.startswith('http'):
                    product_url = self.base_url + product_url

                product_id = container.get('data-product-id')

                if not product_url or not product_id:
                    continue

                # Get price by adding to cart
                # You need to know the "Add to Cart" button selector
                price_data = self.get_price_from_cart(
                    product_url,
                    add_to_cart_selector='.add-to-cart-btn'  # UPDATE THIS
                )

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

                self.logger.info(f"Got price for {name}: ${price_data['current_price']}")

                # Be polite - add delay
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"Error parsing product: {e}")
                continue

        return shoes

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Override to use Selenium."""
        try:
            self.init_driver()
            self.logger.info(f"Fetching with Selenium: {url}")

            self.driver.get(url)
            time.sleep(3)

            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'lxml')

        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Not used in this scraper."""
        return None

    def close(self):
        """Clean up Selenium driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        super().close()
