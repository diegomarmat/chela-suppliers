"""
Database Migration: Add brand and invoice_name fields to Product table
Rename name -> short_name, preferred_supplier_id -> supplier_id
Created: Dec 26, 2025
"""

import os
from sqlalchemy import create_engine, text

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production (Railway with PostgreSQL)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=True)
    print("📍 Migrating PRODUCTION database (PostgreSQL on Railway)")
else:
    # Local development (SQLite)
    DB_PATH = "/Users/diegomarmat/Chela/suppliers/data/suppliers.db"
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=True)
    print(f"📍 Migrating LOCAL database ({DB_PATH})")

def migrate():
    """Run migration"""
    with engine.connect() as conn:
        print("\n🔄 Starting migration...")

        try:
            # Check if migration already applied
            result = conn.execute(text("SELECT * FROM products LIMIT 1"))
            columns = result.keys()

            if 'short_name' in columns:
                print("✅ Migration already applied! Columns exist.")
                return

            print("\n📝 Applying migrations...")

            # Step 1: Add new columns
            print("  1. Adding 'brand' column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN brand VARCHAR"))
            conn.commit()

            print("  2. Adding 'invoice_name' column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN invoice_name VARCHAR"))
            conn.commit()

            # Step 2: Rename 'name' to 'short_name'
            print("  3. Renaming 'name' to 'short_name'...")
            if 'sqlite' in str(engine.url):
                # SQLite doesn't support column rename directly, need to recreate table
                print("     (SQLite detected - using table recreation method)")
                conn.execute(text("""
                    CREATE TABLE products_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        short_name VARCHAR NOT NULL,
                        brand VARCHAR,
                        invoice_name VARCHAR,
                        category VARCHAR,
                        unit VARCHAR NOT NULL,
                        current_price FLOAT,
                        current_price_date DATE,
                        supplier_id INTEGER,
                        is_backup BOOLEAN NOT NULL DEFAULT 0,
                        unit_size FLOAT,
                        unit_size_measurement VARCHAR,
                        notes TEXT,
                        created_at DATETIME,
                        updated_at DATETIME,
                        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                """))
                conn.commit()

                print("     Copying data from old table...")
                conn.execute(text("""
                    INSERT INTO products_new
                    (id, short_name, brand, invoice_name, category, unit, current_price, current_price_date,
                     supplier_id, is_backup, unit_size, unit_size_measurement, notes, created_at, updated_at)
                    SELECT
                        id, name, NULL, NULL, category, unit, current_price, current_price_date,
                        preferred_supplier_id, is_backup, unit_size, unit_size_measurement, notes, created_at, updated_at
                    FROM products
                """))
                conn.commit()

                print("     Dropping old table...")
                conn.execute(text("DROP TABLE products"))
                conn.commit()

                print("     Renaming new table...")
                conn.execute(text("ALTER TABLE products_new RENAME TO products"))
                conn.commit()

            else:
                # PostgreSQL - can rename column directly
                print("     (PostgreSQL detected - using ALTER COLUMN)")
                conn.execute(text("ALTER TABLE products RENAME COLUMN name TO short_name"))
                conn.commit()

                conn.execute(text("ALTER TABLE products RENAME COLUMN preferred_supplier_id TO supplier_id"))
                conn.commit()

            print("\n✅ Migration completed successfully!")
            print("\n📊 New schema:")
            print("   - short_name (renamed from 'name')")
            print("   - brand (new, optional)")
            print("   - invoice_name (new, optional for OCR)")
            print("   - supplier_id (renamed from 'preferred_supplier_id')")

        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()
