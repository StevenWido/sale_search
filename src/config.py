"""Configuration management for the shoe sale search application."""

import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Notification settings
    NOTIFICATION_METHOD = os.getenv('NOTIFICATION_METHOD', 'console')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

    # Scraping settings
    USER_AGENT = os.getenv(
        'USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    REQUEST_DELAY = int(os.getenv('REQUEST_DELAY', '2'))

    # Schedule settings
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '60'))

    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'shoe_sales.db')

    # Filtering settings
    MIN_DISCOUNT_PERCENTAGE = float(os.getenv('MIN_DISCOUNT_PERCENTAGE', '10'))

    @staticmethod
    def get_keywords() -> List[str]:
        """Get list of keywords to filter shoes."""
        keywords_str = os.getenv('KEYWORDS', 'running,run,runner,trail,marathon,athletic')
        return [kw.strip().lower() for kw in keywords_str.split(',')]

    @staticmethod
    def get_headers() -> dict:
        """Get HTTP headers for requests."""
        return {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
