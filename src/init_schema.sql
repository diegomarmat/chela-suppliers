-- Chela Suppliers Management System
-- Database Schema v1.0
-- Created: December 21, 2025

-- ============================================================================
-- SUPPLIERS TABLE
-- Who we buy from
-- ============================================================================
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,  -- Official/legal name (e.g., PT KOPI BAR SELA)
    short_name TEXT NOT NULL,    -- Fantasy name/nickname (e.g., Chela)
    category TEXT,               -- Supplier category: Food, Drinks, Operational
    contact_person TEXT,
    phone TEXT,                  -- Legacy field (kept for compatibility)
    order_phone TEXT,            -- Phone number for placing orders
    admin_phone TEXT,            -- Phone number for admin/billing contacts
    email TEXT,
    payment_terms TEXT CHECK(payment_terms IN ('cash', '2week', 'monthly')) NOT NULL DEFAULT 'cash',
    bank_name TEXT,
    bank_account_number TEXT,
    bank_account_name TEXT,
    delivery_days TEXT,  -- Days they deliver (e.g., "Mon, Wed, Fri")
    is_active BOOLEAN NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INVOICES TABLE
-- Bills we receive from suppliers
-- ============================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    invoice_number TEXT,
    invoice_date DATE NOT NULL,
    due_date DATE,
    total_amount REAL NOT NULL,
    payment_status TEXT CHECK(payment_status IN ('pending', 'paid', 'overdue')) NOT NULL DEFAULT 'pending',
    payment_date DATE,
    payment_method TEXT CHECK(payment_method IN ('cash', 'transfer', NULL)),
    invoice_file_path TEXT,  -- Path to stored invoice photo/PDF
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- ============================================================================
-- INVOICE ITEMS TABLE
-- Line items on each invoice
-- ============================================================================
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER,  -- NULL if product not yet in catalog
    product_name TEXT NOT NULL,
    category TEXT,  -- We'll develop categories as we go
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,  -- kg, pcs, box, liter, etc.
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- ============================================================================
-- PRODUCTS TABLE
-- Master catalog of all products we buy (builds over time)
-- ============================================================================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    unit TEXT NOT NULL,  -- Standard unit of measure
    current_price REAL,  -- Latest price we paid
    current_price_date DATE,  -- When we last updated price
    preferred_supplier_id INTEGER,  -- Which supplier we usually buy from
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (preferred_supplier_id) REFERENCES suppliers(id)
);

-- ============================================================================
-- PRICE HISTORY TABLE
-- Track price changes over time
-- ============================================================================
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    invoice_id INTEGER NOT NULL,
    price REAL NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

-- ============================================================================
-- INDEXES for performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_invoices_supplier ON invoices(supplier_id);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_product ON invoice_items(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date);

-- ============================================================================
-- TRIGGERS to auto-update timestamps
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp
AFTER UPDATE ON suppliers
BEGIN
    UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_invoices_timestamp
AFTER UPDATE ON invoices
BEGIN
    UPDATE invoices SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_products_timestamp
AFTER UPDATE ON products
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- TRIGGER to auto-update product prices and create price history
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_product_price_on_invoice_item
AFTER INSERT ON invoice_items
WHEN NEW.product_id IS NOT NULL
BEGIN
    -- Update product's current price if this invoice is newer
    UPDATE products
    SET
        current_price = NEW.unit_price,
        current_price_date = (SELECT invoice_date FROM invoices WHERE id = NEW.invoice_id)
    WHERE
        id = NEW.product_id
        AND (current_price_date IS NULL OR current_price_date < (SELECT invoice_date FROM invoices WHERE id = NEW.invoice_id));

    -- Create price history entry
    INSERT INTO price_history (product_id, supplier_id, invoice_id, price, date)
    SELECT
        NEW.product_id,
        i.supplier_id,
        NEW.invoice_id,
        NEW.unit_price,
        i.invoice_date
    FROM invoices i
    WHERE i.id = NEW.invoice_id;
END;
