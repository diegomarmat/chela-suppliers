"""
Clear all data from suppliers database
Run this to start with a clean slate
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
    print("🗑️  Deleting all data from suppliers database...")

    # Delete in correct order to avoid foreign key violations
    cursor.execute("DELETE FROM invoice_items")
    invoice_items_count = cursor.rowcount
    print(f"   ✅ Deleted {invoice_items_count} invoice items")

    cursor.execute("DELETE FROM price_history")
    price_history_count = cursor.rowcount
    print(f"   ✅ Deleted {price_history_count} price history records")

    cursor.execute("DELETE FROM invoices")
    invoices_count = cursor.rowcount
    print(f"   ✅ Deleted {invoices_count} invoices")

    cursor.execute("DELETE FROM products")
    products_count = cursor.rowcount
    print(f"   ✅ Deleted {products_count} products")

    cursor.execute("DELETE FROM suppliers")
    suppliers_count = cursor.rowcount
    print(f"   ✅ Deleted {suppliers_count} suppliers")

    # Reset auto-increment counters
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('suppliers', 'invoices', 'invoice_items', 'products', 'price_history')")

    conn.commit()
    print("\n✅ Database cleared successfully! Starting fresh with ID 1 for all tables.")
    print("   Dashboard notes preserved (if any)")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
