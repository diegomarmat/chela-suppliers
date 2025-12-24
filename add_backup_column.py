"""
Add is_backup column to products table
Run this once to update the database schema
"""

import sqlite3
import os

# Database path
db_path = "/Users/diegomarmat/Chela/suppliers/data/suppliers.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(products)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'is_backup' in columns:
        print("✅ Column 'is_backup' already exists in products table")
    else:
        # Add the column
        cursor.execute("ALTER TABLE products ADD COLUMN is_backup BOOLEAN DEFAULT FALSE")
        conn.commit()
        print("✅ Successfully added 'is_backup' column to products table")
        print("   Default value: FALSE (all existing products are primary suppliers)")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✅ Database migration complete!")
