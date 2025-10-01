"""
Test that default_employee_count is preserved when adding employees
This was the bug: default would reset to 5 when adding employees
"""
from scripts.database import TrackingDatabase
from datetime import datetime

print("\n" + "="*60)
print("TEST: Default Count Preservation When Adding Employees")
print("="*60)

db = TrackingDatabase()
test_company = "test_preserve_default"

# Step 1: Set a custom default (not 5)
print("\n1. Setting custom default count to 3...")
db.set_company_default_count(test_company, 3)
default = db.get_company_default_count(test_company)
print(f"   Default set to: {default}")
assert default == 3, f"Expected 3, got {default}"

# Step 2: Add some employees
print("\n2. Adding 2 employees to the company...")
fake_employees = [
    {
        'id': 'test_emp_1',
        'full_name': 'Test Employee 1',
        'job_title': 'Engineer',
        'job_company_name': test_company
    },
    {
        'id': 'test_emp_2',
        'full_name': 'Test Employee 2',
        'job_title': 'Manager',
        'job_company_name': test_company
    }
]

added, updated = db.add_employees(fake_employees, test_company)
print(f"   Added: {added} employees")

# Step 3: Check if default was preserved
print("\n3. Checking if default was preserved...")
default_after = db.get_company_default_count(test_company)
print(f"   Default after adding employees: {default_after}")

if default_after == 3:
    print("   [OK] SUCCESS: Default was preserved!")
else:
    print(f"   [FAIL] Default changed from 3 to {default_after}")

# Step 4: Add more employees and check again
print("\n4. Adding 1 more employee...")
more_employees = [
    {
        'id': 'test_emp_3',
        'full_name': 'Test Employee 3',
        'job_title': 'Designer',
        'job_company_name': test_company
    }
]

added, updated = db.add_employees(more_employees, test_company)
print(f"   Added: {added} employees")

default_final = db.get_company_default_count(test_company)
print(f"   Final default: {default_final}")

if default_final == 3:
    print("   [OK] SUCCESS: Default still preserved!")
else:
    print(f"   [FAIL] Default changed from 3 to {default_final}")

# Cleanup
import sqlite3
conn = sqlite3.connect(db.db_path)
cursor = conn.cursor()
cursor.execute("DELETE FROM tracked_employees WHERE company = ?", (test_company,))
cursor.execute("DELETE FROM company_config WHERE company = ?", (test_company,))
conn.commit()
conn.close()

print("\n" + "="*60)
if default_after == 3 and default_final == 3:
    print("[OK] ALL TESTS PASSED - Bug is fixed!")
else:
    print("[FAIL] TESTS FAILED - Bug still exists")
print("="*60)
