"""
Add needs_review column to invoices table
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
    cursor.execute("PRAGMA table_info(invoices)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'needs_review' in columns:
        print("✅ Column 'needs_review' already exists in invoices table")
    else:
        # Add the column
        cursor.execute("ALTER TABLE invoices ADD COLUMN needs_review BOOLEAN DEFAULT FALSE")
        conn.commit()
        print("✅ Successfully added 'needs_review' column to invoices table")
        print("   Use this to mark invoices that need follow-up (confirm details, returns, etc.)")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✅ Database migration complete!")
