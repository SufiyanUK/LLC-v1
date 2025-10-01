"""
Diagnostic script to check database state and data
"""
from scripts.database import TrackingDatabase
import sqlite3

print("\n" + "="*60)
print("DATABASE DIAGNOSTIC REPORT")
print("="*60)

# Initialize database
db = TrackingDatabase()

# Connect directly to check
conn = sqlite3.connect(db.db_path)
cursor = conn.cursor()

# Check tables exist
print("\n1. CHECKING TABLES...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"   Found {len(tables)} tables:")
for table in tables:
    print(f"   - {table[0]}")

# Check tracked_employees table
print("\n2. CHECKING TRACKED_EMPLOYEES...")
cursor.execute("SELECT COUNT(*) FROM tracked_employees")
total_employees = cursor.fetchone()[0]
print(f"   Total employees: {total_employees}")

cursor.execute("SELECT status, COUNT(*) FROM tracked_employees GROUP BY status")
status_counts = cursor.fetchall()
print("   By status:")
for status, count in status_counts:
    print(f"   - {status}: {count}")

# Check company_config table
print("\n3. CHECKING COMPANY_CONFIG...")
cursor.execute("SELECT COUNT(*) FROM company_config")
total_companies = cursor.fetchone()[0]
print(f"   Total companies in config: {total_companies}")

cursor.execute("SELECT company, employee_count, default_employee_count FROM company_config")
companies = cursor.fetchall()
print("   Companies:")
for company, emp_count, default in companies:
    print(f"   - {company}: employees={emp_count}, default={default}")

# Test the database methods
print("\n4. TESTING DATABASE METHODS...")
print("   Testing get_all_employees()...")
employees = db.get_all_employees()
print(f"   Returned {len(employees)} employees")

print("\n   Testing get_company_employee_counts()...")
counts = db.get_company_employee_counts()
print(f"   Returned counts for {len(counts)} companies:")
for company, count in counts.items():
    print(f"   - {company}: {count}")

print("\n   Testing get_all_company_defaults()...")
defaults = db.get_all_company_defaults()
print(f"   Returned defaults for {len(defaults)} companies:")
for company, default in defaults.items():
    print(f"   - {company}: {default}")

# Check if there are any employees with actual data
print("\n5. SAMPLE EMPLOYEE DATA...")
cursor.execute("SELECT name, company, title, status FROM tracked_employees LIMIT 5")
sample_employees = cursor.fetchall()
if sample_employees:
    print("   First 5 employees:")
    for name, company, title, status in sample_employees:
        print(f"   - {name} at {company} ({status})")
else:
    print("   [WARNING] No employee data found!")

conn.close()

print("\n" + "="*60)
print("END OF DIAGNOSTIC REPORT")
print("="*60)
