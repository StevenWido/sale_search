#!/usr/bin/env python3
"""
Database migration script to add new columns for hidden price detection.

This script updates an existing database to add:
- price_hidden (BOOLEAN)
- requires_manual_review (BOOLEAN)

Run this if you have an existing database you want to keep.
"""

import sqlite3
import sys

def migrate_database(db_path='shoe_sales.db'):
    """Add new columns to existing database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Migrating database: {db_path}")
        print("-" * 60)

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(shoes)")
        columns = [col[1] for col in cursor.fetchall()]

        migrations_needed = []

        if 'price_hidden' not in columns:
            migrations_needed.append(('price_hidden', 'BOOLEAN DEFAULT 0'))

        if 'requires_manual_review' not in columns:
            migrations_needed.append(('requires_manual_review', 'BOOLEAN DEFAULT 0'))

        if not migrations_needed:
            print("✅ Database is already up to date!")
            conn.close()
            return

        print(f"Adding {len(migrations_needed)} new columns...")

        for column_name, column_def in migrations_needed:
            try:
                sql = f"ALTER TABLE shoes ADD COLUMN {column_name} {column_def}"
                cursor.execute(sql)
                print(f"  ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if 'duplicate column' in str(e).lower():
                    print(f"  ⚠️  Column {column_name} already exists, skipping")
                else:
                    raise

        conn.commit()
        conn.close()

        print("-" * 60)
        print("✅ Migration complete!")
        print("\nYou can now use the application with hidden price detection.")

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import os

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = 'shoe_sales.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("\nNo migration needed - the database will be created with correct schema on first run.")
        sys.exit(0)

    migrate_database(db_path)
