"""
Add dashboard_notes table for shared work notes
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
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_notes'")
    table_exists = cursor.fetchone() is not None

    if table_exists:
        print("✅ Table 'dashboard_notes' already exists")
    else:
        # Create the table
        cursor.execute("""
            CREATE TABLE dashboard_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert initial empty row
        cursor.execute("INSERT INTO dashboard_notes (notes) VALUES ('')")

        conn.commit()
        print("✅ Successfully created 'dashboard_notes' table")
        print("   Shared scratchpad for work notes between Diego and Astik")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✅ Database migration complete!")
