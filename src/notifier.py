"""Notification system for sending sale alerts."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime
from src.config import Config


class Notifier:
    """Handles sending notifications about shoe sales."""

    def __init__(self):
        """Initialize the notifier."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.method = Config.NOTIFICATION_METHOD.lower()

    def send_alerts(self, alerts: List[Dict]) -> int:
        """
        Send notifications for new sale alerts.

        Args:
            alerts: List of alert dictionaries from database

        Returns:
            Number of alerts successfully sent
        """
        if not alerts:
            self.logger.info("No new alerts to send")
            return 0

        self.logger.info(f"Sending {len(alerts)} sale alerts via {self.method}")

        if self.method == 'email':
            return self._send_email_alerts(alerts)
        else:  # Default to console
            return self._send_console_alerts(alerts)

    def _send_console_alerts(self, alerts: List[Dict]) -> int:
        """Print alerts to console."""
        print("\n" + "=" * 80)
        print(f"🔔 NEW RUNNING SHOE SALES FOUND! ({len(alerts)} items)")
        print("=" * 80 + "\n")

        for i, alert in enumerate(alerts, 1):
            print(f"{i}. {alert['name']}")
            if alert.get('brand'):
                print(f"   Brand: {alert['brand']}")
            print(f"   Website: {alert['website']}")
            print(f"   Original Price: ${alert['original_price']:.2f}")
            print(f"   Sale Price: ${alert['sale_price']:.2f}")
            print(f"   Discount: {alert['discount_percentage']:.1f}% OFF")
            print(f"   URL: {alert['url']}")
            print()

        print("=" * 80 + "\n")

        return len(alerts)

    def _send_email_alerts(self, alerts: List[Dict]) -> int:
        """Send alerts via email."""
        if not Config.EMAIL_TO or not Config.EMAIL_FROM:
            self.logger.error("Email configuration missing. Please set EMAIL_TO and EMAIL_FROM in .env")
            return 0

        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🏃 {len(alerts)} New Running Shoe Sales Found!"
            msg['From'] = Config.EMAIL_FROM
            msg['To'] = Config.EMAIL_TO

            # Create email body
            text_body = self._create_text_email(alerts)
            html_body = self._create_html_email(alerts)

            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
                    server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {Config.EMAIL_TO}")
            return len(alerts)

        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return 0

    def _create_text_email(self, alerts: List[Dict]) -> str:
        """Create plain text email body."""
        lines = [
            f"NEW RUNNING SHOE SALES FOUND! ({len(alerts)} items)",
            f"Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 80,
            ""
        ]

        for i, alert in enumerate(alerts, 1):
            lines.append(f"{i}. {alert['name']}")
            if alert.get('brand'):
                lines.append(f"   Brand: {alert['brand']}")
            lines.append(f"   Website: {alert['website']}")
            lines.append(f"   Original Price: ${alert['original_price']:.2f}")
            lines.append(f"   Sale Price: ${alert['sale_price']:.2f}")
            lines.append(f"   Discount: {alert['discount_percentage']:.1f}% OFF")
            lines.append(f"   URL: {alert['url']}")
            lines.append("")

        lines.append("-" * 80)
        lines.append("")
        lines.append("Happy shopping!")

        return "\n".join(lines)

    def _create_html_email(self, alerts: List[Dict]) -> str:
        """Create HTML email body."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .alert {{ background-color: #f9f9f9; border-left: 4px solid #4CAF50; margin: 20px 0; padding: 15px; }}
                .alert h3 {{ margin-top: 0; color: #333; }}
                .price {{ font-size: 18px; font-weight: bold; }}
                .original-price {{ text-decoration: line-through; color: #999; }}
                .sale-price {{ color: #e74c3c; }}
                .discount {{ background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px; display: inline-block; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏃 New Running Shoe Sales Found!</h1>
                <p>{len(alerts)} amazing deals waiting for you</p>
                <p style="font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        for alert in alerts:
            brand_text = f"<p><strong>Brand:</strong> {alert['brand']}</p>" if alert.get('brand') else ""

            html += f"""
            <div class="alert">
                <h3>{alert['name']}</h3>
                {brand_text}
                <p><strong>Website:</strong> {alert['website']}</p>
                <p class="price">
                    <span class="original-price">${alert['original_price']:.2f}</span>
                    →
                    <span class="sale-price">${alert['sale_price']:.2f}</span>
                </p>
                <p><span class="discount">{alert['discount_percentage']:.1f}% OFF</span></p>
                <a href="{alert['url']}" class="button">View Deal</a>
            </div>
            """

        html += """
            <div class="footer">
                <p>This is an automated alert from your Running Shoe Sale Tracker</p>
                <p>Happy shopping! 🎉</p>
            </div>
        </body>
        </html>
        """

        return html

    def send_summary(self, stats: Dict, sales_count: int, manual_review_count: int = 0):
        """Send a summary of the current state."""
        if self.method == 'console':
            print("\n" + "-" * 60)
            print("SHOE SALE TRACKER SUMMARY")
            print("-" * 60)
            print(f"Total shoes tracked: {stats['total_shoes']}")
            print(f"Currently on sale: {stats['shoes_on_sale']}")
            print(f"Average discount: {stats['average_discount']:.1f}%")
            print(f"New sales found this check: {sales_count}")
            if manual_review_count > 0:
                print(f"Items requiring manual review: {manual_review_count}")
            print("-" * 60 + "\n")

    def send_manual_review_alerts(self, items: List[Dict]) -> int:
        """
        Send notifications for items requiring manual review (hidden prices).

        Args:
            items: List of shoe dictionaries that need manual review

        Returns:
            Number of alerts successfully sent
        """
        if not items:
            return 0

        self.logger.info(f"Sending manual review alerts for {len(items)} items")

        if self.method == 'email':
            return self._send_manual_review_email(items)
        else:  # Default to console
            return self._send_manual_review_console(items)

    def _send_manual_review_console(self, items: List[Dict]) -> int:
        """Print manual review items to console."""
        print("\n" + "=" * 80)
        print(f"🔍 ITEMS REQUIRING MANUAL REVIEW ({len(items)} items)")
        print("These items may be on sale but prices are hidden - check them manually!")
        print("=" * 80 + "\n")

        for i, item in enumerate(items, 1):
            print(f"{i}. {item['name']}")
            if item.get('brand'):
                print(f"   Brand: {item['brand']}")
            print(f"   Website: {item['website']}")
            print(f"   💡 Price Hidden - Check cart for actual price")
            print(f"   URL: {item['url']}")
            print()

        print("=" * 80 + "\n")

        return len(items)

    def _send_manual_review_email(self, items: List[Dict]) -> int:
        """Send manual review items via email."""
        if not Config.EMAIL_TO or not Config.EMAIL_FROM:
            self.logger.error("Email configuration missing")
            return 0

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔍 {len(items)} Items Need Manual Price Check"
            msg['From'] = Config.EMAIL_FROM
            msg['To'] = Config.EMAIL_TO

            # Create email body
            text_body = self._create_manual_review_text_email(items)
            html_body = self._create_manual_review_html_email(items)

            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
                    server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)

            self.logger.info(f"Manual review email sent to {Config.EMAIL_TO}")
            return len(items)

        except Exception as e:
            self.logger.error(f"Error sending manual review email: {e}")
            return 0

    def _create_manual_review_text_email(self, items: List[Dict]) -> str:
        """Create plain text email for manual review items."""
        lines = [
            f"ITEMS REQUIRING MANUAL REVIEW ({len(items)} items)",
            "These items may be on sale but prices are hidden.",
            f"Alert sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 80,
            ""
        ]

        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item['name']}")
            if item.get('brand'):
                lines.append(f"   Brand: {item['brand']}")
            lines.append(f"   Website: {item['website']}")
            lines.append(f"   Price: HIDDEN - Check cart for actual price")
            lines.append(f"   URL: {item['url']}")
            lines.append("")

        lines.append("-" * 80)
        lines.append("")
        lines.append("Click each link to check the price manually!")

        return "\n".join(lines)

    def _create_manual_review_html_email(self, items: List[Dict]) -> str:
        """Create HTML email for manual review items."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .item {{ background-color: #fff3cd; border-left: 4px solid #FF9800; margin: 20px 0; padding: 15px; }}
                .item h3 {{ margin-top: 0; color: #333; }}
                .button {{ background-color: #FF9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                .warning {{ color: #856404; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Manual Price Check Required</h1>
                <p>{len(items)} items need your attention</p>
                <p style="font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        for item in items:
            brand_text = f"<p><strong>Brand:</strong> {item['brand']}</p>" if item.get('brand') else ""

            html += f"""
            <div class="item">
                <h3>{item['name']}</h3>
                {brand_text}
                <p><strong>Website:</strong> {item['website']}</p>
                <p class="warning">💡 Price Hidden - Check cart for actual price</p>
                <a href="{item['url']}" class="button">Check Price</a>
            </div>
            """

        html += """
            <div class="footer">
                <p>These items may be on sale but require you to add them to your cart to see the price.</p>
                <p>Click "Check Price" to visit each product and check manually.</p>
            </div>
        </body>
        </html>
        """

        return html
