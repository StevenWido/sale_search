"""Scraper modules for different shoe retailers."""

from .base_scraper import BaseScraper
from .example_scraper import ExampleScraper
from .demo_scraper import DemoScraper

# Real website scrapers (commented out until configured)
# from .adidas_scraper import AdidasScraper
# from .running_warehouse_scraper import RunningWarehouseScraper
# from .dicks_scraper import DicksScraper

# List of all available scrapers
SCRAPERS = [
    DemoScraper,  # Demo scraper for testing
    # ExampleScraper,  # Template - uncomment when you create real scrapers

    # Uncomment these after configuring the scrapers (see SCRAPER_IMPLEMENTATION_GUIDE.md):
    # AdidasScraper,
    # RunningWarehouseScraper,
    # DicksScraper,
]

__all__ = ['BaseScraper', 'ExampleScraper', 'DemoScraper', 'SCRAPERS']
