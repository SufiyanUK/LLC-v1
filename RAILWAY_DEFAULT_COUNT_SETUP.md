# Railway Deployment: Default Employee Count Feature

## Overview

This guide ensures the default employee count feature works correctly when deploying to Railway with PostgreSQL.

## ✅ What's Been Done

### 1. PostgreSQL Implementation (Complete)
- ✅ `database_postgres.py` has all default count methods
- ✅ Schema includes `default_employee_count INTEGER DEFAULT 5`
- ✅ `add_employees()` preserves default count (bug fixed)
- ✅ Auto-migration on startup

### 2. SQLite Implementation (Complete)
- ✅ Fully implemented and tested locally
- ✅ All features working

## 🚀 Deployment Options

You have **TWO OPTIONS** for Railway deployment:

---

## Option 1: Automatic Migration (Recommended)

**Best for:** Existing Railway deployments

The system will **automatically migrate** your database when you deploy!

### Steps:

1. **Push your code to Railway:**
   ```bash
   git add .
   git commit -m "Add default employee count feature"
   git push
   ```

2. **Railway automatically deploys**

3. **On first startup**, `database_postgres.py` will:
   - Check if `default_employee_count` column exists
   - If missing, automatically add it with `ALTER TABLE`
   - Set default value to 5 for all existing companies
   - Print migration status to logs

4. **Verify in Railway logs:**
   ```
   [MIGRATION] Adding default_employee_count column to company_config table...
   [MIGRATION] Column added successfully!
   ```

**That's it!** No manual steps needed.

---

## Option 2: Manual Migration Script

**Best for:** Manual control or troubleshooting

### Steps:

1. **Deploy your code to Railway**

2. **Run migration script in Railway console:**
   - Open your Railway project
   - Go to your service → **"Console"** tab
   - Run:
     ```bash
     python migrate_railway_default_count.py
     ```

3. **Expected output:**
   ```
   ============================================================
   RAILWAY MIGRATION: Add default_employee_count Column
   ============================================================

   [INFO] Connecting to database...
   [OK] Connected to [hostname]/[database]
   [OK] company_config table found
   [MIGRATION] Adding default_employee_count column...
   [OK] Column added successfully!

   Updated company_config schema:
     - company (text) DEFAULT None
     - employee_count (integer) DEFAULT None
     - default_employee_count (integer) DEFAULT 5
     - last_updated (timestamp) DEFAULT CURRENT_TIMESTAMP

   [SUCCESS] Migration completed successfully!
   ```

4. **Restart your Railway service**

---

## 🆕 Fresh Railway Deployment

**If deploying for the first time:**

1. **Push your code to Railway**
2. **The database will be created with the correct schema automatically**
3. **No migration needed** - the column is included from the start

---

## ✅ Verification

After deployment, verify the feature works:

1. **Open your Railway app URL**

2. **Check a company card:**
   - You should see "🎯 Default: 5" (or custom value)
   - "Default:" input field is present

3. **Test setting a default:**
   - Set a company default to 3
   - Add an employee
   - Default should remain 3 (not change to 5)

4. **Test auto-refetch:**
   - Set company default to 5
   - Add 5 employees
   - Delete 1 employee
   - System auto-fetches 1 to restore count to 5

---

## 🔍 Troubleshooting

### Issue: Column doesn't exist error

**Symptoms:**
```
column "default_employee_count" does not exist
```

**Solution:**
Run the manual migration script:
```bash
python migrate_railway_default_count.py
```

### Issue: Auto-migration didn't run

**Check Railway logs:**
```bash
railway logs
```

Look for:
```
[MIGRATION] Adding default_employee_count column...
```

**If not present:**
- Run manual migration script
- Or redeploy to trigger auto-migration again

### Issue: Default count shows 5 instead of custom value

**This was the bug we fixed!**

**Verify fix is deployed:**
1. Check `database_postgres.py` line 209-217
2. Should have `ON CONFLICT (company) DO UPDATE SET`
3. Should NOT overwrite `default_employee_count`

---

## 📊 Database Schema

After successful migration:

```sql
CREATE TABLE company_config (
    company TEXT PRIMARY KEY,
    employee_count INTEGER,
    default_employee_count INTEGER DEFAULT 5,  -- NEW COLUMN
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 Migration Safety

The migration is **100% safe**:

- ✅ Uses `ALTER TABLE ADD COLUMN IF NOT EXISTS` logic
- ✅ Won't fail if column already exists
- ✅ Doesn't modify existing data
- ✅ Sets sensible default (5) for all companies
- ✅ No downtime required
- ✅ Reversible (can drop column if needed)

---

## 📝 Summary

| Scenario | Action Required |
|----------|----------------|
| **New Railway deployment** | None - automatic |
| **Existing Railway deployment** | None - auto-migration on deploy |
| **Auto-migration fails** | Run manual script |
| **Want manual control** | Use manual migration script |

---

## 🎯 Next Steps After Deployment

1. ✅ Set default counts for your key companies
2. ✅ Test auto-refetch with different defaults
3. ✅ Set some companies to 0 to disable auto-refetch
4. ✅ Enjoy automated employee tracking!

---

## 📞 Support

If you encounter issues:

1. Check Railway logs: `railway logs`
2. Run diagnostic: `python diagnose_db.py` (after downloading DB)
3. Manual migration: `python migrate_railway_default_count.py`

Everything is set up to work automatically! 🚀
