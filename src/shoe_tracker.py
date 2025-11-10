"""Main shoe sale tracking logic."""

import logging
from typing import List, Dict
from src.database import Database
from src.notifier import Notifier
from src.scrapers import SCRAPERS


class ShoeTracker:
    """Main class that coordinates scraping, database updates, and notifications."""

    def __init__(self, db_path: str = "shoe_sales.db"):
        """Initialize the shoe tracker."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = Database(db_path)
        self.notifier = Notifier()
        self.scrapers = [scraper_class() for scraper_class in SCRAPERS]

    def run_check(self):
        """Run a single check across all scrapers."""
        self.logger.info("Starting shoe sale check...")

        all_new_sales = []

        # Run all scrapers
        for scraper in self.scrapers:
            try:
                self.logger.info(f"Running scraper: {scraper.website_name}")
                shoes = scraper.scrape()

                # Update database and track new sales
                new_sales = []
                for shoe in shoes:
                    is_new_sale = self.db.upsert_shoe(shoe)
                    if is_new_sale:
                        new_sales.append(shoe)

                self.logger.info(
                    f"{scraper.website_name}: Found {len(shoes)} shoes, "
                    f"{len(new_sales)} new sales"
                )

                all_new_sales.extend(new_sales)

            except Exception as e:
                self.logger.error(f"Error running scraper {scraper.website_name}: {e}")

            finally:
                # Clean up scraper session
                try:
                    scraper.close()
                except:
                    pass

        # Send notifications for new sales
        if all_new_sales:
            unsent_alerts = self.db.get_unsent_alerts()
            sent_count = self.notifier.send_alerts(unsent_alerts)

            # Mark alerts as sent
            for alert in unsent_alerts[:sent_count]:
                self.db.mark_alert_sent(alert['id'])

        # Send notifications for items requiring manual review
        manual_review_items = self.db.get_manual_review_items()
        if manual_review_items:
            self.notifier.send_manual_review_alerts(manual_review_items)

        # Get and display stats
        stats = self.db.get_stats()
        self.notifier.send_summary(stats, len(all_new_sales), len(manual_review_items))

        self.logger.info(f"Check complete. Found {len(all_new_sales)} new sales, "
                        f"{len(manual_review_items)} items need manual review")

        return {
            'total_shoes_checked': sum(len(s.scrape()) for s in self.scrapers),
            'new_sales': len(all_new_sales),
            'stats': stats
        }

    def get_current_sales(self, limit: int = 20) -> List[Dict]:
        """Get currently active sales."""
        return self.db.get_active_sales(limit)

    def get_manual_review_items(self, limit: int = 20) -> List[Dict]:
        """Get items requiring manual review."""
        return self.db.get_manual_review_items(limit)

    def get_stats(self) -> Dict:
        """Get current statistics."""
        return self.db.get_stats()

    def close(self):
        """Clean up resources."""
        self.db.close()
        for scraper in self.scrapers:
            try:
                scraper.close()
            except:
                pass
