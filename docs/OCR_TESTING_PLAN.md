# OCR Testing Plan - December 22, 2025

**Session:** Diego + Astik with real invoices
**Goal:** Test OCR auto-fill with real supplier invoices and iterate on accuracy

---

## Current OCR Status (December 21, Evening)

### What Works ✅
- **EasyOCR Integration**: Successfully extracts text from invoice photos
- **Multi-strategy Parser**: Tries multiple approaches to find data
- **Basic Auto-fill**: Pre-populates supplier, date, amount, line items
- **Visual Feedback**: Shows what was detected vs not found

### What Needs Work ❌
- **Amount Detection**: Sometimes picks wrong number (e.g., account number instead of total)
- **Line Items**: Not reliably detecting product table rows
- **Format Variations**: Each supplier has different invoice layout

### Test Results So Far

**Test Invoice: Thirst Trap (Dec 19, 2025)**
- Supplier: ✅ Correctly matched "Thirst Trap"
- Date: ✅ Correctly extracted 19/12/2025
- Amount: ❌ Extracted 1,000,000 instead of 4,000,000 (picked line item instead of total)
- Line Items: ❌ Detected 0 items (should be 4 smoothie products)

---

## Strategy: Supplier-Specific Extraction Rules

### The Problem
Every supplier has a different invoice format:
- Some put total at bottom, some at top
- Different table structures
- Different keywords (TOTAL vs JUMLAH vs GRAND TOTAL)
- Handwritten vs printed
- English vs Indonesian

### The Solution
**Each supplier uses the same template every time!**

Instead of one universal parser (impossible), build a library of supplier-specific rules:

1. **First invoice from Supplier A**
   - General parser attempts extraction
   - User corrects mistakes
   - System saves corrections as "rules for Supplier A"

2. **Second invoice from Supplier A**
   - System uses Supplier A's rules
   - Should be near-perfect
   - If still errors, refine the rules

3. **After 2-3 invoices per supplier**
   - System knows each supplier's format perfectly
   - Future invoices: zero corrections needed

### Implementation Plan

**Phase 1: Build Rule Structure (Not started)**
- Add `invoice_parsing_rules` JSON field to Supplier model
- Create correction/learning UI
- Save user corrections as extraction patterns

**Phase 2: Rule Application**
- Check if supplier has custom rules before using general parser
- Apply supplier-specific rules first
- Fallback to general parser if no rules exist

**Phase 3: Rule Library**
- Export/import rules (backup)
- Rule visualization (see what rules exist for each supplier)
- Manual rule editing for advanced users

---

## Tomorrow's Testing Agenda

### Preparation
- [ ] Have Astik bring 5-10 different supplier invoices (photos on phone or printed)
- [ ] Prepare notebook to document which suppliers work/don't work
- [ ] Make sure app is running and accessible

### Testing Process

**For each invoice:**
1. **Upload photo** via OCR section
2. **Review extracted data**:
   - Supplier match? (correct/wrong/not found)
   - Date extraction? (correct/wrong/not found)
   - Amount extraction? (correct/wrong/picked wrong number)
   - Line items? (correct/partial/none)
3. **Document results** in testing notes
4. **Manually correct** and save invoice
5. **Identify patterns** for that supplier's format

**After testing 5-10 invoices:**
- Analyze common failure patterns
- Decide which suppliers need custom rules first
- Prioritize improvements based on invoice volume

### Questions to Answer
- Which suppliers have most invoices per month? (prioritize those)
- Which formats are most common? (Indonesian vs English, handwritten vs printed)
- What's the acceptable accuracy threshold? (80%? 90%?)
- Should we implement supplier rules now or wait for more data?

---

## Technical Notes

### Current Parser Logic

**Supplier Matching:**
- Scans entire OCR text for supplier name match
- Checks both `short_name` and `company_name`
- Fuzzy matching: 60% word match threshold
- **Issue:** Needs supplier already in database

**Date Extraction:**
- Regex patterns: `DD/MM/YYYY` or `DD-MM-YYYY`
- Skips lines with ACCOUNT/PHONE to avoid false positives
- Year sanity check: 2020-2030
- **Issue:** Sometimes extracts date from wrong field

**Amount Extraction (Priority System):**
- +100 points: Lines with "TOTAL AMOUNT", "GRAND TOTAL", "JUMLAH"
- +50 points: Amounts in last 30% of document
- +10 points: Larger amounts (usually total > line items)
- Filters: Ignore < 5,000 (too small) and > 999,999,999 (account numbers)
- Skips lines with: ACCOUNT, BANK, PHONE, TELP
- **Issue:** Priority system not tuned correctly

**Line Items Detection:**
- Looks for table after headers (DESCRIPTION, QTY, PRODUCT)
- Stops at TOTAL/SUBTOTAL lines
- Requires 2+ numbers per line (qty + price)
- Sanity checks: qty 1-10,000, price 1-10M
- Unit detection: KG, LITER, PCS, PACK, etc.
- **Issue:** Not matching actual table rows correctly

### Files Modified Today
- `/Users/diegomarmat/Chela/suppliers/src/app.py` - Main app with OCR parser
- `/Users/diegomarmat/Chela/suppliers/src/requirements.txt` - Added EasyOCR, Pillow 9.5.0
- `/Users/diegomarmat/Chela/suppliers/README.md` - Updated docs

### Known Issues
1. **Pillow version**: Must use 9.5.0 (not 10.x) for EasyOCR compatibility
2. **First OCR run**: Downloads models (2-3 min wait)
3. **Port conflict**: Sometimes need to kill previous Streamlit process
4. **Line item parsing**: Too strict, missing actual table rows

---

## Cost Analysis: MVP vs API

### Option A: Supplier-Specific Rules (Current Plan)
- **Cost:** $0 (free)
- **Effort:** High initial setup (~2-3 invoices per supplier to learn)
- **Accuracy:** Very high after learning (95%+)
- **Scalability:** Requires one-time setup per new supplier

### Option B: Claude API Integration
- **Cost:** ~$0.01-0.05 per invoice = $10-50/month (1000 invoices)
- **Effort:** Low (integrate API once, works immediately)
- **Accuracy:** High from day 1 (90%+)
- **Scalability:** Zero setup for new suppliers

### Decision: Start with Option A (Free MVP)
- Test with real invoices first
- If accuracy is too low or effort too high, switch to API
- With ~10-20 regular suppliers, one-time learning is reasonable
- Can always add API later as premium feature

---

## Success Metrics

**MVP Success = 70%+ accuracy across all suppliers**
- Supplier match: 90%+ (easy, just need supplier in database)
- Date extraction: 85%+ (fairly reliable)
- Amount extraction: 70%+ (challenging, many edge cases)
- Line items: 50%+ (most complex, optional for MVP)

**If we achieve:**
- 70-80% accuracy → MVP is viable, continue refining
- 50-70% accuracy → Consider supplier-specific rules immediately
- <50% accuracy → May need Claude API for acceptable UX

---

## Next Session Checklist

- [ ] App running on port 8503
- [ ] Database backed up
- [ ] Test invoices ready
- [ ] Notebook for documenting results
- [ ] This doc printed/open for reference

**Remember:** This is iterative! Don't expect perfection day 1. Goal is to learn what works and what doesn't with real data.
