#!/usr/bin/env python3
"""
Test script for Dick's Sporting Goods scraper.

This script helps you test and debug the Dick's scraper.

Usage:
    python test_dicks_scraper.py
"""

import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.dicks_scraper import DicksScraper
from src.database import Database

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dicks_scraper_test.log')
    ]
)

logger = logging.getLogger(__name__)


def test_scraper():
    """Test the Dick's scraper."""
    logger.info("=" * 80)
    logger.info("TESTING DICK'S SPORTING GOODS SCRAPER")
    logger.info("=" * 80)

    # Create scraper
    scraper = DicksScraper()

    try:
        logger.info(f"Website: {scraper.website_name}")
        logger.info(f"URLs to scrape: {scraper.get_search_urls()}")
        logger.info("")

        # Run scraper
        logger.info("Starting scrape...")
        shoes = scraper.scrape()

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"SCRAPING COMPLETE - Found {len(shoes)} shoes")
        logger.info("=" * 80)
        logger.info("")

        if shoes:
            # Separate visible and hidden prices
            visible_prices = [s for s in shoes if not s.get('price_hidden')]
            hidden_prices = [s for s in shoes if s.get('price_hidden')]

            logger.info(f"Shoes with visible prices: {len(visible_prices)}")
            logger.info(f"Shoes with hidden prices (manual review): {len(hidden_prices)}")
            logger.info("")

            # Show first 5 with visible prices
            if visible_prices:
                logger.info("FIRST 5 SHOES WITH VISIBLE PRICES:")
                logger.info("-" * 80)
                for i, shoe in enumerate(visible_prices[:5], 1):
                    logger.info(f"{i}. {shoe['name']}")
                    if shoe.get('brand'):
                        logger.info(f"   Brand: {shoe['brand']}")
                    logger.info(f"   Price: ${shoe['current_price']:.2f}")
                    if shoe['is_on_sale']:
                        logger.info(f"   Original: ${shoe['original_price']:.2f} "
                                  f"({shoe['discount_percentage']:.1f}% off)")
                    logger.info(f"   URL: {shoe['url']}")
                    logger.info("")

            # Show first 5 with hidden prices
            if hidden_prices:
                logger.info("FIRST 5 SHOES REQUIRING MANUAL REVIEW:")
                logger.info("-" * 80)
                for i, shoe in enumerate(hidden_prices[:5], 1):
                    logger.info(f"{i}. {shoe['name']}")
                    if shoe.get('brand'):
                        logger.info(f"   Brand: {shoe['brand']}")
                    logger.info(f"   💡 Price Hidden - Check cart")
                    logger.info(f"   URL: {shoe['url']}")
                    logger.info("")

            # Ask if user wants to save to database
            logger.info("=" * 80)
            response = input("\nSave results to database? (y/n): ").strip().lower()

            if response == 'y':
                db = Database()
                saved_count = 0
                new_sales = 0

                for shoe in shoes:
                    is_new = db.upsert_shoe(shoe)
                    saved_count += 1
                    if is_new:
                        new_sales += 1

                db.close()

                logger.info(f"✅ Saved {saved_count} shoes to database")
                logger.info(f"   {new_sales} are new sales")
                logger.info(f"   {len(hidden_prices)} require manual review")
                logger.info("")
                logger.info("View with:")
                logger.info("  python main.py --mode show    # See sales")
                logger.info("  python main.py --mode review  # See items needing review")
            else:
                logger.info("Results not saved to database")

        else:
            logger.warning("No shoes found! This could mean:")
            logger.warning("1. The selectors need updating")
            logger.warning("2. The page didn't load properly")
            logger.warning("3. Cloudflare blocked the request")
            logger.warning("")
            logger.warning("Check 'dicks_scraper_test.log' for details")
            logger.warning("If a browser window opened, check if it loaded the page")

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        logger.error("")
        logger.error("Common issues:")
        logger.error("1. Selenium/ChromeDriver not installed")
        logger.error("2. Chrome browser not found")
        logger.error("3. Network/firewall blocking")
        logger.error("")
        logger.error("Install with: pip install selenium undetected-chromedriver")

    finally:
        # Clean up
        try:
            scraper.close()
            logger.info("Scraper closed")
        except:
            pass

    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    test_scraper()
