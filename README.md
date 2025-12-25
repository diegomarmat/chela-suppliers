# Chela Suppliers Management System

**Status:** 🚧 OCR Testing Phase - Ready for Real Invoices
**Created:** December 21, 2025
**Last Updated:** December 21, 2025 (Evening)
**For:** Astik (Purchasing/Admin) + Diego

---

## What This Does

This system helps Astik manage suppliers, invoices, and payments for Chela. It replaces manual spreadsheets and makes it easy to:

- **Track Suppliers**: Store all supplier information (contacts, payment terms, bank details)
- **Enter Invoices**: Manually enter invoices (OCR scanning coming later!)
- **Manage Payments**: See what's due, mark invoices as paid
- **Generate Reports**: Monthly payment summaries, supplier spend analysis

---

## How to Run the App

### 1. Navigate to the project folder
```bash
cd /Users/diegomarmat/Chela/suppliers/src
```

### 2. Activate the virtual environment
```bash
source venv/bin/activate
```

### 3. Run the Streamlit app
```bash
streamlit run app.py
```

### 4. Open in your browser
The app will automatically open at: **http://localhost:8501**

---

## Main Features (MVP)

### ✅ Dashboard
- Quick overview: Active suppliers, total invoices, pending payments
- Recent invoices list
- Summary statistics

### ✅ Suppliers
- **View Suppliers**: See all active suppliers with contact info
- **Add Supplier**: Add new suppliers with payment terms (cash, 2-week, monthly)
- Stores: Name, contact person, phone, email, payment terms, bank details

### 🚧 Invoices (OCR Testing)
- **View Invoices**: Filter by status (pending/paid) and supplier
- **Add Invoice** - Two methods:
  - **📸 OCR Scanning**: Upload invoice photo → auto-extract data (TESTING)
  - **✍️ Manual Entry**: Type in invoice details
- **Auto-fill from OCR**: Extracts supplier, date, amount, line items
- **Payment Terms**: Auto-calculates due date based on supplier settings
- **Line Items**: Add products with quantity, unit, price (for delivery control)

### ✅ Payments
- **Pending Payments**: See all unpending invoices with due dates
- **Mark as Paid**: Mark invoices as paid with payment date and method
- Shows "OVERDUE" for late payments

### ✅ Reports
- **Monthly Payment Summary**: See total invoices per supplier for any month
- **Supplier Spend Analysis**: Total spend per supplier (all time)

---

## Database Structure

**Location:** `/Users/diegomarmat/Chela/suppliers/data/suppliers.db`

**Tables:**
1. `suppliers` - Supplier information
2. `invoices` - Invoice headers (supplier, date, total, status)
3. `invoice_items` - Line items (ready for product tracking)
4. `products` - Product catalog (builds automatically over time)
5. `price_history` - Price tracking (for analytics later)

---

## Payment Terms Logic

The system auto-calculates due dates based on supplier payment terms and invoice date:

- **Cash**: Due same day (due date = invoice date)
- **2-week**: Month split in half
  - Invoice before 15th → Pay on 15th
  - Invoice on/after 15th → Pay end of month
- **Monthly**: Pay end of month for all invoices from that month

Example: Invoice dated Dec 10 with "2-week" terms → Due Dec 15
Example: Invoice dated Dec 20 with "2-week" terms → Due Dec 31

---

## OCR Strategy: Supplier-Specific Extraction Rules

**Key Insight:** Each supplier uses the same invoice template every time!

**Approach for MVP (FREE, no API costs):**
1. **First invoice from supplier** → General OCR parser tries to extract data
2. **User corrects** any mistakes in the auto-filled form
3. **System learns** and saves extraction rules for that supplier
4. **Future invoices** → Use supplier-specific rules (near-perfect accuracy)

**Benefits:**
- Zero API costs (vs $10-50/month for 1000 invoices)
- Accuracy improves over time
- After 2-3 invoices per supplier, system knows their format perfectly
- With ~10-20 regular suppliers, one-time setup effort

**Tomorrow's Plan with Astik:**
- Upload real invoices from different suppliers
- Test current general parser
- Start building supplier-specific rule library
- Iterate until accurate

---

## What's Next (Future Updates)

### Phase 1: OCR Refinement (IN PROGRESS)
- [x] Basic OCR text extraction (EasyOCR)
- [x] General multi-strategy parser (supplier, date, amount, items)
- [ ] **Supplier-specific extraction rules (NEXT STEP)**
- [ ] Correction UI → Save as rules
- [ ] Rule library management per supplier
- [ ] Batch invoice upload

### Phase 2: Advanced Analytics
- [ ] Price trend tracking (is chicken getting more expensive?)
- [ ] Order pattern detection (waste/theft alerts)
- [ ] Delivery control (ordered vs received tracking)
- [ ] Price comparison across suppliers
- [ ] Product catalog insights

### Phase 3: Integration
- [ ] Connect to Recipe costing (ingredient prices → dish costs)
- [ ] Cross-reference with Sales (revenue vs costs)
- [ ] Profit optimization dashboard
- [ ] Ingredient cost alerts

### Phase 4: Production (Next.js)
- [ ] Professional web interface
- [ ] Mobile-responsive design
- [ ] Role-based access control (Astik vs Diego access)
- [ ] Advanced reporting & exports
- [ ] Mobile app for invoice scanning

---

## For Astik - Testing Instructions

### Step 1: Add a Test Supplier
1. Go to **Suppliers** → **Add Supplier** tab
2. Fill in:
   - Supplier Name: "Bali Fresh Produce" (or any real supplier)
   - Contact Person: "Made Wirawan"
   - Phone: "812 3456 7890"
   - Payment Terms: Select "monthly"
3. Click **Add Supplier**

### Step 2: Add a Test Invoice
1. Go to **Invoices** → **Add Invoice** tab
2. Fill in:
   - Select the supplier you just created
   - Invoice Number: "INV-001"
   - Invoice Date: Today's date
   - Total Amount: 5000000 (5 million IDR)
3. Click **Save Invoice**

### Step 3: Check Payments
1. Go to **Payments** → **Pending Payments** tab
2. You should see the invoice you just added
3. Go to **Mark as Paid** tab
4. Select the invoice and mark it as paid

### Step 4: View Reports
1. Go to **Reports** → **Monthly Payment Summary**
2. Select current month - you should see your test invoice
3. Go to **Supplier Spend Analysis** - you should see total spend per supplier

---

## Troubleshooting

**App won't start?**
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Check you're in the right folder: `cd /Users/diegomarmat/Chela/suppliers/src`

**Can't add supplier/invoice?**
- Check that all required fields (marked with *) are filled
- Make sure total amount is greater than 0

**Database issues?**
- Database is at: `/Users/diegomarmat/Chela/suppliers/data/suppliers.db`
- To reset database: Delete the file and re-run the app (it will recreate)

---

## Files Overview

```
/Users/diegomarmat/Chela/suppliers/
├── src/
│   ├── app.py              # Main Streamlit application
│   ├── models.py           # Database models (SQLAlchemy)
│   ├── init_schema.sql     # Database schema definition
│   ├── requirements.txt    # Python dependencies
│   └── venv/               # Virtual environment
├── data/
│   └── suppliers.db        # SQLite database
├── invoices/               # Stored invoice photos (coming soon)
├── docs/                   # Documentation
└── README.md              # This file
```

---

## Contact

**Questions?** Ask Diego!
**Issues?** Report to Diego!
**Ideas?** Tell Diego!

---

## Version History

- **v1.1 (Dec 21, 2025 Evening)**: OCR Testing Phase
  - Added EasyOCR invoice photo scanning
  - Multi-strategy parser (supplier, date, amount, line items)
  - Auto-fill invoice form from OCR data
  - Ready for real invoice testing with Astik

- **v1.0 (Dec 21, 2025 Morning)**: MVP Launch
  - Basic supplier/invoice/payment management
  - Payment terms automation (cash/2-week/monthly)
  - Dashboard and reports
