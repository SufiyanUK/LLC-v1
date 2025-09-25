"""
Quick fix for company display issues
Ensures all target companies are properly loaded and visible
"""

import sys
import sqlite3
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def fix_companies():
    """Fix company display and database issues"""
    print("FIXING COMPANY DISPLAY ISSUES")
    print("="*50)

    try:
        # Import target companies
        from config.target_companies import TARGET_COMPANIES
        print(f"✓ Loaded {len(TARGET_COMPANIES)} target companies")

        # Connect to database
        conn = sqlite3.connect('data/tracking.db')
        cursor = conn.cursor()

        # Create company_config table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_config (
                company TEXT PRIMARY KEY,
                employee_count INTEGER DEFAULT 5,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Get current companies in database
        cursor.execute('SELECT company FROM company_config')
        db_companies = {row[0].lower() for row in cursor.fetchall()}

        print(f"✓ Found {len(db_companies)} companies in database")

        # Add missing companies
        added = 0
        for company in TARGET_COMPANIES:
            if company.lower() not in db_companies:
                cursor.execute(
                    'INSERT OR REPLACE INTO company_config (company, employee_count) VALUES (?, ?)',
                    (company, 5)
                )
                added += 1
                print(f"  + Added {company}")

        # Fix NULL employee counts
        cursor.execute('UPDATE company_config SET employee_count = 5 WHERE employee_count IS NULL')
        fixed_nulls = cursor.rowcount

        # Commit changes
        conn.commit()

        # Show final status
        cursor.execute('SELECT company, employee_count FROM company_config ORDER BY company')
        all_companies = cursor.fetchall()

        print(f"\n✓ Total companies in database: {len(all_companies)}")
        print(f"✓ Added {added} missing companies")
        print(f"✓ Fixed {fixed_nulls} NULL employee counts")

        print(f"\nFinal company list:")
        for i, (company, count) in enumerate(all_companies, 1):
            print(f"  {i:2d}. {company:<20} ({count or 0} employees)")

        conn.close()

        # Test API import
        try:
            from api_v2 import app
            print(f"\n✓ API successfully imports companies")
        except Exception as e:
            print(f"\n✗ API import error: {e}")

        print(f"\n{'='*50}")
        print("COMPANY FIX COMPLETED!")
        print("="*50)
        print("Now start your server and test:")
        print("  python api_v2.py")
        print("  Then visit: http://localhost:8000/companies")

        return True

    except ImportError as e:
        print(f"✗ Cannot import target companies: {e}")
        print("Check that config/target_companies.py exists")
        return False

    except Exception as e:
        print(f"✗ Database error: {e}")
        print("Check that data/ directory exists and is writable")
        return False

if __name__ == "__main__":
    fix_companies()