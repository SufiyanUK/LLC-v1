# Critical Bug Fix: Default Count Being Overwritten

## Bug Report

**Issue:** When adding employees to a company that has a custom default count set, the default would reset to 5.

**Example:**
1. Set Neuralink default to 3
2. Add 1 employee to Neuralink
3. Default changes from 3 to 5 ❌
4. Shows wrong employee count

## Root Cause

In `database.py` line 172-177, the `add_employees()` method was using `INSERT OR REPLACE` which **completely replaces** the row in `company_config`, losing the custom `default_employee_count` and applying the schema default of 5.

**Old Code (BROKEN):**
```sql
INSERT OR REPLACE INTO company_config (company, employee_count, last_updated)
VALUES (?,
        (SELECT COALESCE(employee_count, 0) + ? FROM company_config WHERE company = ?),
        ?)
```

**Problem:** This doesn't include `default_employee_count` in the INSERT, so it reverts to schema default (5)

## Fix Applied

**New Code (FIXED):**
```sql
INSERT INTO company_config (company, employee_count, default_employee_count, last_updated)
VALUES (?, ?, 5, ?)
ON CONFLICT(company) DO UPDATE SET
    employee_count = COALESCE(employee_count, 0) + ?,
    last_updated = ?
```

**How it works:**
- If company doesn't exist: Creates with default=5
- If company exists: Only updates `employee_count` and `last_updated`
- **Preserves existing `default_employee_count`** ✅

## Files Changed

1. ✅ `scripts/database.py` line 172-178 (SQLite)
2. ✅ `scripts/database_postgres.py` line 209-217 (PostgreSQL)

## Testing

Run the test to verify:
```bash
python test_default_preservation.py
```

Expected output:
```
1. Setting custom default count to 3...
   Default set to: 3

2. Adding 2 employees to the company...
   Added: 2 employees

3. Checking if default was preserved...
   Default after adding employees: 3
   [OK] SUCCESS: Default was preserved!

4. Adding 1 more employee...
   Added: 1 employees
   Final default: 3
   [OK] SUCCESS: Default still preserved!

[OK] ALL TESTS PASSED - Bug is fixed!
```

## Verification Steps

1. **Restart the API server:**
   ```bash
   # Stop current server (Ctrl+C)
   python api_v2.py
   ```

2. **Test in the UI:**
   - Open http://localhost:8002
   - Find Neuralink (or any company)
   - Set Default to 3
   - Add 1 employee using the "Add:" field
   - Check the default - it should still show "🎯 Default: 3" ✅
   - Check employee count - should be correct

3. **Test auto-refetch with preserved default:**
   - Keep Neuralink default at 3
   - If you have 3 employees, delete 1
   - System should auto-fetch to restore count to 3
   - Default should remain 3 (not change to 5)

## Impact

This was a **critical bug** that:
- ❌ Overwrote user's custom default settings
- ❌ Caused incorrect employee counts displayed
- ❌ Made auto-refetch behavior unpredictable

Now:
- ✅ Custom defaults are preserved when adding employees
- ✅ Employee counts are accurate
- ✅ Auto-refetch works as expected with correct defaults
