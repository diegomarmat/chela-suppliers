"""
Chela Expenses - CAPEX (Capital Expenditures)
Separate page for better performance
"""

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime, date
from models import get_db, init_db

# Page config
st.set_page_config(
    page_title="Chela Expenses - CAPEX",
    page_icon="🔧",
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
    st.sidebar.markdown("### 🔧 CAPEX")
    st.sidebar.markdown(f"**User:** {st.session_state.get('name', 'Unknown')}")
    authenticator.logout(location='sidebar')
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Section",
        ["Overview", "Categories", "Purchases", "Depreciation"]
    )

    # Initialize database
    init_db()
    db = next(get_db())

    try:
        if page == "Overview":
            show_overview(db)
        elif page == "Categories":
            show_categories(db)
        elif page == "Purchases":
            show_purchases(db)
        elif page == "Depreciation":
            show_depreciation(db)
    finally:
        db.close()


def show_overview(db):
    """Overview page"""
    st.title("🔧 Capital Expenditures (CAPEX)")
    st.markdown("---")

    st.info("""
    **What goes here:**
    - Equipment purchases (ovens, fridges, coffee machines)
    - Furniture (tables, chairs, bar stools)
    - Construction/renovations
    - Major repairs (AC units, kitchen hood)
    - Vehicles
    - Technology (POS systems, computers)
    - And other capital investments...
    """)

    st.markdown("### Why track CAPEX separately?")
    st.markdown("""
    - **Not monthly expenses** - one-time or infrequent purchases
    - **Depreciation** - value decreases over time (for accounting)
    - **Investment tracking** - see where money is invested
    - **Tax purposes** - different treatment than operational expenses
    """)

    st.markdown("---")

    # Quick stats placeholder
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total CAPEX (2024)", "Coming soon")
    with col2:
        st.metric("Total CAPEX (2025)", "Coming soon")
    with col3:
        st.metric("YTD (2026)", "Coming soon")


def show_categories(db):
    """Manage CAPEX categories"""
    st.title("📁 CAPEX Categories")
    st.markdown("---")

    st.markdown("""
    **Organize capital expenditures by category:**
    """)

    # Default categories
    categories = [
        ("Kitchen Equipment", "Ovens, fridges, prep tables, etc."),
        ("Bar Equipment", "Coffee machines, blenders, ice makers, etc."),
        ("Furniture", "Tables, chairs, bar stools, sofas"),
        ("Construction", "Renovations, expansions, repairs"),
        ("Technology", "POS systems, computers, cameras"),
        ("Vehicles", "Motorbikes, cars, delivery vehicles"),
        ("Other", "Miscellaneous capital purchases")
    ]

    for name, description in categories:
        with st.expander(f"**{name}**"):
            st.write(description)
            st.caption("Items in this category will appear here")

    st.markdown("---")
    st.markdown("### Add Custom Category")
    with st.form("add_capex_category"):
        col1, col2 = st.columns(2)
        with col1:
            cat_name = st.text_input("Category Name")
        with col2:
            cat_desc = st.text_input("Description")

        if st.form_submit_button("Add Category"):
            if cat_name:
                st.success(f"Category '{cat_name}' added! (Database integration coming soon)")


def show_purchases(db):
    """Enter CAPEX purchases"""
    st.title("🛒 CAPEX Purchases")
    st.markdown("---")

    st.markdown("### Add New Purchase")
    with st.form("add_capex_purchase"):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("Item Name *", placeholder="e.g., Commercial Oven")
            category = st.selectbox("Category", [
                "Kitchen Equipment", "Bar Equipment", "Furniture",
                "Construction", "Technology", "Vehicles", "Other"
            ])
            vendor = st.text_input("Vendor/Supplier", placeholder="Where purchased")

        with col2:
            amount = st.number_input("Amount (Rp) *", min_value=0, step=100000)
            purchase_date = st.date_input("Purchase Date", value=date.today())
            useful_life = st.number_input("Useful Life (years)", min_value=1, max_value=20, value=5)

        description = st.text_area("Description/Notes", placeholder="Brand, model, warranty info, etc.")

        col3, col4 = st.columns(2)
        with col3:
            invoice_number = st.text_input("Invoice Number", placeholder="Optional")
        with col4:
            warranty_until = st.date_input("Warranty Until", value=None)

        if st.form_submit_button("Add Purchase", type="primary"):
            if item_name and amount > 0:
                st.success(f"CAPEX added: {item_name} - {format_currency(amount)} (Database integration coming soon)")
            else:
                st.error("Item name and amount are required")

    st.markdown("---")
    st.markdown("### Recent Purchases")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_category = st.selectbox("Filter by Category", ["All", "Kitchen Equipment", "Bar Equipment", "Furniture", "Construction", "Technology", "Vehicles", "Other"])
    with col2:
        filter_year = st.selectbox("Filter by Year", ["All", "2026", "2025", "2024"])

    st.info("Purchase list will appear here once database is connected.")


def show_depreciation(db):
    """Track depreciation"""
    st.title("📉 Depreciation Tracking")
    st.markdown("---")

    st.markdown("""
    **What is depreciation?**

    Capital assets lose value over time. For accounting purposes, we spread the cost over the asset's useful life.

    **Example:**
    - Bought oven for Rp 50,000,000
    - Useful life: 5 years
    - Annual depreciation: Rp 10,000,000/year
    - After 3 years: Book value = Rp 20,000,000
    """)

    st.markdown("---")

    # Depreciation summary
    st.markdown("### Depreciation Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Asset Value", "Coming soon")
        st.metric("Accumulated Depreciation", "Coming soon")
    with col2:
        st.metric("Net Book Value", "Coming soon")
        st.metric("Annual Depreciation Expense", "Coming soon")

    st.markdown("---")
    st.markdown("### Asset Depreciation Schedule")
    st.info("Depreciation schedule will appear here once database is connected with asset data.")

    st.markdown("---")
    st.caption("Note: Depreciation calculations use straight-line method. Consult with your accountant for tax purposes.")


if __name__ == "__main__":
    main()
