"""
Chela Suppliers Management System
SQLAlchemy Models
Created: December 21, 2025
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    Date, DateTime, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

# Database configuration
# Use DATABASE_URL from environment (Railway) or fallback to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production (Railway with PostgreSQL)
    # Railway provides postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # Local development (SQLite)
    DB_PATH = "/Users/diegomarmat/Chela/suppliers/data/suppliers.db"
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


# ============================================================================
# MODELS
# ============================================================================

class Supplier(Base):
    """Suppliers - who we buy from"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False)  # Official/legal name
    short_name = Column(String, nullable=False)    # Fantasy name/nickname
    category = Column(String)  # Supplier category: Food, Drinks, Operational
    contact_person = Column(String)
    phone = Column(String)  # Legacy field (kept for compatibility)
    order_phone = Column(String)  # Phone number for placing orders
    admin_phone = Column(String)  # Phone number for admin/billing contacts
    email = Column(String)
    payment_terms = Column(
        String,
        CheckConstraint("payment_terms IN ('cash', '2week', 'monthly')"),
        nullable=False,
        default='cash'
    )
    ppn_handling = Column(
        String,
        CheckConstraint("ppn_handling IN ('included', 'added')"),
        nullable=False,
        default='included'
    )  # Tax handling: 'included' = final price shown, 'added' = subtotal + PPN
    bank_name = Column(String)
    bank_account_number = Column(String)
    bank_account_name = Column(String)
    delivery_days = Column(String)  # Days they deliver (e.g., "Mon, Wed, Fri")
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    invoices = relationship("Invoice", back_populates="supplier")
    products = relationship("Product", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, short_name='{self.short_name}', company_name='{self.company_name}')>"


class Invoice(Base):
    """Invoices - bills we receive from suppliers"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    invoice_number = Column(String)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    total_amount = Column(Float, nullable=False)
    payment_status = Column(
        String,
        CheckConstraint("payment_status IN ('pending', 'paid', 'overdue')"),
        nullable=False,
        default='pending'
    )
    payment_date = Column(Date)
    payment_method = Column(
        String,
        CheckConstraint("payment_method IN ('cash', 'transfer', NULL)")
    )
    invoice_file_path = Column(String)
    notes = Column(Text)
    needs_review = Column(Boolean, nullable=False, default=False)  # Flag for "details to check"
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.id}, supplier_id={self.supplier_id}, date={self.invoice_date}, total={self.total_amount})>"


class InvoiceItem(Base):
    """Invoice Items - line items on each invoice"""
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    product_name = Column(String, nullable=False)
    category = Column(String)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, product='{self.product_name}', qty={self.quantity}, price={self.total_price})>"


class Product(Base):
    """Products - master catalog of all products we buy"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String, nullable=False)  # Human-readable name: "Cheese Block"
    brand = Column(String)  # Optional brand: "BECA" (nullable for generic items like vegetables)
    invoice_name = Column(String)  # For OCR matching: "BECA Cheese Block Imported France Premium" (populated later)
    category = Column(String)
    unit = Column(String, nullable=False)
    current_price = Column(Float)
    current_price_date = Column(Date)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))  # Main supplier for this product
    is_backup = Column(Boolean, nullable=False, default=False)
    unit_size = Column(Float)  # For non-exact units (pcs, bottle, etc.) - how much does 1 unit contain
    unit_size_measurement = Column(String)  # g, ml, kg, L
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    invoice_items = relationship("InvoiceItem", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, short_name='{self.short_name}', brand='{self.brand}', price={self.current_price})>"

    def display_name(self):
        """Return formatted display name: 'Short Name (Brand)' or just 'Short Name'"""
        if self.brand:
            return f"{self.short_name} ({self.brand})"
        return self.short_name

    def invoice_dropdown_name(self):
        """Return formatted name for invoice dropdowns: 'Short Name (Brand - unit)' or 'Short Name (unit)'"""
        if self.brand:
            return f"{self.short_name} ({self.brand} - {self.unit})"
        return f"{self.short_name} ({self.unit})"


class PriceHistory(Base):
    """Price History - track price changes over time"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    price = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    product = relationship("Product", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, date={self.date})>"


class DashboardNotes(Base):
    """Dashboard Notes - shared scratchpad for work notes"""
    __tablename__ = "dashboard_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<DashboardNotes(id={self.id}, updated={self.updated_at})>"


# ============================================================================
# DATABASE SESSION HELPER
# ============================================================================

def get_db():
    """Get database session - use with context manager or next()"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database tables (if not exists)"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    # Test database connection
    if DATABASE_URL:
        print(f"Database: PostgreSQL (Railway)")
    else:
        print(f"Database path: {DB_PATH}")
        print(f"Database exists: {os.path.exists(DB_PATH)}")

    # Test session
    db = next(get_db())
    suppliers_count = db.query(Supplier).count()
    invoices_count = db.query(Invoice).count()
    products_count = db.query(Product).count()
    db.close()

    print(f"✅ Suppliers: {suppliers_count}")
    print(f"✅ Invoices: {invoices_count}")
    print(f"✅ Products: {products_count}")
    print("✅ Models working correctly!")
