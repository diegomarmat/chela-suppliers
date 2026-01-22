"""
Chela Expenses - OVERHEAD (Operational Expenses)
Separate page for better performance
"""

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime, date
from models import get_db, init_db
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

# Page config
st.set_page_config(
    page_title="Chela Expenses - Overhead",
    page_icon="🏢",
    layout="wide"
)

# ============================================================================
# AUTHENTICATION (same as main app)
# ============================================================================

def get_auth_config():
    """Get authentication config"""
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
    """Check if user is authenticated."""
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
# HELPER FUNCTIONS
# ============================================================================

def format_currency(amount):
    """Format amount as IDR currency"""
    if amount is None:
        return "Rp 0"
    return f"Rp {amount:,.0f}"


# ============================================================================
# MAIN PAGE
# ============================================================================

def main():
    # Check authentication
    is_authenticated, authenticator = check_authentication()

    if not is_authenticated:
        st.stop()

    # Sidebar
    st.sidebar.markdown("### 🏢 Overhead")
    st.sidebar.markdown(f"**User:** {st.session_state.get('name', 'Unknown')}")
    authenticator.logout(location='sidebar')
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Section",
        ["Overview", "Vendors", "Expenses", "Payments"]
    )

    # Initialize database
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


def show_overview(db):
    """Overview page"""
    st.title("🏢 Operational Overhead")
    st.markdown("---")

    st.info("""
    **What goes here:**
    - Trash pickup
    - Electricity bills (PLN)
    - Water bills (PDAM)
    - Cleaning services
    - Gardener
    - Pest control
    - Internet/phone
    - Security
    - And other operational expenses...
    """)

    st.markdown("### Current Status")
    st.success("This section is now separate from the main app for better performance.")

    # Quick stats placeholder
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Vendors", "Coming soon")
    with col2:
        st.metric("This Month", "Coming soon")
    with col3:
        st.metric("Pending Payments", "Coming soon")


def show_vendors(db):
    """Manage overhead vendors"""
    st.title("🏢 Overhead Vendors")
    st.markdown("---")

    st.markdown("""
    **Operational vendors are simpler than ingredient suppliers:**
    - Name (e.g., "PLN" for electricity)
    - Contact (phone/email)
    - Typical amount (if fixed monthly)
    - Payment cycle (when bills typically come)
    """)

    st.markdown("---")

    # Add vendor form
    st.markdown("### Add New Vendor")
    with st.form("add_overhead_vendor"):
        col1, col2 = st.columns(2)
        with col1:
            vendor_name = st.text_input("Vendor Name *", placeholder="e.g., PLN, PDAM, Gardener Wayan")
            contact = st.text_input("Contact", placeholder="Phone or email")
        with col2:
            typical_amount = st.number_input("Typical Monthly Amount", min_value=0, step=50000)
            payment_cycle = st.selectbox("Payment Cycle", ["Monthly", "Bi-weekly", "Weekly", "As needed"])

        notes = st.text_area("Notes", placeholder="Any additional info...")

        if st.form_submit_button("Add Vendor", type="primary"):
            if vendor_name:
                st.success(f"Vendor '{vendor_name}' added! (Database integration coming soon)")
            else:
                st.error("Vendor name is required")

    st.markdown("---")
    st.markdown("### Existing Vendors")
    st.info("Vendor list will appear here once database is connected.")


def show_expenses(db):
    """Enter overhead expenses"""
    st.title("💸 Overhead Expenses")
    st.markdown("---")

    st.markdown("""
    **Simple expense entry - no line items needed:**
    - Select vendor
    - Enter amount
    - Select date
    - Mark as paid or pending
    """)

    st.markdown("---")

    # Add expense form
    st.markdown("### Add New Expense")
    with st.form("add_overhead_expense"):
        col1, col2 = st.columns(2)
        with col1:
            vendor = st.text_input("Vendor *", placeholder="e.g., PLN")
            amount = st.number_input("Amount (Rp) *", min_value=0, step=10000)
        with col2:
            expense_date = st.date_input("Date", value=date.today())
            status = st.selectbox("Status", ["Pending", "Paid"])

        description = st.text_input("Description", placeholder="e.g., January electricity bill")

        if st.form_submit_button("Add Expense", type="primary"):
            if vendor and amount > 0:
                st.success(f"Expense added: {vendor} - {format_currency(amount)} (Database integration coming soon)")
            else:
                st.error("Vendor and amount are required")

    st.markdown("---")
    st.markdown("### Recent Expenses")
    st.info("Expense list will appear here once database is connected.")


def show_payments(db):
    """Track overhead payments"""
    st.title("💳 Overhead Payments")
    st.markdown("---")

    st.markdown("""
    **Track what operational bills need to be paid:**
    - Upcoming payments
    - Mark as paid when done
    - Monthly totals for P&L
    """)

    st.markdown("---")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Paid"])
    with col2:
        filter_month = st.selectbox("Filter by Month", ["All", "This Month", "Last Month"])

    st.markdown("---")
    st.markdown("### Payment List")
    st.info("Payment list will appear here once database is connected.")

    # Summary
    st.markdown("---")
    st.markdown("### Monthly Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Paid", "Coming soon")
    with col2:
        st.metric("Total Pending", "Coming soon")


if __name__ == "__main__":
    main()
