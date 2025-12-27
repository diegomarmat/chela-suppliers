# Alembic Database Migrations Guide

## What is Alembic?

Alembic is a database migration tool that allows you to **change your database schema WITHOUT losing data**.

**Before Alembic (what we did today):**
- Add a field → Drop table → Recreate → **ALL DATA LOST** ❌

**With Alembic (from now on):**
- Add a field → Run migration → **ALL DATA PRESERVED** ✅

---

## How to Make Schema Changes (Step-by-Step)

### Example: Adding a new field to Supplier model

**Step 1: Edit the model in `models.py`**

```python
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, nullable=False)
    # ... existing fields ...

    # NEW FIELD - Add this line:
    supplier_rating = Column(Integer)  # 1-5 star rating
```

**Step 2: Generate migration**

```bash
cd /Users/diegomarmat/Chela/suppliers/src
source venv/bin/activate
alembic revision --autogenerate -m "Add supplier_rating field"
```

This creates a migration file in `alembic/versions/` like:
```
xxxxx_add_supplier_rating_field.py
```

**Step 3: Review the migration**

Open the generated file and verify it looks correct:
```python
def upgrade() -> None:
    op.add_column('suppliers', sa.Column('supplier_rating', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('suppliers', 'supplier_rating')
```

**Step 4: Apply migration LOCALLY first**

```bash
alembic upgrade head
```

This adds the new column to your local database. **All existing data is preserved!**

**Step 5: Test locally**

- Run the app: `streamlit run app.py`
- Verify everything works
- Check that existing suppliers still have all their data

**Step 6: Deploy to production (Railway)**

```bash
git add .
git commit -m "Add supplier_rating field"
git push origin main
```

Railway deploys the new code. The migration runs automatically on startup (or you run it manually).

**Step 7: Apply migration on Railway**

Option A - Automatic (recommended for future):
- Add migration to app startup (we can set this up)

Option B - Manual:
- SSH into Railway or use Railway CLI
- Run: `alembic upgrade head`

---

## Common Migration Scenarios

### Adding a Field

**models.py:**
```python
new_field = Column(String)
```

**Command:**
```bash
alembic revision --autogenerate -m "Add new_field"
alembic upgrade head
```

### Renaming a Field

**models.py:**
```python
# Before: old_name = Column(String)
# After: new_name = Column(String)
```

**Manual migration needed** (autogenerate can't detect renames):
```bash
alembic revision -m "Rename old_name to new_name"
```

Edit the migration file:
```python
def upgrade():
    op.alter_column('table_name', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('table_name', 'new_name', new_column_name='old_name')
```

### Changing Field Type

**models.py:**
```python
# Before: price = Column(Integer)
# After: price = Column(Float)
```

**Command:**
```bash
alembic revision --autogenerate -m "Change price to Float"
alembic upgrade head
```

### Removing a Field

**models.py:**
```python
# Delete or comment out the field
# old_field = Column(String)
```

**Command:**
```bash
alembic revision --autogenerate -m "Remove old_field"
alembic upgrade head
```

---

## Important Commands

### Check current database version
```bash
alembic current
```

### See migration history
```bash
alembic history
```

### Upgrade to latest
```bash
alembic upgrade head
```

### Downgrade one version (undo last migration)
```bash
alembic downgrade -1
```

### Downgrade to specific version
```bash
alembic downgrade <revision_id>
```

---

## Testing Migrations

**Always test locally first!**

1. Make your model change
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Apply locally: `alembic upgrade head`
4. Test the app thoroughly
5. If it works → deploy to production
6. If it fails → downgrade: `alembic downgrade -1`

---

## Migration Files Location

**Migrations are stored in:**
```
/Users/diegomarmat/Chela/suppliers/src/alembic/versions/
```

Each migration is a Python file with:
- `upgrade()` - How to apply the change
- `downgrade()` - How to undo the change

**These files are committed to git** so Railway knows what migrations to run.

---

## What Happens on Railway Deployment

**Current setup (manual):**
1. Code deploys
2. You manually run `alembic upgrade head` on Railway

**Future setup (automatic):**
We can add to `app.py`:
```python
from alembic import command
from alembic.config import Config

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

# Run on app startup
run_migrations()
init_db()
```

---

## Key Principles

✅ **DO:**
- Always test migrations locally first
- Review generated migrations before applying
- Commit migration files to git
- Keep migrations small and focused

❌ **DON'T:**
- Don't edit old migration files (create new ones)
- Don't skip migrations (run them in order)
- Don't delete migration files
- Don't run untested migrations on production

---

## Summary

**Before (Today):**
```
Change model → Drop tables → Lose data ❌
```

**Now (With Alembic):**
```
Change model → Generate migration → Apply migration → Keep all data ✅
```

**When you have 300 products and need to add a field:**
```bash
# 1. Edit models.py
# 2. Generate migration
alembic revision --autogenerate -m "Add new field"
# 3. Apply locally
alembic upgrade head
# 4. Test
# 5. Deploy
git push
# 6. Apply on Railway
alembic upgrade head
```

**Result:** 300 products preserved, new field added. Zero data loss. 🎉
