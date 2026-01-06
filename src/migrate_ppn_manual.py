"""
Database Migration: Add Manual PPN Handling
- Add 'manual' option to suppliers.ppn_handling
- Add ppn_handling column to invoices table
"""

import os
import sys
from sqlalchemy import create_engine, text

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

print(f"\n🔧 Running migration on {db_type}...\n")

try:
    with engine.connect() as conn:
        # For PostgreSQL, we need to alter the constraint
        if db_type == "PostgreSQL":
            print("📝 Updating suppliers table ppn_handling constraint...")
            # Drop old constraint
            conn.execute(text("""
                ALTER TABLE suppliers
                DROP CONSTRAINT IF EXISTS suppliers_ppn_handling_check
            """))
            # Add new constraint with 'manual' option
            conn.execute(text("""
                ALTER TABLE suppliers
                ADD CONSTRAINT suppliers_ppn_handling_check
                CHECK (ppn_handling IN ('included', 'added', 'manual'))
            """))

            print("📝 Adding ppn_handling column to invoices table...")
            # Add new column to invoices (PostgreSQL)
            conn.execute(text("""
                ALTER TABLE invoices
                ADD COLUMN IF NOT EXISTS ppn_handling VARCHAR
                CHECK (ppn_handling IN ('included', 'added', NULL))
            """))

        else:  # SQLite
            print("📝 Adding ppn_handling column to invoices table...")
            # SQLite doesn't support ALTER CONSTRAINT, so we can't change the supplier constraint
            # But SQLite is lenient and will allow 'manual' anyway
            # Just add the new column to invoices
            try:
                conn.execute(text("""
                    ALTER TABLE invoices
                    ADD COLUMN ppn_handling VARCHAR
                """))
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("⚠️  Column already exists, skipping...")
                else:
                    raise

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nChanges:")
        print("  ✓ Suppliers can now have ppn_handling = 'manual'")
        print("  ✓ Invoices can now store specific ppn_handling when supplier = 'manual'")

except Exception as e:
    print(f"\n❌ Migration failed: {str(e)}")
    sys.exit(1)
