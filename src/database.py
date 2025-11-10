"""Database module for storing and managing shoe sale data."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os


class Database:
    """Handles all database operations for shoe sale tracking."""

    def __init__(self, db_path: str = "shoe_sales.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def init_db(self):
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Table for storing shoe products and their current prices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                brand TEXT,
                website TEXT NOT NULL,
                url TEXT NOT NULL,
                current_price REAL,
                original_price REAL,
                discount_percentage REAL,
                is_on_sale BOOLEAN DEFAULT 0,
                price_hidden BOOLEAN DEFAULT 0,
                requires_manual_review BOOLEAN DEFAULT 0,
                last_checked TIMESTAMP,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_url TEXT
            )
        """)

        # Table for tracking price history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                price REAL NOT NULL,
                was_on_sale BOOLEAN DEFAULT 0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES shoes(product_id)
            )
        """)

        # Table for tracking when new sales are detected
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                alert_sent BOOLEAN DEFAULT 0,
                alert_sent_at TIMESTAMP,
                sale_price REAL,
                original_price REAL,
                discount_percentage REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES shoes(product_id)
            )
        """)

        self.conn.commit()

    def upsert_shoe(self, shoe_data: Dict) -> bool:
        """Insert or update shoe information. Returns True if it's a new sale."""
        cursor = self.conn.cursor()

        # Check if shoe already exists
        cursor.execute("SELECT * FROM shoes WHERE product_id = ?", (shoe_data['product_id'],))
        existing = cursor.fetchone()

        is_new_sale = False

        if existing:
            # Check if sale status changed
            was_on_sale = existing['is_on_sale']
            is_now_on_sale = shoe_data.get('is_on_sale', False)

            if is_now_on_sale and not was_on_sale:
                is_new_sale = True

            # Update existing shoe
            cursor.execute("""
                UPDATE shoes SET
                    name = ?,
                    brand = ?,
                    url = ?,
                    current_price = ?,
                    original_price = ?,
                    discount_percentage = ?,
                    is_on_sale = ?,
                    price_hidden = ?,
                    requires_manual_review = ?,
                    last_checked = ?,
                    image_url = ?
                WHERE product_id = ?
            """, (
                shoe_data['name'],
                shoe_data.get('brand'),
                shoe_data['url'],
                shoe_data.get('current_price'),
                shoe_data.get('original_price'),
                shoe_data.get('discount_percentage'),
                shoe_data.get('is_on_sale', False),
                shoe_data.get('price_hidden', False),
                shoe_data.get('requires_manual_review', False),
                datetime.now(),
                shoe_data.get('image_url'),
                shoe_data['product_id']
            ))
        else:
            # Insert new shoe
            is_new_sale = shoe_data.get('is_on_sale', False)

            cursor.execute("""
                INSERT INTO shoes (
                    product_id, name, brand, website, url, current_price,
                    original_price, discount_percentage, is_on_sale,
                    price_hidden, requires_manual_review,
                    last_checked, image_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                shoe_data['product_id'],
                shoe_data['name'],
                shoe_data.get('brand'),
                shoe_data['website'],
                shoe_data['url'],
                shoe_data.get('current_price'),
                shoe_data.get('original_price'),
                shoe_data.get('discount_percentage'),
                shoe_data.get('is_on_sale', False),
                shoe_data.get('price_hidden', False),
                shoe_data.get('requires_manual_review', False),
                datetime.now(),
                shoe_data.get('image_url')
            ))

        # Add to price history
        cursor.execute("""
            INSERT INTO price_history (product_id, price, was_on_sale)
            VALUES (?, ?, ?)
        """, (
            shoe_data['product_id'],
            shoe_data.get('current_price'),
            shoe_data.get('is_on_sale', False)
        ))

        # Create sale alert if it's a new sale
        if is_new_sale:
            cursor.execute("""
                INSERT INTO sale_alerts (
                    product_id, sale_price, original_price, discount_percentage
                ) VALUES (?, ?, ?, ?)
            """, (
                shoe_data['product_id'],
                shoe_data.get('current_price'),
                shoe_data.get('original_price'),
                shoe_data.get('discount_percentage')
            ))

        self.conn.commit()
        return is_new_sale

    def get_active_sales(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all shoes currently on sale."""
        cursor = self.conn.cursor()

        query = """
            SELECT * FROM shoes
            WHERE is_on_sale = 1
            ORDER BY discount_percentage DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_unsent_alerts(self) -> List[Dict]:
        """Get sale alerts that haven't been sent yet."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT sa.*, s.name, s.brand, s.url, s.website, s.image_url
            FROM sale_alerts sa
            JOIN shoes s ON sa.product_id = s.product_id
            WHERE sa.alert_sent = 0
            ORDER BY sa.created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def mark_alert_sent(self, alert_id: int):
        """Mark a sale alert as sent."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sale_alerts
            SET alert_sent = 1, alert_sent_at = ?
            WHERE id = ?
        """, (datetime.now(), alert_id))
        self.conn.commit()

    def get_manual_review_items(self, limit: Optional[int] = None) -> List[Dict]:
        """Get items that require manual review (hidden prices)."""
        cursor = self.conn.cursor()

        query = """
            SELECT * FROM shoes
            WHERE requires_manual_review = 1
            ORDER BY last_checked DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def mark_manual_review_done(self, product_id: str):
        """Mark a manual review item as reviewed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE shoes
            SET requires_manual_review = 0
            WHERE product_id = ?
        """, (product_id,))
        self.conn.commit()

    def get_price_history(self, product_id: str) -> List[Dict]:
        """Get price history for a specific product."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM price_history
            WHERE product_id = ?
            ORDER BY recorded_at DESC
        """, (product_id,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM shoes")
        total_shoes = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM shoes WHERE is_on_sale = 1")
        shoes_on_sale = cursor.fetchone()['total']

        cursor.execute("""
            SELECT AVG(discount_percentage) as avg_discount
            FROM shoes WHERE is_on_sale = 1
        """)
        avg_discount = cursor.fetchone()['avg_discount'] or 0

        return {
            'total_shoes': total_shoes,
            'shoes_on_sale': shoes_on_sale,
            'average_discount': round(avg_discount, 2)
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
