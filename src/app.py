"""
Chela Suppliers Management System
Main Streamlit Application
Created: December 21, 2025
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from models import (
    get_db, Supplier, Invoice, InvoiceItem, Product, PriceHistory, DashboardNotes, init_db
)
from sqlalchemy import func
from PIL import Image
import pillow_heif
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Initialize database tables (create if not exists)
init_db()

# Register HEIF opener to enable HEIC support
pillow_heif.register_heif_opener()

# Page configuration
st.set_page_config(
    page_title="Chela Suppliers",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E4057;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #048A81;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .stat-card {
        background-color: #F8F9FA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #048A81;
    }
    .success-box {
        padding: 1rem;
        background-color: #D4EDDA;
        border-left: 4px solid #28A745;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #F8D7DA;
        border-left: 4px solid #DC3545;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_stats():
    """Get dashboard statistics"""
    db = next(get_db())
    try:
        total_suppliers = db.query(Supplier).filter(Supplier.is_active == True).count()
        total_invoices = db.query(Invoice).count()

        return {
            'total_suppliers': total_suppliers,
            'total_invoices': total_invoices
        }
    finally:
        db.close()


def format_currency(amount):
    """Format amount as IDR currency"""
    return f"Rp {amount:,.0f}"


def calculate_due_date(invoice_date, payment_terms):
    """Calculate due date based on payment terms

    Args:
        invoice_date: Date object of the invoice
        payment_terms: 'cash', '2week', or 'monthly'

    Returns:
        Date object for the due date
    """
    from calendar import monthrange

    if payment_terms == 'cash':
        return invoice_date

    elif payment_terms == '2week':
        # Month split in half: pay on 15th and end of month
        # If invoice before 15th -> due on 15th
        # If invoice on or after 15th -> due end of month
        if invoice_date.day < 15:
            return date(invoice_date.year, invoice_date.month, 15)
        else:
            # Last day of the month
            last_day = monthrange(invoice_date.year, invoice_date.month)[1]
            return date(invoice_date.year, invoice_date.month, last_day)

    else:  # monthly
        # All orders from that month -> pay at end of month
        last_day = monthrange(invoice_date.year, invoice_date.month)[1]
        return date(invoice_date.year, invoice_date.month, last_day)


def format_date_input(date_obj):
    """Format date as DD/MM/YYYY for display"""
    if date_obj:
        return date_obj.strftime('%d/%m/%Y')
    return ""


def generate_payment_schedule_pdf(report_data, month_name, cycle_name, total_amount, review_count, category_filter):
    """Generate PDF for payment schedule report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2C1810'),
        spaceAfter=30,
        alignment=1  # Center
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#5D4037'),
        spaceAfter=20,
        alignment=1  # Center
    )

    # Title
    title = Paragraph("CHELA<br/>Payment Summary", title_style)
    elements.append(title)

    # Subtitle with filters
    category_text = f" - {category_filter}" if category_filter != "All" else ""
    subtitle = Paragraph(f"{month_name} - {cycle_name}{category_text}", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3 * inch))

    # Table data - group by category if "All" selected
    if category_filter == "All":
        # Group by category
        from collections import defaultdict
        categories = defaultdict(list)
        for row in report_data:
            categories[row.get('Category', 'Other')].append(row)

        # Create table for each category
        for category_name in sorted(categories.keys()):
            category_rows = categories[category_name]

            # Category header
            category_header = Paragraph(f"<b>{category_name}</b>", subtitle_style)
            elements.append(category_header)
            elements.append(Spacer(1, 0.1 * inch))

            # Table data for this category
            table_data = [['Supplier', 'Payment Terms', 'Total Amount']]
            category_subtotal = 0

            for row in category_rows:
                table_data.append([
                    row['Supplier'],
                    row['Payment Terms'],
                    row['Total Amount']
                ])
                category_subtotal += row.get('Total_Raw', 0)

            # Add subtotal row
            table_data.append([
                'Subtotal',
                '',
                format_currency(category_subtotal)
            ])

            # Create table
            table = Table(table_data, colWidths=[3*inch, 2*inch, 2*inch])
            subtotal_row_idx = len(table_data) - 1

            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5D4037')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),

                # Data rows styling
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.beige]),
                ('TOPPADDING', (0, 1), (-1, -2), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 8),

                # Subtotal row styling
                ('BACKGROUND', (0, subtotal_row_idx), (-1, subtotal_row_idx), colors.HexColor('#E0E0E0')),
                ('FONTNAME', (0, subtotal_row_idx), (-1, subtotal_row_idx), 'Helvetica-Bold'),
                ('FONTSIZE', (0, subtotal_row_idx), (-1, subtotal_row_idx), 11),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 0.3 * inch))

    else:
        # Single category - no grouping needed
        table_data = [['Supplier', 'Payment Terms', 'Total Amount']]
        for row in report_data:
            table_data.append([
                row['Supplier'],
                row['Payment Terms'],
                row['Total Amount']
            ])

        # Create table
        table = Table(table_data, colWidths=[3*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5D4037')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige]),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5 * inch))

    # Summary section
    summary_data = [
        ['Total Payment Amount', format_currency(total_amount)]
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2E4057')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(summary_table)

    # Footer
    elements.append(Spacer(1, 0.5 * inch))
    footer_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %H:%M')}"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def parse_invoice_ocr(text, suppliers_list):
    """
    Multi-strategy OCR parser - tries different approaches to extract invoice data

    Returns dict with:
    - supplier_name: matched supplier or None
    - invoice_date: parsed date or None
    - total_amount: parsed amount or 0
    - line_items: list of {name, quantity, unit, unit_price}
    """
    import re
    from datetime import datetime

    result = {
        'supplier_name': None,
        'invoice_date': None,
        'total_amount': 0,
        'line_items': []
    }

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text_upper = text.upper()

    # ============================================================================
    # 1. FIND SUPPLIER - Multiple strategies
    # ============================================================================

    # Strategy A: Scan entire document for supplier match
    for supplier in suppliers_list:
        # Check short name
        if supplier.short_name.upper() in text_upper:
            result['supplier_name'] = supplier.short_name
            break
        # Check company name
        if supplier.company_name.upper() in text_upper:
            result['supplier_name'] = supplier.short_name
            break
        # Fuzzy match - check if 60% of words match (lower threshold for flexibility)
        supplier_words = supplier.short_name.upper().split()
        if len(supplier_words) > 0:
            matches = sum(1 for word in supplier_words if word in text_upper)
            if matches / len(supplier_words) >= 0.6:
                result['supplier_name'] = supplier.short_name
                break

    # ============================================================================
    # 2. FIND DATE - Look for DD/MM/YYYY patterns
    # ============================================================================

    date_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # DD/MM/YYYY
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b',  # DD/MM/YY
    ]

    for line in lines:
        # Skip lines with ACCOUNT or BANK to avoid false positives
        if any(word in line.upper() for word in ['ACCOUNT', 'REKENING', 'NO:', 'NO.', 'HP', 'PHONE', 'TELP']):
            continue

        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    day, month, year = match.groups()
                    if len(year) == 2:
                        year = '20' + year
                    parsed_date = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").date()
                    # Sanity check - date should be reasonable (not in far future/past)
                    year_int = int(year)
                    if 2020 <= year_int <= 2030:
                        result['invoice_date'] = parsed_date
                        break
                except:
                    continue
        if result['invoice_date']:
            break

    # ============================================================================
    # 3. FIND TOTAL AMOUNT - Multiple strategies
    # ============================================================================

    candidate_amounts = []

    for i, line in enumerate(lines):
        line_upper = line.upper()

        # Strategy A: Lines with TOTAL keywords (highest priority)
        total_keywords = ['TOTAL AMOUNT', 'GRAND TOTAL', 'TOTAL:', 'JUMLAH', 'AMOUNT DUE']
        has_total_keyword = any(keyword in line_upper for keyword in total_keywords)

        # Skip lines with account/bank/phone (these have wrong numbers)
        skip_keywords = ['ACCOUNT', 'REKENING', 'BANK', 'NO.', 'NO:', 'HP', 'PHONE', 'TELP', 'FAX']
        has_skip_keyword = any(keyword in line_upper for keyword in skip_keywords)

        if has_skip_keyword:
            continue

        # Extract all numbers from line
        numbers = re.findall(r'[\d.,]+', line)

        for num_str in numbers:
            try:
                # Clean the number (remove dots as thousand separators, keep as integer)
                clean = num_str.replace('.', '').replace(',', '').replace('Rp', '').strip()
                if not clean.isdigit():
                    continue

                amount = int(clean)

                # Filter by reasonable ranges
                # Too small: probably item quantity or small price
                # Too large: probably account number (usually 10+ digits)
                if amount < 5000:  # Too small
                    continue
                if amount > 999999999:  # Account numbers (10+ digits)
                    continue

                # Calculate priority
                priority = 0

                # Boost priority for total keywords
                if has_total_keyword:
                    priority += 100

                # Boost priority for amounts in last 30% of document
                if i > len(lines) * 0.7:
                    priority += 50

                # Boost priority for larger amounts (usually total > line items)
                if amount > 100000:
                    priority += 10

                candidate_amounts.append((amount, priority))

            except:
                continue

    # Pick highest priority amount
    if candidate_amounts:
        candidate_amounts.sort(key=lambda x: x[1], reverse=True)
        result['total_amount'] = candidate_amounts[0][0]

    # ============================================================================
    # 4. FIND LINE ITEMS - Flexible table detection
    # ============================================================================

    in_items_section = False

    for i, line in enumerate(lines):
        line_upper = line.upper()

        # Start detecting items after table headers
        header_keywords = ['DESCRIPTION', 'ITEM', 'PRODUCT', 'QTY', 'QUANTITY', 'NO.']
        if any(keyword in line_upper for keyword in header_keywords):
            in_items_section = True
            continue

        # Stop at total/subtotal lines
        stop_keywords = ['TOTAL', 'SUBTOTAL', 'SUB TOTAL', 'JUMLAH', 'THANK YOU', 'BANK']
        if any(keyword in line_upper for keyword in stop_keywords):
            in_items_section = False
            continue

        # Look for lines with numbers (potential items)
        numbers = re.findall(r'\d+[.,]?\d*', line)

        # Need at least 2 numbers (quantity + price, or price + total)
        if len(numbers) >= 2:
            # Extract product name (text part after removing numbers)
            product_name = line
            for num in numbers:
                product_name = product_name.replace(num, '')
            # Clean up product name
            product_name = re.sub(r'[.,]', '', product_name).strip()

            # Skip if product name is too short or contains junk
            if len(product_name) < 3:
                continue
            if any(word in product_name.upper() for word in ['NO', 'QTY', 'PRICE', 'TOTAL']):
                continue

            try:
                # Parse numbers
                qty = float(numbers[0].replace(',', '.'))

                # Unit price is usually second number or second-to-last
                if len(numbers) >= 3:
                    unit_price = float(numbers[1].replace('.', '').replace(',', ''))
                else:
                    unit_price = float(numbers[-1].replace('.', '').replace(',', ''))

                # Sanity checks
                if qty <= 0 or qty > 10000:  # Unreasonable quantity
                    continue
                if unit_price <= 0 or unit_price > 10000000:  # Unreasonable price
                    continue

                # Detect unit
                unit = 'pcs'
                units_map = {
                    'KG': 'kg', 'KILO': 'kg', 'KILOGRAM': 'kg',
                    'GRAM': 'g', 'GR': 'g',
                    'LITER': 'liter', 'L': 'liter', 'LTR': 'liter',
                    'ML': 'ml', 'MILI': 'ml',
                    'PCS': 'pcs', 'PC': 'pcs', 'PIECE': 'pcs',
                    'PACK': 'pack', 'PAK': 'pack',
                    'BOX': 'box', 'KOTAK': 'box',
                    'BOTTLE': 'bottle', 'BTL': 'bottle',
                    'CAN': 'can', 'KALENG': 'can'
                }

                for unit_keyword, unit_value in units_map.items():
                    if unit_keyword in line_upper:
                        unit = unit_value
                        break

                result['line_items'].append({
                    'name': product_name[:50],
                    'quantity': qty,
                    'unit': unit,
                    'unit_price': unit_price
                })

            except:
                continue

    return result


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def show_dashboard():
    """Dashboard - Overview of suppliers and invoices"""
    st.markdown('<p class="main-header">📦 Chela Suppliers Dashboard</p>', unsafe_allow_html=True)

    # Get statistics
    stats = get_stats()

    # Display stats in columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric("Active Suppliers", stats['total_suppliers'])
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric("Total Invoices", stats['total_invoices'])
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Recent invoices
    st.markdown('<p class="sub-header">Recent Invoices</p>', unsafe_allow_html=True)

    db = next(get_db())
    try:
        recent_invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(10).all()

        if recent_invoices:
            invoice_data = []
            for inv in recent_invoices:
                invoice_data.append({
                    'Date Entered': inv.created_at.strftime('%d/%m/%Y %H:%M'),
                    'Supplier': inv.supplier.short_name,
                    'Invoice #': inv.invoice_number or '-',
                    'Invoice Date': inv.invoice_date.strftime('%d/%m/%Y'),
                    'Amount': format_currency(inv.total_amount),
                    'Due Date': inv.due_date.strftime('%d/%m/%Y') if inv.due_date else '-'
                })

            df = pd.DataFrame(invoice_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No invoices yet. Start by adding a supplier and creating an invoice!")
    finally:
        db.close()

    st.markdown("---")

    # Dashboard Notes (shared scratchpad)
    st.markdown('<p class="sub-header">📝 Work Notes</p>', unsafe_allow_html=True)
    st.caption("Shared scratchpad for Diego and Astik - track TODOs, reminders, etc.")

    db = next(get_db())
    try:
        # Get or create notes record
        notes_record = db.query(DashboardNotes).first()
        if not notes_record:
            notes_record = DashboardNotes(notes="")
            db.add(notes_record)
            db.commit()

        current_notes = notes_record.notes or ""

        # Text area for notes
        new_notes = st.text_area(
            "Notes",
            value=current_notes,
            height=150,
            key="dashboard_notes",
            placeholder="Write your work notes here... (e.g., 'Call Supplier X tomorrow', 'Check prices next week')",
            label_visibility="collapsed"
        )

        # Save button
        if st.button("💾 Save Notes", use_container_width=True):
            notes_record.notes = new_notes
            notes_record.updated_at = datetime.now()
            db.commit()
            st.success("✅ Notes saved!")
            st.rerun()

        # Show last update time
        if notes_record.updated_at:
            st.caption(f"Last updated: {notes_record.updated_at.strftime('%d/%m/%Y %H:%M')}")

    finally:
        db.close()


def show_suppliers():
    """Suppliers page - View and manage suppliers"""
    st.markdown('<p class="main-header">👥 Suppliers</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["View Suppliers", "Add Supplier", "Edit Supplier"])

    with tab1:
        st.markdown('<p class="sub-header">Active Suppliers</p>', unsafe_allow_html=True)

        db = next(get_db())
        try:
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()

            if suppliers:
                supplier_data = []
                for sup in suppliers:
                    supplier_data.append({
                        'Short Name': sup.short_name,
                        'Category': sup.category or '-',
                        'Payment Terms': sup.payment_terms.upper(),
                        'Delivery Days': sup.delivery_days or '-',
                        'PPN Handling': sup.ppn_handling.capitalize()
                    })

                df = pd.DataFrame(supplier_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No suppliers yet. Add your first supplier in the 'Add Supplier' tab!")
        finally:
            db.close()

    with tab2:
        st.markdown('<p class="sub-header">Add New Supplier</p>', unsafe_allow_html=True)

        with st.form("add_supplier_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                short_name = st.text_input("Short Name *", placeholder="e.g., Chela (what you call them)")
                company_name = st.text_input("Company Name *", placeholder="e.g., PT KOPI BAR SELA (official/legal)")
                category = st.selectbox("Category *", ["Food", "Drinks", "Operational"])
                contact_person = st.text_input("Contact Person", placeholder="e.g., Made Wirawan")
                order_phone = st.text_input("Order Phone", placeholder="e.g., 812 3456 7890")
                admin_phone = st.text_input("Admin Phone", placeholder="e.g., 812 9876 5432")
                email = st.text_input("Email", placeholder="e.g., supplier@example.com")

            with col2:
                payment_terms = st.selectbox("Payment Terms *", ["cash", "2week", "monthly"])
                ppn_handling = st.selectbox(
                    "PPN (Tax) Handling *",
                    ["included", "added"],
                    help="'Included' = final price shown in invoice | 'Added' = subtotal + PPN at bottom"
                )

                # Delivery days selector
                st.markdown("**Delivery Days**")
                col_days = st.columns(7)
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                selected_days = []
                for i, day in enumerate(days):
                    with col_days[i]:
                        if st.checkbox(day, key=f"day_{day}"):
                            selected_days.append(day)

                bank_name = st.text_input("Bank Name", placeholder="e.g., BCA")
                bank_account_number = st.text_input("Account Number", placeholder="e.g., 1234567890")
                bank_account_name = st.text_input("Account Name", placeholder="e.g., PT. Supplier Name")

            notes = st.text_area("Notes", placeholder="Any additional notes")

            submitted = st.form_submit_button("Add Supplier", use_container_width=True)

            if submitted:
                if not short_name or not company_name:
                    st.error("Short name and company name are required!")
                else:
                    db = next(get_db())
                    try:
                        # Check for duplicate names
                        existing_short = db.query(Supplier).filter(
                            Supplier.short_name == short_name,
                            Supplier.is_active == True
                        ).first()
                        existing_company = db.query(Supplier).filter(
                            Supplier.company_name == company_name,
                            Supplier.is_active == True
                        ).first()

                        if existing_short:
                            st.error(f"❌ Supplier with short name '{short_name}' already exists!")
                        elif existing_company:
                            st.error(f"❌ Supplier with company name '{company_name}' already exists!")
                        else:
                            delivery_days_str = ", ".join(selected_days) if selected_days else None

                            new_supplier = Supplier(
                                short_name=short_name,
                                company_name=company_name,
                                category=category,
                                contact_person=contact_person or None,
                                order_phone=order_phone or None,
                                admin_phone=admin_phone or None,
                                email=email or None,
                                payment_terms=payment_terms,
                                ppn_handling=ppn_handling,
                                delivery_days=delivery_days_str,
                                bank_name=bank_name or None,
                                bank_account_number=bank_account_number or None,
                                bank_account_name=bank_account_name or None,
                                notes=notes or None
                            )
                            db.add(new_supplier)
                            db.commit()
                            st.success(f"✅ Supplier '{short_name}' ({company_name}) added successfully!")
                            st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error adding supplier: {str(e)}")
                    finally:
                        db.close()

    with tab3:
        st.markdown('<p class="sub-header">Edit Supplier</p>', unsafe_allow_html=True)

        # Get all suppliers for dropdown
        db = next(get_db())
        suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
        db.close()

        if not suppliers:
            st.info("No suppliers to edit. Add a supplier first!")
        else:
            # Select supplier to edit
            supplier_options = [f"{s.short_name} ({s.company_name})" for s in suppliers]

            st.info("💡 **Tip:** Click the dropdown and start typing to search (e.g., type supplier name)")

            selected_option = st.selectbox(
                f"Select supplier to edit ({len(suppliers)} total)",
                supplier_options
            )

            # Get the selected supplier
            selected_index = supplier_options.index(selected_option)
            supplier_to_edit = suppliers[selected_index]

            st.markdown("---")

            with st.form("edit_supplier_form"):
                col1, col2 = st.columns(2)

                with col1:
                    short_name = st.text_input("Short Name *", value=supplier_to_edit.short_name)
                    company_name = st.text_input("Company Name *", value=supplier_to_edit.company_name)
                    category = st.selectbox(
                        "Category *",
                        ["Food", "Drinks", "Operational"],
                        index=["Food", "Drinks", "Operational"].index(supplier_to_edit.category) if supplier_to_edit.category else 0
                    )
                    contact_person = st.text_input("Contact Person", value=supplier_to_edit.contact_person or "")
                    order_phone = st.text_input("Order Phone", value=supplier_to_edit.order_phone or "")
                    admin_phone = st.text_input("Admin Phone", value=supplier_to_edit.admin_phone or "")
                    email = st.text_input("Email", value=supplier_to_edit.email or "")

                with col2:
                    payment_terms = st.selectbox(
                        "Payment Terms *",
                        ["cash", "2week", "monthly"],
                        index=["cash", "2week", "monthly"].index(supplier_to_edit.payment_terms)
                    )
                    ppn_handling = st.selectbox(
                        "PPN (Tax) Handling *",
                        ["included", "added"],
                        index=["included", "added"].index(supplier_to_edit.ppn_handling) if supplier_to_edit.ppn_handling else 0,
                        help="'Included' = final price shown in invoice | 'Added' = subtotal + PPN at bottom"
                    )

                    # Delivery days selector
                    st.markdown("**Delivery Days**")
                    existing_days = supplier_to_edit.delivery_days.split(", ") if supplier_to_edit.delivery_days else []
                    col_days = st.columns(7)
                    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    selected_days = []
                    for i, day in enumerate(days):
                        with col_days[i]:
                            if st.checkbox(day, key=f"edit_day_{day}", value=(day in existing_days)):
                                selected_days.append(day)

                    bank_name = st.text_input("Bank Name", value=supplier_to_edit.bank_name or "")
                    bank_account_number = st.text_input("Account Number", value=supplier_to_edit.bank_account_number or "")
                    bank_account_name = st.text_input("Account Name", value=supplier_to_edit.bank_account_name or "")

                notes = st.text_area("Notes", value=supplier_to_edit.notes or "")

                col_buttons = st.columns([3, 1])
                with col_buttons[0]:
                    submitted = st.form_submit_button("Update Supplier", use_container_width=True)
                with col_buttons[1]:
                    deactivate = st.form_submit_button("Deactivate", use_container_width=True, type="secondary")

                if submitted:
                    if not short_name or not company_name:
                        st.error("Short name and company name are required!")
                    else:
                        db = next(get_db())
                        try:
                            delivery_days_str = ", ".join(selected_days) if selected_days else None

                            # Update supplier
                            supplier = db.query(Supplier).filter(Supplier.id == supplier_to_edit.id).first()
                            supplier.short_name = short_name
                            supplier.company_name = company_name
                            supplier.category = category
                            supplier.contact_person = contact_person or None
                            supplier.order_phone = order_phone or None
                            supplier.admin_phone = admin_phone or None
                            supplier.email = email or None
                            supplier.payment_terms = payment_terms
                            supplier.ppn_handling = ppn_handling
                            supplier.delivery_days = delivery_days_str
                            supplier.bank_name = bank_name or None
                            supplier.bank_account_number = bank_account_number or None
                            supplier.bank_account_name = bank_account_name or None
                            supplier.notes = notes or None

                            db.commit()
                            st.success(f"✅ Supplier '{short_name}' updated successfully!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Error updating supplier: {str(e)}")
                        finally:
                            db.close()

                if deactivate:
                    db = next(get_db())
                    try:
                        supplier = db.query(Supplier).filter(Supplier.id == supplier_to_edit.id).first()
                        supplier.is_active = False
                        db.commit()
                        st.success(f"✅ Supplier '{supplier_to_edit.short_name}' deactivated!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error deactivating supplier: {str(e)}")
                    finally:
                        db.close()


def show_market_list():
    """Market List page - Manage products catalog"""
    st.markdown('<p class="main-header">🛒 Market List</p>', unsafe_allow_html=True)
    st.markdown("Manage your product catalog - all products you regularly order from suppliers")

    tab1, tab2, tab3 = st.tabs(["Market List", "Add Product", "Edit Product"])

    # TAB 1: VIEW PRODUCTS
    with tab1:
        st.markdown("### 📋 Market List")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input(
                "🔍 Search products",
                placeholder="Type to filter (e.g., 'tom' for tomatoes)...",
                key="product_search"
            )
        with col2:
            category_filter = st.selectbox(
                "Filter by category",
                ["All", "Food", "Drinks", "Operational"],
                key="product_category_filter"
            )
        with col3:
            # Get suppliers for filter
            db_temp = next(get_db())
            suppliers = db_temp.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
            supplier_names = ["All"] + [s.short_name for s in suppliers]
            db_temp.close()

            supplier_filter = st.selectbox(
                "Filter by supplier",
                supplier_names,
                key="product_supplier_filter"
            )

        # Get products
        db = next(get_db())
        try:
            query = db.query(Product).join(
                Supplier, Product.preferred_supplier_id == Supplier.id, isouter=True
            )

            if search_term:
                query = query.filter(Product.name.ilike(f"%{search_term}%"))

            if category_filter != "All":
                query = query.filter(Product.category == category_filter)

            if supplier_filter != "All":
                query = query.filter(Supplier.short_name == supplier_filter)

            products = query.order_by(Product.category, Product.name).all()

            if products:
                product_data = []
                for prod in products:
                    # Add backup indicator to product name
                    product_name = prod.name
                    if prod.is_backup:
                        product_name = f"🔄 {prod.name}"

                    # Determine measurement unit
                    measurement_unit = '-'
                    if prod.unit == 'kg':
                        measurement_unit = 'g'
                    elif prod.unit == 'liter':
                        measurement_unit = 'ml'
                    elif prod.unit == 'gram':
                        measurement_unit = 'g'
                    elif prod.unit == 'ml':
                        measurement_unit = 'ml'
                    elif prod.unit in ['pcs', 'bottle', 'box', 'ctn', 'pack']:
                        # Use unit_size_measurement if set
                        if prod.unit_size_measurement:
                            measurement_unit = prod.unit_size_measurement

                    product_data.append({
                        'Product Name': product_name,
                        'Category': prod.category or '-',
                        'Unit': prod.unit,
                        'Measurement Unit': measurement_unit,
                        'Current Price': format_currency(prod.current_price) if prod.current_price else '-',
                        'Supplier': prod.preferred_supplier.short_name if prod.preferred_supplier else '-',
                        'Notes': prod.notes[:30] + '...' if prod.notes and len(prod.notes) > 30 else (prod.notes or '-')
                    })

                df = pd.DataFrame(product_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                backup_count = sum(1 for p in products if p.is_backup)
                if backup_count > 0:
                    st.caption(f"📦 Total products: {len(products)} ({backup_count} backup)")
                else:
                    st.caption(f"📦 Total products: {len(products)}")
            else:
                st.info("No products found. Add your first product in the 'Add Product' tab!")
        finally:
            db.close()

    # TAB 2: ADD PRODUCT
    with tab2:
        st.markdown("### ➕ Add New Product")
        st.markdown("Add a product to your market list")

        with st.form("add_product_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                product_name = st.text_input("Product Name *", key="new_product_name")
                category = st.selectbox(
                    "Category *",
                    ["Food", "Drinks", "Operational"],
                    key="new_product_category"
                )
                unit = st.selectbox(
                    "Unit *",
                    ["kg", "gram", "liter", "ml", "pcs", "box", "ctn", "pack", "bottle"],
                    key="new_product_unit"
                )

                # Unit size fields (only for non-exact units)
                st.markdown("**📏 Unit Size** (only for pcs/bottle/box/ctn/pack)")
                col_size1, col_size2 = st.columns(2)
                with col_size1:
                    unit_size = st.number_input(
                        "Size",
                        min_value=0.0,
                        step=1.0,
                        key="new_product_unit_size",
                        help="How much does 1 unit contain? E.g., 1 bottle = 1000"
                    )
                with col_size2:
                    unit_size_measurement = st.selectbox(
                        "Measurement",
                        ["", "g", "ml"],
                        key="new_product_unit_size_measurement",
                        help="E.g., 1 bottle = 1000ml → select 'ml'"
                    )

            with col2:
                # Get active suppliers for dropdown
                db = next(get_db())
                suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
                db.close()

                supplier_options = {s.short_name: s.id for s in suppliers}

                if supplier_options:
                    selected_supplier = st.selectbox(
                        "Supplier *",
                        options=list(supplier_options.keys()),
                        key="new_product_supplier"
                    )
                else:
                    st.warning("⚠️ No active suppliers found. Please add a supplier first.")
                    selected_supplier = None

                st.info("💡 **Price Tracking:** Prices are automatically recorded from invoices (with dates). No manual entry needed!")

                is_backup = st.checkbox(
                    "🔄 Mark as backup supplier",
                    value=False,
                    help="Check this if this is a backup/temporary supplier (e.g., when primary supplier is out of stock)",
                    key="new_product_is_backup"
                )

                notes = st.text_area("Notes", key="new_product_notes")

            submitted = st.form_submit_button("💾 Add Product", use_container_width=True)

            if submitted:
                if not product_name:
                    st.error("❌ Product name is required")
                elif not selected_supplier:
                    st.error("❌ Please add a supplier first")
                else:
                    try:
                        db = next(get_db())

                        # Check if product already exists
                        existing = db.query(Product).filter(Product.name == product_name).first()
                        if existing:
                            st.error(f"❌ Product '{product_name}' already exists!")
                        else:
                            # Only save unit size for non-exact units
                            save_unit_size = None
                            save_unit_size_measurement = None
                            if unit in ['pcs', 'box', 'ctn', 'pack', 'bottle']:
                                if unit_size > 0 and unit_size_measurement:
                                    save_unit_size = unit_size
                                    save_unit_size_measurement = unit_size_measurement

                            new_product = Product(
                                name=product_name,
                                category=category,
                                unit=unit,
                                current_price=None,  # Price will be set from first invoice
                                current_price_date=None,
                                preferred_supplier_id=supplier_options[selected_supplier],
                                is_backup=is_backup,
                                unit_size=save_unit_size,
                                unit_size_measurement=save_unit_size_measurement,
                                notes=notes if notes else None
                            )

                            db.add(new_product)
                            db.commit()

                            backup_msg = " (marked as backup)" if is_backup else ""
                            size_msg = f" ({unit_size}{unit_size_measurement} per {unit})" if save_unit_size else ""
                            st.success(f"✅ Product '{product_name}' added successfully{backup_msg}{size_msg}! Price will be recorded from invoices.")
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error adding product: {str(e)}")
                    finally:
                        db.close()

    # TAB 3: EDIT PRODUCT
    with tab3:
        st.markdown("### ✏️ Edit Product")

        # Get all products
        db = next(get_db())
        from sqlalchemy.orm import joinedload
        products = db.query(Product).options(joinedload(Product.preferred_supplier)).order_by(Product.name).all()

        # Build options before closing db
        product_options = {
            f"{p.name} ({p.preferred_supplier.short_name if p.preferred_supplier else 'No supplier'})": p.id
            for p in products
        }
        db.close()

        if not products:
            st.info("No products to edit. Add products first!")
        else:

            st.info("💡 **Tip:** Click the dropdown and start typing to search (e.g., type 'tom' to find tomatoes)")

            selected_product_key = st.selectbox(
                f"Select product to edit ({len(products)} total)",
                options=list(product_options.keys()),
                key="edit_product_select"
            )

            if selected_product_key:
                product_id = product_options[selected_product_key]

                db = next(get_db())
                product = db.query(Product).filter(Product.id == product_id).first()
                db.close()

                if product:
                    with st.form("edit_product_form"):
                        col1, col2 = st.columns(2)

                        with col1:
                            edit_name = st.text_input("Product Name *", value=product.name)
                            edit_category = st.selectbox(
                                "Category *",
                                ["Food", "Drinks", "Operational"],
                                index=["Food", "Drinks", "Operational"].index(product.category) if product.category in ["Food", "Drinks", "Operational"] else 0
                            )
                            edit_unit = st.selectbox(
                                "Unit *",
                                ["kg", "gram", "liter", "ml", "pcs", "box", "ctn", "pack", "bottle"],
                                index=["kg", "gram", "liter", "ml", "pcs", "box", "ctn", "pack", "bottle"].index(product.unit) if product.unit in ["kg", "gram", "liter", "ml", "pcs", "box", "ctn", "pack", "bottle"] else 0
                            )

                            # Unit size fields (only for non-exact units)
                            st.markdown("**📏 Unit Size** (only for pcs/bottle/box/ctn/pack)")
                            col_size1, col_size2 = st.columns(2)
                            with col_size1:
                                edit_unit_size = st.number_input(
                                    "Size",
                                    min_value=0.0,
                                    step=1.0,
                                    value=float(product.unit_size) if product.unit_size else 0.0,
                                    key="edit_product_unit_size",
                                    help="How much does 1 unit contain? E.g., 1 bottle = 1000"
                                )
                            with col_size2:
                                current_measurement_index = 0
                                if product.unit_size_measurement:
                                    measurement_options = ["", "g", "ml"]
                                    if product.unit_size_measurement in measurement_options:
                                        current_measurement_index = measurement_options.index(product.unit_size_measurement)

                                edit_unit_size_measurement = st.selectbox(
                                    "Measurement",
                                    ["", "g", "ml"],
                                    index=current_measurement_index,
                                    key="edit_product_unit_size_measurement",
                                    help="E.g., 1 bottle = 1000ml → select 'ml'"
                                )

                        with col2:
                            # Get suppliers
                            db = next(get_db())
                            suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
                            db.close()

                            supplier_options = {s.short_name: s.id for s in suppliers}
                            current_supplier = next((s.short_name for s in suppliers if s.id == product.preferred_supplier_id), None)

                            edit_supplier = st.selectbox(
                                "Supplier *",
                                options=list(supplier_options.keys()),
                                index=list(supplier_options.keys()).index(current_supplier) if current_supplier else 0
                            )

                            # Show current price as read-only info
                            if product.current_price:
                                price_info = f"{format_currency(product.current_price)}"
                                if product.current_price_date:
                                    price_info += f" (from invoice on {product.current_price_date.strftime('%d/%m/%Y')})"
                                st.info(f"💰 **Current Price:** {price_info}")
                            else:
                                st.info("💰 **Current Price:** Not set yet (will be recorded from first invoice)")

                            edit_is_backup = st.checkbox(
                                "🔄 Mark as backup supplier",
                                value=bool(product.is_backup),
                                help="Check this if this is a backup/temporary supplier (e.g., when primary supplier is out of stock)",
                                key="edit_product_is_backup"
                            )

                            edit_notes = st.text_area("Notes", value=product.notes if product.notes else "")

                        col1, col2 = st.columns(2)
                        with col1:
                            update_submitted = st.form_submit_button("💾 Update Product", use_container_width=True)
                        with col2:
                            delete_submitted = st.form_submit_button("🗑️ Delete Product", use_container_width=True)

                        if update_submitted:
                            if not edit_name:
                                st.error("❌ Product name is required")
                            else:
                                try:
                                    db = next(get_db())

                                    # Fetch the product in this session
                                    product_to_update = db.query(Product).filter(Product.id == product.id).first()

                                    # Check if new name conflicts with existing product
                                    if edit_name != product_to_update.name:
                                        existing = db.query(Product).filter(Product.name == edit_name).first()
                                        if existing:
                                            st.error(f"❌ Product '{edit_name}' already exists!")
                                            db.close()
                                            return

                                    # Update the product
                                    product_to_update.name = edit_name
                                    product_to_update.category = edit_category
                                    product_to_update.unit = edit_unit
                                    product_to_update.preferred_supplier_id = supplier_options[edit_supplier]
                                    product_to_update.is_backup = edit_is_backup
                                    # current_price and current_price_date are NOT updated here - only from invoices
                                    product_to_update.notes = edit_notes if edit_notes else None

                                    # Only save unit size for non-exact units
                                    if edit_unit in ['pcs', 'box', 'ctn', 'pack', 'bottle']:
                                        if edit_unit_size > 0 and edit_unit_size_measurement:
                                            product_to_update.unit_size = edit_unit_size
                                            product_to_update.unit_size_measurement = edit_unit_size_measurement
                                        else:
                                            product_to_update.unit_size = None
                                            product_to_update.unit_size_measurement = None
                                    else:
                                        # For exact units (kg, gram, liter, ml), clear unit size
                                        product_to_update.unit_size = None
                                        product_to_update.unit_size_measurement = None

                                    product_to_update.updated_at = datetime.now()

                                    db.commit()
                                    backup_msg = " (marked as backup)" if edit_is_backup else ""
                                    size_msg = f" ({edit_unit_size}{edit_unit_size_measurement} per {edit_unit})" if product_to_update.unit_size else ""
                                    st.success(f"✅ Product '{edit_name}' updated successfully{backup_msg}{size_msg}!")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"❌ Error updating product: {str(e)}")
                                finally:
                                    db.close()

                        if delete_submitted:
                            try:
                                db = next(get_db())

                                # Check what will be deleted
                                invoice_items_count = db.query(InvoiceItem).filter(
                                    InvoiceItem.product_id == product.id
                                ).count()

                                price_history_count = db.query(PriceHistory).filter(
                                    PriceHistory.product_id == product.id
                                ).count()

                                # Show warning but ALLOW deletion (you're the boss!)
                                warnings = []
                                if invoice_items_count > 0:
                                    warnings.append(f"⚠️ Used in {invoice_items_count} invoice(s)")
                                if price_history_count > 0:
                                    warnings.append(f"⚠️ Has {price_history_count} price history record(s)")

                                if warnings:
                                    st.warning("**Deleting this product will:**\n" + "\n".join(warnings))
                                    st.info("💡 Price history will be deleted. Invoice items will remain but product link will be removed.")

                                # Delete price history first
                                if price_history_count > 0:
                                    db.query(PriceHistory).filter(PriceHistory.product_id == product.id).delete()

                                # Update invoice items to NULL product_id (keep the record but remove link)
                                if invoice_items_count > 0:
                                    db.query(InvoiceItem).filter(InvoiceItem.product_id == product.id).update(
                                        {"product_id": None}
                                    )

                                # Now delete the product
                                db.delete(product)
                                db.commit()
                                st.success(f"✅ Product '{product.name}' deleted successfully!")
                                st.rerun()

                            except Exception as e:
                                db.rollback()
                                st.error(f"❌ Error deleting product: {str(e)}")
                            finally:
                                db.close()


def show_invoices():
    """Invoices page - View and add invoices"""
    st.markdown('<p class="main-header">🧾 Invoices</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["View Invoices", "Add Invoice", "Edit/Delete Invoice"])

    with tab1:
        st.markdown('<p class="sub-header">All Invoices</p>', unsafe_allow_html=True)

        # Filters
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            # Supplier filter
            db_temp = next(get_db())
            suppliers = db_temp.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
            supplier_names = ["All"] + [s.short_name for s in suppliers]
            db_temp.close()
            filter_supplier = st.selectbox("Supplier", supplier_names, key="invoice_filter_supplier")

        with col2:
            # Category filter
            categories = ["All", "Food", "Drinks", "Operational"]
            filter_category = st.selectbox("Category", categories, key="invoice_filter_category")

        with col3:
            # Year filter
            current_year = date.today().year
            years = ["All"] + [current_year - 1, current_year, current_year + 1]
            filter_year = st.selectbox("Year", years, key="invoice_filter_year")

        with col4:
            # Month filter
            months = ["All"] + list(range(1, 13))
            filter_month = st.selectbox(
                "Month",
                months,
                format_func=lambda x: x if x == "All" else date(2025, x, 1).strftime('%B'),
                key="invoice_filter_month"
            )

        with col5:
            # Payment cycle filter
            filter_payment_cycle = st.selectbox(
                "Payment Cycle",
                ["All", "Cash", "2-week", "Monthly"],
                key="invoice_filter_payment_cycle"
            )

        # Get invoices
        db = next(get_db())
        try:
            from sqlalchemy import extract
            from sqlalchemy.orm import joinedload

            query = db.query(Invoice).options(joinedload(Invoice.supplier))

            # Apply supplier filter
            if filter_supplier != "All":
                supplier = db.query(Supplier).filter(Supplier.short_name == filter_supplier).first()
                if supplier:
                    query = query.filter(Invoice.supplier_id == supplier.id)

            # Apply category filter
            if filter_category != "All":
                query = query.join(Supplier).filter(Supplier.category == filter_category)

            # Apply year filter
            if filter_year != "All":
                query = query.filter(extract('year', Invoice.invoice_date) == filter_year)

            # Apply month filter
            if filter_month != "All":
                query = query.filter(extract('month', Invoice.invoice_date) == filter_month)

            # Apply payment cycle filter
            if filter_payment_cycle != "All":
                payment_term_map = {"Cash": "cash", "2-week": "2week", "Monthly": "monthly"}
                query = query.join(Supplier).filter(Supplier.payment_terms == payment_term_map[filter_payment_cycle])

            invoices = query.order_by(Invoice.invoice_date.desc()).all()

            if invoices:
                invoice_data = []
                for inv in invoices:
                    # Add indicator if invoice needs review
                    invoice_num = inv.invoice_number or '-'
                    if inv.needs_review:
                        invoice_num = f"⚠️ {invoice_num}"

                    invoice_data.append({
                        'Invoice #': invoice_num,
                        'Supplier': inv.supplier.short_name,
                        'Date': inv.invoice_date.strftime('%d/%m/%Y'),
                        'Due Date': inv.due_date.strftime('%d/%m/%Y') if inv.due_date else '-',
                        'Amount': format_currency(inv.total_amount),
                        'Items': len(inv.items)
                    })

                df = pd.DataFrame(invoice_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Show count of invoices needing review
                review_count = sum(1 for inv in invoices if inv.needs_review)
                if review_count > 0:
                    st.caption(f"📋 Total invoices: {len(invoices)} ({review_count} need review ⚠️)")
                else:
                    st.caption(f"📋 Total invoices: {len(invoices)}")
            else:
                st.info("No invoices match your filters.")
        finally:
            db.close()

    with tab2:
        st.markdown('<p class="sub-header">Add New Invoice</p>', unsafe_allow_html=True)

        # Get suppliers for dropdown
        db = next(get_db())
        suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
        db.close()

        if not suppliers:
            st.warning("⚠️ No suppliers found. Please add a supplier first!")
            return

        # Supplier and Invoice Date selection OUTSIDE form for dynamic updates
        col_select1, col_select2 = st.columns(2)

        with col_select1:
            supplier_names = [s.short_name for s in suppliers]

            # Check if OCR found a supplier match
            if 'ocr_supplier' in st.session_state and st.session_state.ocr_supplier:
                try:
                    default_index = supplier_names.index(st.session_state.ocr_supplier)
                    # Clear after using (prevent sticky behavior)
                    st.session_state.ocr_supplier = None
                except ValueError:
                    default_index = 0
            else:
                default_index = 0

            selected_supplier = st.selectbox(
                "Select Supplier *",
                supplier_names,
                index=default_index,
                key="invoice_supplier_select"
            )

        with col_select2:
            # Check if OCR found a date
            if 'ocr_date' in st.session_state and st.session_state.ocr_date:
                default_date = st.session_state.ocr_date
                # Clear after using
                st.session_state.ocr_date = None
            else:
                default_date = date.today()

            invoice_date = st.date_input(
                "Invoice Date *",
                value=default_date,
                format="DD/MM/YYYY",
                key="invoice_date_select"
            )

        # Get selected supplier object
        selected_supplier_obj = next(s for s in suppliers if s.short_name == selected_supplier)
        payment_terms = selected_supplier_obj.payment_terms
        ppn_handling = selected_supplier_obj.ppn_handling

        # Calculate due date based on invoice date and payment terms
        calculated_due_date = calculate_due_date(invoice_date, payment_terms)

        # Display supplier info
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            if payment_terms == 'cash':
                payment_info = "Cash (same day)"
            elif payment_terms == '2week':
                payment_info = "2-Week (15th & end of month)"
            else:
                payment_info = "Monthly (end of month)"
            st.info(f"**Payment Terms:** {payment_info}")

        with col_info2:
            st.info(f"**Due Date:** {format_date_input(calculated_due_date)}")

        with col_info3:
            ppn_info = "Included in prices" if ppn_handling == "included" else "Added at bottom (+11%)"
            st.info(f"**PPN:** {ppn_info}")

        st.markdown("---")

        # Initialize session state for invoice items
        if 'invoice_items' not in st.session_state:
            st.session_state.invoice_items = []

        # Initialize line items in session state
        if 'line_items' not in st.session_state:
            st.session_state.line_items = []

        # ============================================================================
        # SUPPLIES DETAIL SECTION (Outside form so buttons work independently)
        # ============================================================================
        st.markdown("**📦 Supplies Detail**")
        st.info("💡 Add products from this invoice - Total will be calculated automatically")

        # Get products for this supplier from Market List
        db = next(get_db())
        supplier_products = db.query(Product).filter(
            Product.preferred_supplier_id == selected_supplier_obj.id
        ).order_by(Product.name).all()
        db.close()

        if not supplier_products:
            st.warning(f"⚠️ No products found for {selected_supplier}. Add products in the Market List page first!")
        else:
            # Add line item inputs
            st.markdown("**Add Item:**")
            col_item1, col_item2, col_item3, col_item4 = st.columns([2, 1, 1, 0.5])

            # Build product options with size/measurement if available
            product_options = {}
            for p in supplier_products:
                if p.unit_size and p.unit_size_measurement:
                    # Show size for non-exact units (e.g., "Olive Oil (bottle - 1000ml)")
                    display_name = f"{p.name} ({p.unit} - {p.unit_size}{p.unit_size_measurement})"
                else:
                    # Regular display for exact units (e.g., "Tomatoes (kg)")
                    display_name = f"{p.name} ({p.unit})"
                product_options[display_name] = p

            with col_item1:
                selected_product_key = st.selectbox(
                    "Product",
                    options=list(product_options.keys()),
                    key="item_product_select",
                    label_visibility="collapsed"
                )
                selected_product = product_options[selected_product_key]

            with col_item2:
                item_qty = st.text_input(
                    "Quantity",
                    key="item_qty_input",
                    placeholder="e.g., 10",
                    label_visibility="collapsed"
                )
                st.caption(f"Unit: {selected_product.unit}")

            with col_item3:
                item_price = st.text_input(
                    "Unit Price",
                    key="item_price_input",
                    placeholder="15.000",
                    label_visibility="collapsed"
                )

            with col_item4:
                if st.button("➕", key="add_item_btn", help="Add item", use_container_width=True):
                    if item_qty and item_price:
                        try:
                            # Parse quantity and price
                            qty = float(item_qty.replace('.', '').replace(',', '.'))
                            price = float(item_price.replace('.', '').replace(',', ''))

                            st.session_state.line_items.append({
                                'name': selected_product.name,
                                'quantity': qty,
                                'unit': selected_product.unit,
                                'unit_price': price,
                                'total': qty * price,
                                'product_id': selected_product.id
                            })
                            st.rerun()
                        except ValueError:
                            st.error("Invalid quantity or price format")
                    else:
                        st.warning("Please fill in quantity and price")

        # Show added items and calculate totals
        if st.session_state.line_items:
            st.markdown("**Added Items:**")
            for idx, item in enumerate(st.session_state.line_items):
                col_show1, col_show2, col_show3 = st.columns([3, 2, 0.5])
                with col_show1:
                    st.text(f"{item['name']} - {item['quantity']} {item['unit']} × {format_currency(item['unit_price'])}")
                with col_show2:
                    st.text(f"= {format_currency(item['total'])}")
                with col_show3:
                    if st.button("🗑️", key=f"del_item_{idx}", help="Remove item"):
                        st.session_state.line_items.pop(idx)
                        st.rerun()

            st.markdown("---")

            # Calculate totals
            subtotal = sum(item['total'] for item in st.session_state.line_items)

            # Show totals based on PPN handling
            if ppn_handling == "added":
                st.markdown("### 🧮 Invoice Totals")
                col_calc1, col_calc2 = st.columns(2)

                with col_calc1:
                    st.markdown(f"**Subtotal (before tax):**")
                    st.markdown(f"**PPN (11%):**")
                    st.markdown(f"**Total Amount:**")

                with col_calc2:
                    ppn_amount = subtotal * 0.11
                    total_with_ppn = subtotal + ppn_amount
                    st.markdown(f"{format_currency(subtotal)}")
                    st.markdown(f"{format_currency(ppn_amount)}")
                    st.markdown(f"**{format_currency(total_with_ppn)}**")

                calculated_total = total_with_ppn
            else:  # PPN included
                st.markdown("### 🧮 Invoice Total")
                st.markdown(f"**Total Amount:** {format_currency(subtotal)}")
                calculated_total = subtotal

        else:
            st.info("👆 Add products above to start building the invoice")
            calculated_total = 0

        st.markdown("---")

        # Helper function to format amount input
        def format_amount_input(value):
            """Format number with dots as thousand separators"""
            if not value:
                return ""
            # Remove any existing dots/commas
            clean = value.replace('.', '').replace(',', '')
            if not clean.isdigit():
                return value
            # Add dots as thousand separators
            return f"{int(clean):,}".replace(',', '.')

        # ============================================================================
        # INVOICE FORM
        # ============================================================================
        with st.form("add_invoice_form"):
            st.markdown("**Invoice Details**")

            invoice_number = st.text_input("Invoice Number (optional)", placeholder="e.g., INV-2025-001")
            notes = st.text_area("Notes (optional)", placeholder="Any additional notes")

            needs_review = st.checkbox(
                "⚠️ Details to check",
                value=False,
                help="Check this if invoice needs follow-up (confirm details, returns, missing items, etc.)"
            )

            # Store calculated due date for saving
            due_date = calculated_due_date
            total_amount = calculated_total

            st.markdown("---")
            st.markdown(f"**Total to save:** {format_currency(total_amount)}")

            submitted = st.form_submit_button("💾 Save Invoice", use_container_width=True, type="primary")

            if submitted:
                if not selected_supplier or not invoice_date:
                    st.error("Please select supplier and invoice date!")
                elif total_amount <= 0:
                    st.error("Please add at least one product to the invoice!")
                else:
                    db = next(get_db())
                    try:
                        # Get supplier object
                        supplier = db.query(Supplier).filter(Supplier.short_name == selected_supplier).first()

                        # Create invoice
                        new_invoice = Invoice(
                            supplier_id=supplier.id,
                            invoice_number=invoice_number or None,
                            invoice_date=invoice_date,
                            due_date=due_date,
                            total_amount=total_amount,
                            notes=notes or None,
                            needs_review=needs_review
                        )
                        db.add(new_invoice)
                        db.flush()  # Get invoice ID

                        # Add line items if any
                        if st.session_state.line_items:
                            for item in st.session_state.line_items:
                                # Create invoice item (product already exists in Market List)
                                invoice_item = InvoiceItem(
                                    invoice_id=new_invoice.id,
                                    product_id=item['product_id'],
                                    product_name=item['name'],
                                    quantity=item['quantity'],
                                    unit=item['unit'],
                                    unit_price=item['unit_price'],
                                    total_price=item['total']
                                )
                                db.add(invoice_item)

                                # Calculate actual price paid (including PPN if applicable)
                                actual_price = item['unit_price']
                                if supplier.ppn_handling == "added":
                                    # For "PPN Added" suppliers, include 11% tax in the tracked price
                                    actual_price = item['unit_price'] * 1.11

                                # Update product current price if this is newer
                                product = db.query(Product).filter(Product.id == item['product_id']).first()
                                if product and (not product.current_price_date or invoice_date >= product.current_price_date):
                                    product.current_price = actual_price
                                    product.current_price_date = invoice_date

                                # ALWAYS create price history record (for tracking price changes over time)
                                price_history_record = PriceHistory(
                                    product_id=item['product_id'],
                                    supplier_id=supplier.id,
                                    invoice_id=new_invoice.id,
                                    price=actual_price,
                                    date=invoice_date
                                )
                                db.add(price_history_record)

                        db.commit()

                        st.success(f"✅ Invoice added successfully! Total: {format_currency(total_amount)}" +
                                 (f" ({len(st.session_state.line_items)} items)" if st.session_state.line_items else ""))
                        st.session_state.invoice_items = []
                        st.session_state.line_items = []  # Clear line items
                        st.session_state.amount_input = ""  # Clear amount field
                        st.session_state.ocr_text = ""  # Clear OCR text
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error adding invoice: {str(e)}")
                    finally:
                        db.close()

    with tab3:
        st.markdown('<p class="sub-header">Edit or Delete Invoice</p>', unsafe_allow_html=True)

        # Filters
        st.markdown("**🔍 Find Invoice**")
        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            # Supplier filter
            db = next(get_db())
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
            supplier_names = ["All"] + [s.short_name for s in suppliers]
            db.close()

            filter_supplier = st.selectbox("Filter by Supplier", supplier_names, key="edit_invoice_supplier_filter")

        with col_filter2:
            # Month and Year dropdowns
            col_month, col_year = st.columns(2)

            with col_month:
                months = ["All", "January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
                filter_month = st.selectbox("Month", months, index=date.today().month, key="edit_invoice_month_filter")

            with col_year:
                current_year = date.today().year
                years = ["All"] + [str(y) for y in range(current_year - 2, current_year + 2)]
                filter_year = st.selectbox("Year", years, index=3, key="edit_invoice_year_filter")  # index=3 is current year

        # Get filtered invoices
        db = next(get_db())
        from sqlalchemy.orm import joinedload
        query = db.query(Invoice).options(joinedload(Invoice.supplier))

        # Apply supplier filter
        if filter_supplier != "All":
            supplier = db.query(Supplier).filter(Supplier.short_name == filter_supplier).first()
            if supplier:
                query = query.filter(Invoice.supplier_id == supplier.id)

        # Apply month/year filter
        if filter_month != "All" and filter_year != "All":
            month_num = months.index(filter_month)  # 1-12
            year_num = int(filter_year)
            month_start = date(year_num, month_num, 1)
            if month_num == 12:
                month_end = date(year_num + 1, 1, 1)
            else:
                month_end = date(year_num, month_num + 1, 1)
            query = query.filter(Invoice.invoice_date >= month_start, Invoice.invoice_date < month_end)
        elif filter_year != "All":
            # Year only filter
            year_num = int(filter_year)
            query = query.filter(Invoice.invoice_date >= date(year_num, 1, 1), Invoice.invoice_date < date(year_num + 1, 1, 1))

        invoices = query.order_by(Invoice.invoice_date.desc()).all()

        if not invoices:
            db.close()
            st.info("No invoices match your filters. Try different filters or add an invoice first!")
        else:
            # Build invoice options WITHOUT ID
            invoice_options = [
                f"{inv.supplier.short_name} - {inv.invoice_number or 'No #'} - {format_currency(inv.total_amount)} - {inv.invoice_date.strftime('%d/%m/%Y')}"
                for inv in invoices
            ]
            db.close()

            st.markdown(f"**Found {len(invoices)} invoice(s)**")
            selected_option = st.selectbox("Select Invoice to Edit/Delete", invoice_options, key="edit_invoice_select")

            # Get the selected invoice
            selected_index = invoice_options.index(selected_option)
            invoice_to_edit = invoices[selected_index]

            # Load existing line items into session state
            if 'edit_invoice_id' not in st.session_state or st.session_state.edit_invoice_id != invoice_to_edit.id:
                st.session_state.edit_invoice_id = invoice_to_edit.id
                db = next(get_db())
                existing_items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_to_edit.id).all()
                st.session_state.edit_line_items = [
                    {
                        'name': item.product_name,
                        'quantity': item.quantity,
                        'unit': item.unit,
                        'unit_price': item.unit_price,
                        'total': item.total_price
                    }
                    for item in existing_items
                ]
                db.close()

            # Initialize edit line items if not exists
            if 'edit_line_items' not in st.session_state:
                st.session_state.edit_line_items = []

            st.markdown("---")

            # ============================================================================
            # SUPPLIES DETAIL SECTION (Outside form so buttons work independently)
            # ============================================================================
            st.markdown("**📦 Supplies Detail (Optional - for delivery & price control)**")
            st.info("💡 Track products from this invoice - quantities and prices")

            # Get products for this supplier from Market List
            db = next(get_db())
            supplier_products = db.query(Product).filter(
                Product.preferred_supplier_id == invoice_to_edit.supplier.id
            ).order_by(Product.name).all()
            db.close()

            if not supplier_products:
                st.warning(f"⚠️ No products found for {invoice_to_edit.supplier.short_name}. Add products in the Market List page first!")
            else:
                # Add line item inputs
                st.markdown("**Add Item:**")
                col_item1, col_item2, col_item3, col_item4 = st.columns([2, 1, 1, 0.5])

                # Build product options with size/measurement if available
                product_options = {}
                for p in supplier_products:
                    if p.unit_size and p.unit_size_measurement:
                        # Show size for non-exact units (e.g., "Olive Oil (bottle - 1000ml)")
                        display_name = f"{p.name} ({p.unit} - {p.unit_size}{p.unit_size_measurement})"
                    else:
                        # Regular display for exact units (e.g., "Tomatoes (kg)")
                        display_name = f"{p.name} ({p.unit})"
                    product_options[display_name] = p

                with col_item1:
                    selected_product_key = st.selectbox(
                        "Product",
                        options=list(product_options.keys()),
                        key="edit_item_product_select",
                        label_visibility="collapsed"
                    )
                    selected_product = product_options[selected_product_key]

                with col_item2:
                    edit_item_qty = st.text_input(
                        "Quantity",
                        key="edit_item_qty_input",
                        placeholder="e.g., 10",
                        label_visibility="collapsed"
                    )
                    st.caption(f"Unit: {selected_product.unit}")

                with col_item3:
                    edit_item_price = st.text_input(
                        "Unit Price",
                        key="edit_item_price_input",
                        placeholder="15.000",
                        label_visibility="collapsed"
                    )

                with col_item4:
                    if st.button("➕", key="edit_add_item_btn", help="Add item", use_container_width=True):
                        if edit_item_qty and edit_item_price:
                            try:
                                # Parse quantity and price
                                qty = float(edit_item_qty.replace('.', '').replace(',', '.'))
                                price = float(edit_item_price.replace('.', '').replace(',', ''))

                                st.session_state.edit_line_items.append({
                                    'name': selected_product.name,
                                    'quantity': qty,
                                    'unit': selected_product.unit,
                                    'unit_price': price,
                                    'total': qty * price
                                })
                                st.rerun()
                            except ValueError:
                                st.error("Invalid quantity or price format")
                        else:
                            st.warning("Please fill in all item fields")

                # Show added items
                if st.session_state.edit_line_items:
                    st.markdown("**Current Items:**")
                    for idx, item in enumerate(st.session_state.edit_line_items):
                        col_show1, col_show2, col_show3 = st.columns([3, 2, 0.5])
                        with col_show1:
                            st.text(f"{item['name']} - {item['quantity']} {item['unit']} × {format_currency(item['unit_price'])}")
                        with col_show2:
                            st.text(f"= {format_currency(item['total'])}")
                        with col_show3:
                            if st.button("🗑️", key=f"edit_del_item_{idx}", help="Remove item"):
                                st.session_state.edit_line_items.pop(idx)
                                st.rerun()

                    # Show total of line items
                    edit_line_items_total = sum(item['total'] for item in st.session_state.edit_line_items)
                    st.markdown(f"**Supplies Detail Total: {format_currency(edit_line_items_total)}**")

            st.markdown("---")

            # Edit form
            with st.form("edit_invoice_form"):
                st.markdown("**Edit Invoice Details**")
                col1, col2 = st.columns(2)

                with col1:
                    # Supplier dropdown (can change supplier)
                    db = next(get_db())
                    suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.short_name).all()
                    supplier_names = [s.short_name for s in suppliers]
                    current_supplier_index = supplier_names.index(invoice_to_edit.supplier.short_name)
                    db.close()

                    selected_supplier = st.selectbox("Supplier *", supplier_names, index=current_supplier_index)

                    invoice_number = st.text_input("Invoice Number", value=invoice_to_edit.invoice_number or "")
                    invoice_date = st.date_input(
                        "Invoice Date *",
                        value=invoice_to_edit.invoice_date,
                        format="DD/MM/YYYY"
                    )

                    # Amount with dots
                    current_amount_formatted = f"{int(invoice_to_edit.total_amount):,}".replace(',', '.')
                    amount_str = st.text_input(
                        "Total Amount (IDR) *",
                        value=current_amount_formatted,
                        help="Edit amount with dots as separators"
                    )

                with col2:
                    # Get supplier payment terms
                    db = next(get_db())
                    selected_supplier_obj = db.query(Supplier).filter(Supplier.short_name == selected_supplier).first()
                    payment_terms = selected_supplier_obj.payment_terms
                    db.close()

                    # Calculate due date
                    calculated_due_date = calculate_due_date(invoice_date, payment_terms)

                    if payment_terms == 'cash':
                        payment_info = "Cash (same day)"
                    elif payment_terms == '2week':
                        payment_info = "2-Week (15th & end of month)"
                    else:
                        payment_info = "Monthly (end of month)"

                    st.text_input("Payment Terms", value=payment_info, disabled=True)
                    st.text_input("Due Date (auto-calculated)", value=format_date_input(calculated_due_date), disabled=True)

                    # Parse amount
                    try:
                        total_amount = int(amount_str.replace('.', '').replace(',', ''))
                        st.success(f"Amount: {format_currency(total_amount)}")
                    except:
                        total_amount = 0
                        st.error("Invalid amount format")

                notes = st.text_area("Notes", value=invoice_to_edit.notes or "")

                needs_review = st.checkbox(
                    "⚠️ Details to check",
                    value=bool(invoice_to_edit.needs_review),
                    help="Check this if invoice needs follow-up (confirm details, returns, missing items, etc.)"
                )

                col_buttons = st.columns([2, 2, 1])
                with col_buttons[0]:
                    update_btn = st.form_submit_button("Update Invoice", use_container_width=True)
                with col_buttons[1]:
                    delete_btn = st.form_submit_button("Delete Invoice", use_container_width=True, type="secondary")

                if update_btn:
                    if total_amount <= 0:
                        st.error("Amount must be greater than 0!")
                    else:
                        db = next(get_db())
                        try:
                            # Get supplier
                            supplier = db.query(Supplier).filter(Supplier.short_name == selected_supplier).first()

                            # Update invoice
                            invoice = db.query(Invoice).filter(Invoice.id == invoice_to_edit.id).first()
                            invoice.supplier_id = supplier.id
                            invoice.invoice_number = invoice_number or None
                            invoice.invoice_date = invoice_date
                            invoice.due_date = calculated_due_date
                            invoice.total_amount = total_amount
                            invoice.notes = notes or None
                            invoice.needs_review = needs_review

                            # Update line items - delete old ones and insert new ones
                            # Delete existing items
                            db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).delete()

                            # Add new line items if any
                            if st.session_state.edit_line_items:
                                for item in st.session_state.edit_line_items:
                                    # Check if product exists, create if not
                                    product = db.query(Product).filter(Product.name == item['name']).first()
                                    if not product:
                                        product = Product(
                                            name=item['name'],
                                            unit=item['unit'],
                                            current_price=item['unit_price'],
                                            current_price_date=invoice_date,
                                            preferred_supplier_id=supplier.id
                                        )
                                        db.add(product)
                                        db.flush()

                                    # Create invoice item
                                    invoice_item = InvoiceItem(
                                        invoice_id=invoice.id,
                                        product_id=product.id,
                                        product_name=item['name'],
                                        quantity=item['quantity'],
                                        unit=item['unit'],
                                        unit_price=item['unit_price'],
                                        total_price=item['total']
                                    )
                                    db.add(invoice_item)

                            db.commit()

                            # Clear session state
                            st.session_state.edit_line_items = []
                            st.session_state.edit_invoice_id = None

                            st.success(f"✅ Invoice updated successfully!" +
                                     (f" ({len(st.session_state.get('edit_line_items', []))} items)" if st.session_state.get('edit_line_items') else ""))
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Error updating invoice: {str(e)}")
                        finally:
                            db.close()

                if delete_btn:
                    db = next(get_db())
                    try:
                        invoice = db.query(Invoice).filter(Invoice.id == invoice_to_edit.id).first()
                        db.delete(invoice)
                        db.commit()
                        st.success(f"✅ Invoice deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error deleting invoice: {str(e)}")
                    finally:
                        db.close()


def show_reports():
    """Reports page - Analytics and reports"""
    st.markdown('<p class="main-header">📊 Reports</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Payment Summary", "Supplier Spend Analysis"])

    with tab1:
        st.markdown('<p class="sub-header">Payment Summary Report</p>', unsafe_allow_html=True)
        st.caption("Generate payment lists for Marcella - grouped by payment due dates")

        # Filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            current_year = date.today().year
            years = [current_year - 1, current_year, current_year + 1]
            selected_year = st.selectbox("Year", years, index=1, key="payment_report_year")

        with col2:
            selected_month = st.selectbox(
                "Month",
                list(range(1, 13)),
                format_func=lambda x: date(2025, x, 1).strftime('%B'),
                index=date.today().month - 1,
                key="payment_report_month"
            )

        with col3:
            payment_cycle = st.selectbox(
                "Payment Cycle",
                ["All", "15th (Mid-month)", "End of Month"],
                key="payment_report_cycle"
            )

        with col4:
            # Category filter
            categories = ["All", "Food", "Drinks", "Operational"]
            filter_category = st.selectbox("Category", categories, key="payment_report_category")

        db = next(get_db())
        try:
            # Get invoices from selected month, filtered by supplier payment terms
            from sqlalchemy import extract
            from sqlalchemy.orm import joinedload

            query = db.query(Invoice).options(joinedload(Invoice.supplier)).filter(
                extract('year', Invoice.invoice_date) == selected_year,
                extract('month', Invoice.invoice_date) == selected_month
            )

            # Filter by supplier payment terms (payment cycle)
            if payment_cycle == "15th (Mid-month)":
                # Only suppliers with 2-week payment terms
                query = query.join(Supplier).filter(Supplier.payment_terms == '2week')
            elif payment_cycle == "End of Month":
                # Only suppliers with monthly payment terms
                query = query.join(Supplier).filter(Supplier.payment_terms == 'monthly')
            # If "All", don't filter by payment terms

            invoices = query.all()

            # Apply category filter if needed
            if filter_category != "All":
                # Filter by supplier category
                invoices = [inv for inv in invoices if inv.supplier.category == filter_category]

            if invoices:
                # Group by supplier
                supplier_data = {}
                for inv in invoices:
                    supplier_name = inv.supplier.short_name
                    if supplier_name not in supplier_data:
                        supplier_data[supplier_name] = {
                            'total': 0,
                            'count': 0,
                            'needs_review': False,
                            'payment_terms': inv.supplier.payment_terms,
                            'category': inv.supplier.category
                        }

                    supplier_data[supplier_name]['total'] += inv.total_amount
                    supplier_data[supplier_name]['count'] += 1

                    # Check if any invoice needs review
                    if inv.needs_review:
                        supplier_data[supplier_name]['needs_review'] = True

                # Create report dataframe
                report_data = []
                for supplier, data in supplier_data.items():
                    # Add warning icon if any invoice needs review
                    supplier_display = f"⚠️ {supplier}" if data['needs_review'] else supplier

                    report_data.append({
                        'Supplier': supplier_display,
                        'Payment Terms': data['payment_terms'].upper(),
                        'Total Amount': format_currency(data['total']),
                        'Category': data['category'],
                        'Total_Raw': data['total']  # Keep raw number for subtotal calculations
                    })

                df = pd.DataFrame(report_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Summary
                total_amount = sum(data['total'] for data in supplier_data.values())
                review_count = sum(1 for data in supplier_data.values() if data['needs_review'])

                st.markdown("---")
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric("Total Payment Amount", format_currency(total_amount))
                with col_metric2:
                    if review_count > 0:
                        st.metric("Suppliers Needing Review", f"{review_count} ⚠️")
                    else:
                        st.metric("Suppliers Needing Review", "0 ✅")

                # Download buttons
                st.markdown("---")
                st.markdown("**📥 Download Payment Summary**")

                cycle_name = payment_cycle if payment_cycle != "All" else "All cycles"
                month_name = date(selected_year, selected_month, 1).strftime('%B %Y')

                # PDF download
                pdf_buffer = generate_payment_schedule_pdf(
                    report_data,
                    month_name,
                    cycle_name,
                    total_amount,
                    review_count,
                    filter_category
                )
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_buffer,
                    file_name=f"payment_summary_{month_name.replace(' ', '_')}_{cycle_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            else:
                month_name = date(selected_year, selected_month, 1).strftime('%B %Y')
                cycle_text = f" - {payment_cycle}" if payment_cycle != "All" else ""
                st.info(f"No invoices found for {month_name}{cycle_text}")
        finally:
            db.close()

    with tab2:
        st.markdown('<p class="sub-header">Supplier Spend Analysis</p>', unsafe_allow_html=True)

        db = next(get_db())
        try:
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()

            if suppliers:
                spend_data = []
                for supplier in suppliers:
                    total_spend = sum(inv.total_amount for inv in supplier.invoices)
                    invoice_count = len(supplier.invoices)

                    if invoice_count > 0:
                        spend_data.append({
                            'Supplier': supplier.short_name,
                            'Total Invoices': invoice_count,
                            'Total Spend': total_spend,
                            'Total Spend (Formatted)': format_currency(total_spend),
                            'Payment Terms': supplier.payment_terms.upper()
                        })

                if spend_data:
                    # Sort by total spend
                    spend_data.sort(key=lambda x: x['Total Spend'], reverse=True)

                    # Display dataframe (without the raw Total Spend column)
                    display_data = [{k: v for k, v in d.items() if k != 'Total Spend'} for d in spend_data]
                    df = pd.DataFrame(display_data)
                    df = df.rename(columns={'Total Spend (Formatted)': 'Total Spend'})
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Total summary
                    grand_total = sum(d['Total Spend'] for d in spend_data)
                    st.markdown(f"**Grand Total Spend: {format_currency(grand_total)}**")
                else:
                    st.info("No invoices found for any supplier yet.")
            else:
                st.info("No suppliers found.")
        finally:
            db.close()


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Sidebar navigation
    st.sidebar.markdown("### 📦 Chela Suppliers")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Suppliers", "Market List", "Invoices", "Reports"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Quick Stats**")
    stats = get_stats()
    st.sidebar.metric("Total Suppliers", stats['total_suppliers'])
    st.sidebar.metric("Total Invoices", stats['total_invoices'])

    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Suppliers":
        show_suppliers()
    elif page == "Market List":
        show_market_list()
    elif page == "Invoices":
        show_invoices()
    elif page == "Reports":
        show_reports()


if __name__ == "__main__":
    main()
