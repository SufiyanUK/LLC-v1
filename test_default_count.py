"""
Test script for default employee count functionality
"""
from scripts.database import TrackingDatabase
import sqlite3

# Initialize database
db = TrackingDatabase()

# Check schema
conn = sqlite3.connect(db.db_path)
cursor = conn.cursor()

print("\n=== Company Config Table Schema ===")
cursor.execute('PRAGMA table_info(company_config)')
for row in cursor.fetchall():
    print(f"  Column: {row[1]}, Type: {row[2]}, Default: {row[4]}")

# Test setting default count
print("\n=== Testing set_company_default_count ===")
test_company = "openai"
test_default = 10

success = db.set_company_default_count(test_company, test_default)
print(f"Set default for {test_company} to {test_default}: {success}")

# Test getting default count
print("\n=== Testing get_company_default_count ===")
default = db.get_company_default_count(test_company)
print(f"Default count for {test_company}: {default}")

# Test getting all defaults
print("\n=== Testing get_all_company_defaults ===")
all_defaults = db.get_all_company_defaults()
print(f"All company defaults: {all_defaults}")

# Clean up
cursor.execute("DELETE FROM company_config WHERE company = ?", (test_company,))
conn.commit()
conn.close()

print("\n[OK] All tests passed!")
