"""
Add unit_size and unit_size_measurement columns to products table
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
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(products)")
    columns = [column[1] for column in cursor.fetchall()]

    columns_to_add = []
    if 'unit_size' not in columns:
        columns_to_add.append(('unit_size', 'REAL'))
    if 'unit_size_measurement' not in columns:
        columns_to_add.append(('unit_size_measurement', 'TEXT'))

    if not columns_to_add:
        print("✅ Columns already exist in products table")
    else:
        for col_name, col_type in columns_to_add:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
            print(f"✅ Added '{col_name}' column to products table")

        conn.commit()
        print("   For non-exact units (pcs, bottle, box, ctn, pack) - stores measurement conversion")
        print("   Example: 1 bottle = 1000ml → unit_size=1000, unit_size_measurement='ml'")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✅ Database migration complete!")
