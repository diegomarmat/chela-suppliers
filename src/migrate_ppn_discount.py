"""
Database Migration: Add PPN Rate and Discount Fields
- Add ppn_rate to suppliers table
- Add discount_percentage, ppn_percentage, ppn_amount to invoice_items table
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production (Railway with PostgreSQL)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=True)
    db_type = "PostgreSQL"
else:
    # Local development (SQLite)
    DB_PATH = "/Users/diegomarmat/Chela/suppliers/data/suppliers.db"
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        sys.exit(1)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=True)
    db_type = "SQLite"

print(f"\n🔧 Running PPN/Discount migration on {db_type}...\n")

try:
    inspector = inspect(engine)

    with engine.connect() as conn:
        # Check and add ppn_rate to suppliers
        supplier_columns = [col['name'] for col in inspector.get_columns('suppliers')]
        if 'ppn_rate' not in supplier_columns:
            print("📝 Adding ppn_rate column to suppliers table...")
            conn.execute(text("""
                ALTER TABLE suppliers
                ADD COLUMN ppn_rate FLOAT DEFAULT 11.0
            """))
            print("   ✓ ppn_rate added")
        else:
            print("   ⚠️  ppn_rate already exists, skipping")

        # Check and add discount/ppn fields to invoice_items
        item_columns = [col['name'] for col in inspector.get_columns('invoice_items')]

        if 'discount_percentage' not in item_columns:
            print("📝 Adding discount_percentage column to invoice_items table...")
            conn.execute(text("""
                ALTER TABLE invoice_items
                ADD COLUMN discount_percentage FLOAT
            """))
            print("   ✓ discount_percentage added")
        else:
            print("   ⚠️  discount_percentage already exists, skipping")

        if 'ppn_percentage' not in item_columns:
            print("📝 Adding ppn_percentage column to invoice_items table...")
            conn.execute(text("""
                ALTER TABLE invoice_items
                ADD COLUMN ppn_percentage FLOAT
            """))
            print("   ✓ ppn_percentage added")
        else:
            print("   ⚠️  ppn_percentage already exists, skipping")

        if 'ppn_amount' not in item_columns:
            print("📝 Adding ppn_amount column to invoice_items table...")
            conn.execute(text("""
                ALTER TABLE invoice_items
                ADD COLUMN ppn_amount FLOAT
            """))
            print("   ✓ ppn_amount added")
        else:
            print("   ⚠️  ppn_amount already exists, skipping")

        conn.commit()
        print("\n✅ PPN/Discount migration completed successfully!")
        print("\nChanges:")
        print("  ✓ Suppliers now have ppn_rate field (default 11%)")
        print("  ✓ Invoice items can now store discount %, PPN %, and PPN amount")

except Exception as e:
    print(f"\n❌ Migration failed: {str(e)}")
    sys.exit(1)
