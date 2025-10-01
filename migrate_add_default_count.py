"""
Migration script to add default_employee_count column to company_config table
"""
import sqlite3
from pathlib import Path

# Path to database
db_path = Path(__file__).parent / 'data' / 'tracking.db'

print(f"Migrating database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute('PRAGMA table_info(company_config)')
    columns = [row[1] for row in cursor.fetchall()]

    if 'default_employee_count' in columns:
        print("[OK] Column 'default_employee_count' already exists")
    else:
        print("Adding 'default_employee_count' column...")
        cursor.execute("""
            ALTER TABLE company_config
            ADD COLUMN default_employee_count INTEGER DEFAULT 5
        """)
        conn.commit()
        print("[OK] Successfully added 'default_employee_count' column")

    # Verify the change
    cursor.execute('PRAGMA table_info(company_config)')
    print("\n=== Updated Company Config Table Schema ===")
    for row in cursor.fetchall():
        print(f"  Column: {row[1]}, Type: {row[2]}, Default: {row[4]}")

    print("\n[OK] Migration completed successfully!")

except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
