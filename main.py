#!/usr/bin/env python3
"""
Running Shoe Sale Tracker

This application monitors multiple websites for running shoe sales and sends
notifications when new sales are found.
"""

import argparse
import logging
import sys
import schedule
import time
from datetime import datetime
from src.shoe_tracker import ShoeTracker
from src.config import Config


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)

    # File handler
    file_handler = logging.FileHandler('logs/shoe_tracker.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def run_once(tracker: ShoeTracker):
    """Run a single check."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info(f"Starting check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        result = tracker.run_check()
        logger.info(f"Check completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during check: {e}", exc_info=True)
        return None


def run_scheduled(tracker: ShoeTracker, interval_minutes: int):
    """Run checks on a schedule."""
    logger = logging.getLogger(__name__)

    logger.info(f"Starting scheduled checks every {interval_minutes} minutes")
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    # Run immediately on start
    run_once(tracker)

    # Schedule future runs
    schedule.every(interval_minutes).minutes.do(run_once, tracker)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds if a job is due
    except KeyboardInterrupt:
        logger.info("\nStopping scheduled checks...")
        tracker.close()


def show_sales(tracker: ShoeTracker, limit: int):
    """Display current sales."""
    sales = tracker.get_current_sales(limit)

    if not sales:
        print("No sales found in database yet. Run a check first!")
        return

    print("\n" + "=" * 80)
    print(f"CURRENT RUNNING SHOE SALES (showing {len(sales)} items)")
    print("=" * 80 + "\n")

    for i, sale in enumerate(sales, 1):
        print(f"{i}. {sale['name']}")
        if sale.get('brand'):
            print(f"   Brand: {sale['brand']}")
        print(f"   Website: {sale['website']}")
        print(f"   Original: ${sale['original_price']:.2f} → Sale: ${sale['current_price']:.2f}")
        print(f"   Discount: {sale['discount_percentage']:.1f}% OFF")
        print(f"   URL: {sale['url']}")
        print(f"   Last checked: {sale['last_checked']}")
        print()

    stats = tracker.get_stats()
    print("=" * 80)
    print(f"Total shoes tracked: {stats['total_shoes']}")
    print(f"Currently on sale: {stats['shoes_on_sale']}")
    print(f"Average discount: {stats['average_discount']:.1f}%")
    print("=" * 80 + "\n")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Running Shoe Sale Tracker - Monitor websites for running shoe sales'
    )

    parser.add_argument(
        '--mode',
        choices=['once', 'schedule', 'show'],
        default='schedule',
        help='Run mode: once (single check), schedule (continuous), show (display current sales)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=Config.CHECK_INTERVAL_MINUTES,
        help=f'Check interval in minutes (default: {Config.CHECK_INTERVAL_MINUTES})'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Number of sales to show in "show" mode (default: 20)'
    )

    parser.add_argument(
        '--db',
        type=str,
        default=Config.DATABASE_PATH,
        help=f'Database file path (default: {Config.DATABASE_PATH})'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Create tracker
    tracker = ShoeTracker(db_path=args.db)

    try:
        if args.mode == 'once':
            # Run single check
            logger.info("Running single check...")
            run_once(tracker)

        elif args.mode == 'schedule':
            # Run on schedule
            run_scheduled(tracker, args.interval)

        elif args.mode == 'show':
            # Show current sales
            show_sales(tracker, args.limit)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        tracker.close()


if __name__ == '__main__':
    main()
