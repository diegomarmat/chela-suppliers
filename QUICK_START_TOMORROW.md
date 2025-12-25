# Quick Start - December 22, 2025 Session

**For:** Diego + Astik OCR Testing Session

---

## 1. Start the App (3 commands)

```bash
# Navigate to project
cd /Users/diegomarmat/Chela/suppliers/src

# Activate environment
source venv/bin/activate

# Run app
streamlit run app.py --server.port=8503
```

**App will open at:** http://localhost:8503

---

## 2. Before Testing - Add Suppliers

Make sure all suppliers that will be tested are already in the database:

1. Go to **Suppliers** page → **Add Supplier** tab
2. Add each supplier you'll test (just need short name and company name minimum)
3. Payment terms can be cash/2week/monthly (affects due date calculation)

**Why?** OCR can only match suppliers that exist in database.

---

## 3. Testing Process

### For Each Invoice:

1. **Go to Invoices → Add Invoice tab**

2. **Upload invoice photo**
   - Use "Upload invoice photo" section at top
   - Click "Extract Text (OCR)"
   - Wait 10-20 seconds (first time: 2-3 min for model download)

3. **Review auto-filled data**
   - Check the colored boxes showing what was detected
   - Green ✅ = Correct
   - Yellow ⚠️ = Wrong or not found

4. **Correct and save**
   - Fix any wrong fields manually
   - Add line items if needed
   - Click "Save Invoice"

5. **Document results** (see testing plan doc)

---

## 4. What to Bring

- **5-10 invoice photos** from different suppliers
- Mix of:
  - High volume suppliers (test those first)
  - Different formats (handwritten vs printed)
  - Different languages (English vs Indonesian)

---

## 5. Current Known Issues

**Amount Detection:**
- Sometimes picks account number instead of total
- Watch out for this, will need correction

**Line Items:**
- Not reliably detecting table rows yet
- May need to add items manually for now

**Supplier Matching:**
- Only works if supplier already in database
- Add suppliers before testing their invoices

---

## 6. Quick Reference

**Stop App:**
```bash
pkill -f "streamlit run app.py"
```

**Restart App:**
```bash
cd /Users/diegomarmat/Chela/suppliers/src
source venv/bin/activate
streamlit run app.py --server.port=8503
```

**Check Database:**
```bash
cd /Users/diegomarmat/Chela/suppliers/data
sqlite3 suppliers.db
```

---

## 7. Documents to Reference

- **Testing Plan:** `/Users/diegomarmat/Chela/suppliers/docs/OCR_TESTING_PLAN.md`
- **Full README:** `/Users/diegomarmat/Chela/suppliers/README.md`
- **Main Project Docs:** `/Users/diegomarmat/Chela/CLAUDE.md`

---

## 8. Goals for Session

**Primary:**
- Test OCR with 5-10 real invoices
- Document what works / what doesn't
- Understand which suppliers need custom rules

**Secondary:**
- Decide if supplier-specific rules are needed now
- Identify most common failure patterns
- Prioritize improvements for next session

**Success = Learn what needs fixing, not achieve perfection!**
