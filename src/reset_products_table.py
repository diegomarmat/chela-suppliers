"""
Reset Products Table Only (Keep Suppliers)
Railway Production - One-time script
Created: Dec 26, 2025
"""

import os
from sqlalchemy import create_engine, text

# Railway PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set (this is for Railway only)")
    exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)

print("🚨 WARNING: This will DROP the products table and recreate it!")
print("📍 Database: Railway Production (PostgreSQL)")
print("✅ Suppliers table: WILL BE PRESERVED")
print("⚠️  Products table: WILL BE DROPPED (1 product will be lost)")

confirm = input("\nType 'RESET' to confirm: ")

if confirm != "RESET":
    print("❌ Cancelled")
    exit(0)

with engine.connect() as conn:
    print("\n🔄 Dropping products table...")

    # Drop dependent tables first
    conn.execute(text("DROP TABLE IF EXISTS price_history CASCADE"))
    conn.commit()

    conn.execute(text("DROP TABLE IF EXISTS invoice_items CASCADE"))
    conn.commit()

    conn.execute(text("DROP TABLE IF EXISTS products CASCADE"))
    conn.commit()

    print("✅ Products table dropped")

    print("\n🔄 Creating products table with new schema...")
    conn.execute(text("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            short_name VARCHAR NOT NULL,
            brand VARCHAR,
            invoice_name VARCHAR,
            category VARCHAR,
            unit VARCHAR NOT NULL,
            current_price FLOAT,
            current_price_date DATE,
            supplier_id INTEGER REFERENCES suppliers(id),
            is_backup BOOLEAN NOT NULL DEFAULT FALSE,
            unit_size FLOAT,
            unit_size_measurement VARCHAR,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()

    print("✅ Products table created with new schema")

    print("\n🔄 Recreating price_history table...")
    conn.execute(text("""
        CREATE TABLE price_history (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            invoice_id INTEGER NOT NULL REFERENCES invoices(id),
            price FLOAT NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()

    print("✅ Price history table recreated")

    print("\n🔄 Recreating invoice_items table...")
    conn.execute(text("""
        CREATE TABLE invoice_items (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER NOT NULL REFERENCES invoices(id),
            product_id INTEGER REFERENCES products(id),
            product_name VARCHAR NOT NULL,
            category VARCHAR,
            quantity FLOAT NOT NULL,
            unit VARCHAR NOT NULL,
            unit_price FLOAT NOT NULL,
            total_price FLOAT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()

    print("✅ Invoice items table recreated")

print("\n✅ DONE! Database ready for new schema.")
print("📝 Astik can now re-enter that 1 product with brand field.")
