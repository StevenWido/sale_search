"""Scraper modules for different shoe retailers."""

from .base_scraper import BaseScraper
from .example_scraper import ExampleScraper
from .demo_scraper import DemoScraper

# List of all available scrapers
SCRAPERS = [
    DemoScraper,  # Demo scraper for testing
    # ExampleScraper,  # Template - uncomment when you create real scrapers
    # Add more scrapers here as you implement them
]

__all__ = ['BaseScraper', 'ExampleScraper', 'DemoScraper', 'SCRAPERS']
