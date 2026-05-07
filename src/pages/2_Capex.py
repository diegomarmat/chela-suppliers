"""
Chela Expenses - CAPEX (Capital Expenditures)
"""

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import io
from datetime import datetime, date
from models import get_db, init_db, CapexVendor, CapexExpense
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

st.set_page_config(
    page_title="Chela Expenses - CAPEX",
    page_icon="🔧",
    layout="wide"
)

# ============================================================================
# AUTHENTICATION
# ============================================================================

def get_auth_config():
    return {
        'credentials': {
            'usernames': {
                'diego': {
                    'name': 'Diego',
                    'password': '$2b$12$x4FjXoa0m/qRElFONGa9guFRU305NtRp682iqGB1gJG0Or86ni7B.',
                    'role': 'admin'
                },
                'marcella': {
                    'name': 'Marcella',
                    'password': '$2b$12$pOrGMqVWHQ3F91q9AxquveMgzuARc4wEhlIok40SBrBNMyre8bOA.',
                    'role': 'admin'
                },
                'astik': {
                    'name': 'Astik',
                    'password': '$2b$12$ppERYa/1M/haJa3VjUjqmOslODo1mR926eiK4cpd1eL0D86QjLbqa',
                    'role': 'expenses'
                }
            }
        },
        'cookie': {
            'name': 'chela_expenses_auth',
            'key': 'chela_expenses_secret_key_2026',
            'expiry_days': 30
        },
        'preauthorized': {'emails': []}
    }


def check_authentication():
    config = get_auth_config()
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config.get('preauthorized', {})
    )
    authenticator.login(location='main')
    authentication_status = st.session_state.get('authentication_status')
    username = st.session_state.get('username')

    if authentication_status == False:
        st.error('Username or password is incorrect')
        return False, None
    if authentication_status == None:
        st.warning('Please enter your username and password')
        return False, None

    user_role = config['credentials']['usernames'].get(username, {}).get('role', '')
    if user_role not in ['admin', 'expenses']:
        st.error('You do not have access to Expenses Platform')
        authenticator.logout(location='main')
        return False, None

    return True, authenticator


# ============================================================================
# HELPERS
# ============================================================================

def format_currency(amount):
    if amount is None:
        return "Rp 0"
    return f"Rp {amount:,.0f}"

CATEGORIES = ["Kitchen Equipment", "Bar Equipment", "Furniture", "Construction", "Technology", "Vehicles", "Other"]
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def generate_capex_payment_pdf(report_data, month_name, total_amount, category_filter, payment_terms_filter, responsible_filter):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
                                  textColor=colors.HexColor('#2C1810'), spaceAfter=30, alignment=1)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=12,
                                     textColor=colors.HexColor('#5D4037'), spaceAfter=20, alignment=1)
    cat_style = ParagraphStyle('Cat', parent=styles['Normal'], fontSize=11,
                                textColor=colors.HexColor('#5D4037'), spaceAfter=10, alignment=0)

    parts = [month_name]
    if payment_terms_filter != "All":
        parts.append(payment_terms_filter)
    if responsible_filter != "All":
        parts.append(f"Responsible: {responsible_filter}")
    if category_filter != "All":
        parts.append(category_filter)
    subtitle_text = " | ".join(parts)

    elements.append(Paragraph("CHELA<br/>CAPEX Payment Summary", title_style))
    elements.append(Paragraph(subtitle_text, subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))

    def make_vendor_table(rows):
        table_data = [['Vendor', 'Payment Terms', 'Responsible', 'Total Amount']]
        for row in rows:
            table_data.append([row['Vendor'], row['Payment Terms'], row['Responsible'], row['Total Amount']])
        t = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.3*inch, 1.6*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5D4037')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ]))
        return t

    if category_filter == "All":
        from collections import defaultdict
        by_cat = defaultdict(list)
        for row in report_data:
            by_cat[row.get('Category', 'Other')].append(row)

        for cat_name in sorted(by_cat.keys()):
            cat_rows = by_cat[cat_name]
            elements.append(Paragraph(f"<b>{cat_name}</b>", cat_style))
            elements.append(Spacer(1, 0.05 * inch))

            table_data = [['Vendor', 'Payment Terms', 'Responsible', 'Total Amount']]
            cat_subtotal = 0
            for row in cat_rows:
                table_data.append([row['Vendor'], row['Payment Terms'], row['Responsible'], row['Total Amount']])
                cat_subtotal += row.get('Total_Raw', 0)
            table_data.append(['Subtotal', '', '', format_currency(cat_subtotal)])

            t = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.3*inch, 1.6*inch])
            subtotal_idx = len(table_data) - 1
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5D4037')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.beige]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('TOPPADDING', (0, 1), (-1, -2), 7),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 7),
                ('BACKGROUND', (0, subtotal_idx), (-1, subtotal_idx), colors.HexColor('#E0E0E0')),
                ('FONTNAME', (0, subtotal_idx), (-1, subtotal_idx), 'Helvetica-Bold'),
                ('FONTSIZE', (0, subtotal_idx), (-1, subtotal_idx), 11),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.3 * inch))
    else:
        elements.append(make_vendor_table(report_data))
        elements.append(Spacer(1, 0.4 * inch))

    summary = Table([['Total Payment Amount', format_currency(total_amount)]], colWidths=[3*inch, 3*inch])
    summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2E4057')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(summary)
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d/%m/%Y at %H:%M')}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_capex_pdf(expense_data, filters_text, total_amount, count):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
                                  textColor=colors.HexColor('#2C1810'), spaceAfter=30, alignment=1)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=12,
                                     textColor=colors.HexColor('#5D4037'), spaceAfter=20, alignment=1)

    elements.append(Paragraph("CHELA<br/>CAPEX Report", title_style))
    elements.append(Paragraph(filters_text, subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))

    table_data = [['Vendor', 'Category', 'Description', 'Date', 'Amount']]
    for row in expense_data:
        table_data.append([row['Vendor'], row['Category'], row['Description'], row['Date'], row['Amount']])

    table = Table(table_data, colWidths=[1.6*inch, 1.4*inch, 1.8*inch, 1.1*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5D4037')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige]),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    summary = Table([['Total Expenses', str(count)], ['Total Amount', format_currency(total_amount)]],
                     colWidths=[3*inch, 3*inch])
    summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary)
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d/%m/%Y at %H:%M')}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ============================================================================
# PAGES
# ============================================================================

def show_overview(db):
    st.title("🔧 CAPEX Overview")
    st.markdown("---")

    today = date.today()
    current_month = today.month
    current_year = today.year

    expenses_this_month = db.query(CapexExpense).filter(
        CapexExpense.month == current_month,
        CapexExpense.year == current_year
    ).all()

    total = sum(e.amount for e in expenses_this_month)
    vendor_count = db.query(CapexVendor).filter(CapexVendor.is_active == True).count()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active Vendors", vendor_count)
    with col2:
        st.metric(f"Total {MONTHS[current_month-1]}", format_currency(total))

    if expenses_this_month:
        st.markdown("---")
        st.markdown(f"### {MONTHS[current_month-1]} {current_year} — By Category")
        by_cat = {}
        for e in expenses_this_month:
            cat = e.vendor.category if e.vendor else "Other"
            by_cat[cat] = by_cat.get(cat, 0) + e.amount
        cat_data = pd.DataFrame([{"Category": k, "Amount": format_currency(v)} for k, v in sorted(by_cat.items(), key=lambda x: -x[1])])
        st.dataframe(cat_data, use_container_width=True, hide_index=True)

        st.markdown(f"### {MONTHS[current_month-1]} Expenses")
        for e in expenses_this_month:
            cols = st.columns([3, 1])
            with cols[0]:
                st.write(f"**{e.vendor.name}**" + (f" — {e.description}" if e.description else ""))
            with cols[1]:
                st.write(format_currency(e.amount))


def show_vendors(db):
    st.title("🔧 CAPEX Vendors")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Vendor List", "Add Vendor", "Edit Vendor"])

    with tab1:
        vendors = db.query(CapexVendor).filter(CapexVendor.is_active == True).order_by(
            CapexVendor.category, CapexVendor.name
        ).all()

        if vendors:
            data = [{
                "Name": v.name,
                "Category": v.category,
                "Payment Terms": v.payment_terms or "-",
                "Responsible": v.responsible or "-",
            } for v in vendors]
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            st.caption(f"{len(vendors)} active vendors")
        else:
            st.info("No vendors yet — add your first one in the 'Add Vendor' tab.")

    with tab2:
        st.markdown("### Add New Vendor")
        with st.form("add_capex_vendor", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                vendor_name = st.text_input("Vendor Name *", placeholder="e.g., CV Bali Kitchen, Ace Hardware")
                category = st.selectbox("Category *", CATEGORIES)
                contact = st.text_input("Contact", placeholder="Phone or WhatsApp number")
                payment_terms = st.selectbox("Payment Terms", ["Cash", "2-Week", "Monthly"])
                responsible = st.selectbox("Responsible", ["Diego", "Marcella", "Admin"])
            with col2:
                bank_name = st.text_input("Bank Name", placeholder="e.g., BCA, Mandiri, BNI")
                bank_account_number = st.text_input("Account Number", placeholder="e.g., 1234567890")
                bank_account_name = st.text_input("Account Name", placeholder="Name on the account")
                notes = st.text_area("Notes", placeholder="Any useful info...", height=100)

            if st.form_submit_button("Add Vendor", type="primary", use_container_width=True):
                if not vendor_name:
                    st.error("Vendor name is required")
                else:
                    existing = db.query(CapexVendor).filter(CapexVendor.name == vendor_name).first()
                    if existing:
                        st.error(f"A vendor named '{vendor_name}' already exists")
                    else:
                        new_vendor = CapexVendor(
                            name=vendor_name,
                            category=category,
                            contact=contact or None,
                            payment_terms=payment_terms.lower().replace("-", ""),
                            responsible=responsible,
                            bank_name=bank_name or None,
                            bank_account_number=bank_account_number or None,
                            bank_account_name=bank_account_name or None,
                            notes=notes or None
                        )
                        db.add(new_vendor)
                        db.commit()
                        st.success(f"Vendor '{vendor_name}' added!")
                        st.rerun()

    with tab3:
        st.markdown("### Edit Vendor")
        vendors_all = db.query(CapexVendor).filter(CapexVendor.is_active == True).order_by(CapexVendor.name).all()

        if not vendors_all:
            st.info("No vendors yet. Add one first.")
        else:
            vendor_options = [v.name for v in vendors_all]
            selected_name = st.selectbox("Select vendor to edit", vendor_options, key="capex_edit_vendor_sel")
            v = next((x for x in vendors_all if x.name == selected_name), None)

            if v:
                st.markdown("---")
                with st.form("edit_capex_vendor"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Vendor Name *", value=v.name)
                        new_category = st.selectbox("Category *", CATEGORIES,
                            index=CATEGORIES.index(v.category) if v.category in CATEGORIES else 0)
                        new_contact = st.text_input("Contact", value=v.contact or "")
                        pt_options = ["Cash", "2-Week", "Monthly"]
                        pt_map = {"cash": "Cash", "2week": "2-Week", "monthly": "Monthly"}
                        new_payment_terms = st.selectbox("Payment Terms", pt_options,
                            index=pt_options.index(pt_map.get(v.payment_terms, "Cash")))
                        resp_options = ["Diego", "Marcella", "Admin"]
                        new_responsible = st.selectbox("Responsible", resp_options,
                            index=resp_options.index(v.responsible) if v.responsible in resp_options else 0)
                    with col2:
                        new_bank_name = st.text_input("Bank Name", value=v.bank_name or "")
                        new_bank_number = st.text_input("Account Number", value=v.bank_account_number or "")
                        new_bank_account_name = st.text_input("Account Name", value=v.bank_account_name or "")
                        new_notes = st.text_area("Notes", value=v.notes or "", height=100)

                    col_btns = st.columns([3, 1])
                    with col_btns[0]:
                        submitted = st.form_submit_button("Update Vendor", type="primary", use_container_width=True)
                    with col_btns[1]:
                        deactivate = st.form_submit_button("Deactivate", use_container_width=True)

                    if submitted:
                        if not new_name:
                            st.error("Vendor name is required")
                        else:
                            v.name = new_name
                            v.category = new_category
                            v.contact = new_contact or None
                            v.payment_terms = new_payment_terms.lower().replace("-", "")
                            v.responsible = new_responsible
                            v.bank_name = new_bank_name or None
                            v.bank_account_number = new_bank_number or None
                            v.bank_account_name = new_bank_account_name or None
                            v.notes = new_notes or None
                            db.commit()
                            st.success(f"Vendor '{new_name}' updated!")
                            st.rerun()

                    if deactivate:
                        v.is_active = False
                        db.commit()
                        st.success(f"Vendor '{v.name}' deactivated.")
                        st.rerun()


def show_expenses(db):
    st.title("💸 CAPEX Expenses")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["View Expenses", "Add Expense", "Edit Expense"])

    with tab2:
        vendors = db.query(CapexVendor).filter(CapexVendor.is_active == True).order_by(CapexVendor.name).all()
        if not vendors:
            st.warning("No vendors yet. Add vendors first.")
            return

        st.markdown("### Add New Expense")
        with st.form("add_capex_expense", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                vendor_options = {v.name: v.id for v in vendors}
                selected_vendor_name = st.selectbox("Vendor *", list(vendor_options.keys()))
                amount = st.number_input("Amount (Rp) *", min_value=0, step=10000)
                description = st.text_input("Description", placeholder="e.g., Commercial oven purchase")
            with col2:
                expense_date = st.date_input("Date *", value=date.today())

            if st.form_submit_button("Add Expense", type="primary", use_container_width=True):
                if not selected_vendor_name or amount <= 0:
                    st.error("Vendor and amount are required")
                else:
                    new_expense = CapexExpense(
                        vendor_id=vendor_options[selected_vendor_name],
                        amount=amount,
                        expense_date=expense_date,
                        month=expense_date.month,
                        year=expense_date.year,
                        description=description or None,
                    )
                    db.add(new_expense)
                    db.commit()
                    st.success(f"Expense added: {selected_vendor_name} — {format_currency(amount)}")
                    st.rerun()

    with tab1:
        all_vendors = db.query(CapexVendor).filter(CapexVendor.is_active == True).order_by(CapexVendor.name).all()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            vendor_names = ["All"] + [v.name for v in all_vendors]
            filter_vendor = st.selectbox("Vendor", vendor_names, key="capex_exp_filter_vendor")
        with col2:
            filter_category = st.selectbox("Category", ["All"] + CATEGORIES, key="capex_exp_filter_category")
        with col3:
            current_year = date.today().year
            filter_year = st.selectbox("Year", ["All", current_year - 1, current_year, current_year + 1],
                                        index=2, key="capex_exp_filter_year")
        with col4:
            filter_month = st.selectbox("Month", ["All"] + MONTHS,
                                         index=date.today().month, key="capex_exp_filter_month")

        from sqlalchemy.orm import joinedload
        query = db.query(CapexExpense).options(joinedload(CapexExpense.vendor))

        if filter_vendor != "All":
            vendor_obj = next((v for v in all_vendors if v.name == filter_vendor), None)
            if vendor_obj:
                query = query.filter(CapexExpense.vendor_id == vendor_obj.id)
        if filter_category != "All":
            query = query.join(CapexVendor).filter(CapexVendor.category == filter_category)
        if filter_year != "All":
            query = query.filter(CapexExpense.year == filter_year)
        if filter_month != "All":
            month_num = MONTHS.index(filter_month) + 1
            query = query.filter(CapexExpense.month == month_num)

        expenses = query.order_by(CapexExpense.expense_date.desc()).all()

        if expenses:
            expense_data = [{
                'Vendor': e.vendor.name,
                'Category': e.vendor.category if e.vendor else '-',
                'Description': e.description or '-',
                'Date': e.expense_date.strftime('%d/%m/%Y'),
                'Amount': format_currency(e.amount)
            } for e in expenses]

            total_amount = sum(e.amount for e in expenses)
            st.metric("Total", format_currency(total_amount))
            st.dataframe(pd.DataFrame(expense_data), use_container_width=True, hide_index=True)
            st.caption(f"{len(expenses)} expense(s)")

            filters_parts = []
            if filter_vendor != "All": filters_parts.append(f"Vendor: {filter_vendor}")
            if filter_category != "All": filters_parts.append(f"Category: {filter_category}")
            if filter_year != "All": filters_parts.append(f"Year: {filter_year}")
            if filter_month != "All": filters_parts.append(f"Month: {filter_month}")
            filters_text = " | ".join(filters_parts) if filters_parts else "All CAPEX Expenses"

            with st.expander("📄 Export to PDF"):
                if st.button("Generate PDF Report", key="gen_capex_pdf"):
                    pdf_buffer = generate_capex_pdf(expense_data, filters_text, total_amount, len(expenses))
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_buffer,
                        file_name=f"capex_report_{date.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No expenses match your filters.")

    with tab3:
        st.markdown("### Edit Expense")

        all_expenses = db.query(CapexExpense).order_by(
            CapexExpense.expense_date.desc()
        ).limit(100).all()

        if not all_expenses:
            st.info("No expenses yet.")
        else:
            expense_options = {
                f"{e.vendor.name} — {format_currency(e.amount)} — {e.expense_date}": e
                for e in all_expenses
            }
            selected_label = st.selectbox("Select expense to edit", list(expense_options.keys()), key="capex_edit_exp_sel")
            e = expense_options[selected_label]

            st.markdown("---")
            vendors_edit = db.query(CapexVendor).filter(CapexVendor.is_active == True).order_by(CapexVendor.name).all()
            vendor_names = [v.name for v in vendors_edit]

            with st.form("edit_capex_expense"):
                col1, col2 = st.columns(2)
                with col1:
                    current_vendor_name = e.vendor.name if e.vendor else vendor_names[0]
                    new_vendor_name = st.selectbox("Vendor *", vendor_names,
                        index=vendor_names.index(current_vendor_name) if current_vendor_name in vendor_names else 0)
                    new_amount = st.number_input("Amount (Rp) *", min_value=0, step=10000, value=int(e.amount))
                    new_description = st.text_input("Description", value=e.description or "")
                with col2:
                    new_date = st.date_input("Date *", value=e.expense_date)

                col_btns = st.columns([3, 1])
                with col_btns[0]:
                    submitted = st.form_submit_button("Update Expense", type="primary", use_container_width=True)
                with col_btns[1]:
                    delete = st.form_submit_button("Delete", use_container_width=True)

                if submitted:
                    vendor_obj = next((v for v in vendors_edit if v.name == new_vendor_name), None)
                    if vendor_obj and new_amount > 0:
                        e.vendor_id = vendor_obj.id
                        e.amount = new_amount
                        e.description = new_description or None
                        e.expense_date = new_date
                        e.month = new_date.month
                        e.year = new_date.year
                        db.commit()
                        st.success("Expense updated!")
                        st.rerun()
                    else:
                        st.error("Vendor and amount are required")

                if delete:
                    db.delete(e)
                    db.commit()
                    st.success("Expense deleted.")
                    st.rerun()


def show_payments(db):
    st.title("💳 CAPEX Payments")
    st.markdown("---")
    st.caption("Monthly CAPEX payment summary — grouped by vendor")

    from sqlalchemy.orm import joinedload

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_year = date.today().year
        selected_year = st.selectbox("Year", [current_year - 1, current_year, current_year + 1],
                                      index=1, key="capex_pay_year")
    with col2:
        selected_month_name = st.selectbox("Month", MONTHS, index=date.today().month - 1, key="capex_pay_month")
        selected_month = MONTHS.index(selected_month_name) + 1
    with col3:
        pt_options = ["All", "Cash", "2-Week", "Monthly"]
        filter_payment_terms = st.selectbox("Payment Terms", pt_options, key="capex_pay_pt")
    with col4:
        filter_category = st.selectbox("Category", ["All"] + CATEGORIES, key="capex_pay_cat")

    filter_responsible = st.selectbox("Responsible", ["All", "Diego", "Marcella", "Admin"], key="capex_pay_resp")

    query = db.query(CapexExpense).options(joinedload(CapexExpense.vendor)).filter(
        CapexExpense.month == selected_month,
        CapexExpense.year == selected_year
    )
    expenses = query.all()

    pt_map = {"Cash": "cash", "2-Week": "2week", "Monthly": "monthly"}
    if filter_payment_terms != "All":
        expenses = [e for e in expenses if e.vendor and e.vendor.payment_terms == pt_map[filter_payment_terms]]
    if filter_category != "All":
        expenses = [e for e in expenses if e.vendor and e.vendor.category == filter_category]
    if filter_responsible != "All":
        expenses = [e for e in expenses if e.vendor and e.vendor.responsible == filter_responsible]

    if expenses:
        vendor_data = {}
        for e in expenses:
            vname = e.vendor.name if e.vendor else "Unknown"
            if vname not in vendor_data:
                vendor_data[vname] = {
                    'total': 0,
                    'payment_terms': (e.vendor.payment_terms or 'cash').upper(),
                    'responsible': e.vendor.responsible or '-',
                    'category': e.vendor.category or 'Other',
                }
            vendor_data[vname]['total'] += e.amount

        report_data = [
            {
                'Vendor': vname,
                'Payment Terms': data['payment_terms'],
                'Responsible': data['responsible'],
                'Total Amount': format_currency(data['total']),
                'Category': data['category'],
                'Total_Raw': data['total'],
            }
            for vname, data in sorted(vendor_data.items(), key=lambda x: x[1]['category'])
        ]

        total_amount = sum(d['Total_Raw'] for d in report_data)

        display_df = pd.DataFrame([{k: v for k, v in r.items() if k not in ('Total_Raw', 'Category')} for r in report_data])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.metric("Total Payment Amount", format_currency(total_amount))

        st.markdown("---")
        st.markdown("**📥 Download Payment Summary**")
        month_name = f"{selected_month_name} {selected_year}"
        pdf_buffer = generate_capex_payment_pdf(
            report_data, month_name, total_amount,
            filter_category, filter_payment_terms, filter_responsible
        )
        st.download_button(
            label="📄 Download PDF",
            data=pdf_buffer,
            file_name=f"capex_payments_{selected_month_name}_{selected_year}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="capex_pay_pdf_dl"
        )
    else:
        st.info(f"No CAPEX expenses for {selected_month_name} {selected_year} matching these filters.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    is_authenticated, authenticator = check_authentication()
    if not is_authenticated:
        st.stop()

    st.sidebar.markdown("### 🔧 CAPEX")
    st.sidebar.markdown(f"**User:** {st.session_state.get('name', 'Unknown')}")
    authenticator.logout(location='sidebar')
    st.sidebar.markdown("---")

    page = st.sidebar.radio("Section", ["Overview", "Vendors", "Expenses", "Payments"])

    init_db()
    db = next(get_db())

    try:
        if page == "Overview":
            show_overview(db)
        elif page == "Vendors":
            show_vendors(db)
        elif page == "Expenses":
            show_expenses(db)
        elif page == "Payments":
            show_payments(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
