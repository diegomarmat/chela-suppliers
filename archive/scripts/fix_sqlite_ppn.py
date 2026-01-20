"""
Fix SQLite constraint for manual PPN handling
SQLite doesn't support ALTER CONSTRAINT, so we need to recreate the table
"""

import os
import sqlite3

DB_PATH = "/Users/diegomarmat/Chela/suppliers/data/suppliers.db"

if not os.path.exists(DB_PATH):
    print(f"❌ Database not found at: {DB_PATH}")
    exit(1)

print(f"🔧 Fixing SQLite database at: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Step 1: Create new suppliers table with updated constraint
    print("📝 Creating new suppliers table with 'manual' PPN option...")
    cursor.execute("""
        CREATE TABLE suppliers_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name VARCHAR NOT NULL,
            short_name VARCHAR NOT NULL,
            category VARCHAR,
            contact_person VARCHAR,
            phone VARCHAR,
            order_phone VARCHAR,
            admin_phone VARCHAR,
            email VARCHAR,
            payment_terms VARCHAR NOT NULL DEFAULT 'cash' CHECK(payment_terms IN ('cash', '2week', 'monthly')),
            ppn_handling VARCHAR NOT NULL DEFAULT 'included' CHECK(ppn_handling IN ('included', 'added', 'manual')),
            bank_name VARCHAR,
            bank_account_number VARCHAR,
            bank_account_name VARCHAR,
            delivery_days VARCHAR,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Step 2: Copy data from old table to new table
    print("📝 Copying existing supplier data...")
    cursor.execute("""
        INSERT INTO suppliers_new
        SELECT * FROM suppliers
    """)

    # Step 3: Drop old table
    print("📝 Removing old suppliers table...")
    cursor.execute("DROP TABLE suppliers")

    # Step 4: Rename new table to suppliers
    print("📝 Renaming new table...")
    cursor.execute("ALTER TABLE suppliers_new RENAME TO suppliers")

    conn.commit()
    print("\n✅ SQLite database fixed successfully!")
    print("   ✓ Suppliers can now have ppn_handling = 'manual'")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {str(e)}")
    exit(1)
finally:
    conn.close()
