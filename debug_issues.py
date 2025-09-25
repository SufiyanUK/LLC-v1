"""
Debug script for company display and PDL API issues
This script diagnoses and fixes common problems with the employee tracking system
"""

import os
import sys
import json
import requests
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_company_display():
    """Test company display functionality"""
    print("="*60)
    print("COMPANY DISPLAY DIAGNOSIS")
    print("="*60)

    try:
        # Test import of company config
        from config.target_companies import TARGET_COMPANIES
        print(f"✓ Target companies loaded: {len(TARGET_COMPANIES)} companies")
        print("Companies configured:")
        for i, company in enumerate(TARGET_COMPANIES, 1):
            print(f"  {i:2d}. {company}")
    except ImportError as e:
        print(f"✗ Failed to import TARGET_COMPANIES: {e}")
        return False

    # Test database companies
    try:
        conn = sqlite3.connect('data/tracking.db')
        cursor = conn.cursor()
        cursor.execute('SELECT company, employee_count, last_updated FROM company_config ORDER BY company')
        db_companies = cursor.fetchall()
        conn.close()

        print(f"\n✓ Database companies: {len(db_companies)} companies")
        print("Companies in database:")
        for i, (company, count, updated) in enumerate(db_companies, 1):
            status = f"{count} employees" if count else "0 employees"
            print(f"  {i:2d}. {company:<20} | {status}")

    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

    # Test API endpoint
    try:
        from api_v2 import app
        print(f"\n✓ API app loaded successfully")
        print(f"  Title: {app.title}")
        print(f"  Version: {app.version}")
    except Exception as e:
        print(f"✗ API import failed: {e}")
        return False

    return True

def test_pdl_api():
    """Test PDL API connectivity and configuration"""
    print("\n" + "="*60)
    print("PDL API DIAGNOSIS")
    print("="*60)

    # Check environment variables
    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        print("✗ No API_KEY found in .env file")
        print("Please check your .env file contains:")
        print("API_KEY=your_pdl_api_key_here")
        return False

    print(f"✓ API key found: {api_key[:20]}...{api_key[-8:]}")

    # Test PDL API connection
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    # Simple test query
    test_query = {
        'sql': 'SELECT * FROM person WHERE job_company_name = "openai" LIMIT 1',
        'size': 1
    }

    try:
        print("\n🔍 Testing PDL API connection...")
        response = requests.post(
            'https://api.peopledatalabs.com/v5/person/search',
            headers=headers,
            json=test_query,
            timeout=30
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            records = data.get('data', [])
            print(f"✓ PDL API working! Found {len(records)} test records")

            # Show available credits
            if 'scroll_token' in data:
                print("✓ Scroll token available for pagination")

            return True

        elif response.status_code == 401:
            print("✗ Authentication failed - API key invalid")
            error_data = response.json()
            print(f"Error: {error_data.get('error', {}).get('message', 'Unknown')}")
            return False

        elif response.status_code == 402:
            print("✗ Payment required - no credits remaining")
            error_data = response.json()
            print(f"Error: {error_data.get('error', {}).get('message', 'Unknown')}")
            return False

        elif response.status_code == 429:
            print("✗ Rate limited - too many requests")
            print("Wait a few minutes and try again")
            return False

        else:
            print(f"✗ PDL API error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response text: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("✗ Request timeout - PDL API took too long to respond")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error - could not connect to PDL API")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_employee_tracker():
    """Test the EmployeeTracker class functionality"""
    print("\n" + "="*60)
    print("EMPLOYEE TRACKER DIAGNOSIS")
    print("="*60)

    try:
        from scripts.employee_tracker import EmployeeTracker
        print("✓ EmployeeTracker imported successfully")

        tracker = EmployeeTracker()
        print("✓ EmployeeTracker instance created")

        # Test database connection
        stats = tracker.db.get_statistics()
        print(f"✓ Database connected")
        print(f"  Total employees: {stats.get('total_employees', 0)}")
        print(f"  Companies: {stats.get('companies_tracked', 0)}")

        # Test getting existing employees for a company
        existing_ids = tracker.get_existing_employee_ids('openai')
        print(f"✓ Existing OpenAI employees: {len(existing_ids)}")

        return True

    except Exception as e:
        print(f"✗ EmployeeTracker error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_pdl_fetch():
    """Test a simple PDL fetch for debugging"""
    print("\n" + "="*60)
    print("SIMPLE PDL FETCH TEST")
    print("="*60)

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        print("✗ No API key available")
        return False

    # Test with a known company
    test_company = 'openai'

    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    # Simple query for senior roles at OpenAI
    query = {
        'sql': f"""
        SELECT * FROM person
        WHERE job_company_name = '{test_company}'
        AND job_title_levels IN ('director', 'vp', 'senior', 'lead', 'principal')
        """.strip(),
        'size': 3
    }

    try:
        print(f"Testing fetch from {test_company}...")
        response = requests.post(
            'https://api.peopledatalabs.com/v5/person/search',
            headers=headers,
            json=query,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            employees = data.get('data', [])
            print(f"✓ Found {len(employees)} employees")

            for i, emp in enumerate(employees, 1):
                name = emp.get('full_name', 'Unknown')
                title = emp.get('job_title', 'Unknown')
                company = emp.get('job_company_name', 'Unknown')
                print(f"  {i}. {name} - {title} at {company}")

            return True
        else:
            print(f"✗ Query failed: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error}")
            except:
                print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"✗ Fetch error: {e}")
        return False

def fix_company_display():
    """Attempt to fix company display issues"""
    print("\n" + "="*60)
    print("FIXING COMPANY DISPLAY")
    print("="*60)

    try:
        # Ensure all target companies are in database
        from config.target_companies import TARGET_COMPANIES

        conn = sqlite3.connect('data/tracking.db')
        cursor = conn.cursor()

        # Check which companies are missing from database
        cursor.execute('SELECT company FROM company_config')
        db_companies = {row[0].lower() for row in cursor.fetchall()}

        missing_companies = []
        for company in TARGET_COMPANIES:
            if company.lower() not in db_companies:
                missing_companies.append(company)

        if missing_companies:
            print(f"Found {len(missing_companies)} missing companies in database:")
            for company in missing_companies:
                print(f"  - {company}")
                cursor.execute(
                    'INSERT OR IGNORE INTO company_config (company, employee_count) VALUES (?, ?)',
                    (company, 5)
                )

            conn.commit()
            print("✓ Added missing companies to database")
        else:
            print("✓ All companies already in database")

        # Update any NULL employee counts
        cursor.execute('UPDATE company_config SET employee_count = 5 WHERE employee_count IS NULL')
        updated = cursor.rowcount
        conn.commit()
        conn.close()

        if updated > 0:
            print(f"✓ Fixed {updated} NULL employee counts")

        return True

    except Exception as e:
        print(f"✗ Fix failed: {e}")
        return False

def main():
    """Run all diagnostics"""
    print("EMPLOYEE TRACKER DIAGNOSTIC TOOL")
    print("=" * 80)

    results = {}
    results['company_display'] = test_company_display()
    results['pdl_api'] = test_pdl_api()
    results['employee_tracker'] = test_employee_tracker()
    results['simple_fetch'] = test_simple_pdl_fetch()

    # Try to fix issues
    if not results['company_display']:
        print("\n🔧 Attempting to fix company display...")
        results['company_fix'] = fix_company_display()

    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)

    all_good = True
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test.upper().replace('_', ' '):<20}: {status}")
        if not passed:
            all_good = False

    print("\n" + "="*80)
    if all_good:
        print("🎉 ALL TESTS PASSED! Your system should be working correctly.")
    else:
        print("⚠️  ISSUES FOUND - Check the details above for specific problems.")
        print("\nCommon solutions:")
        print("1. Company display: Run the server and visit /companies endpoint")
        print("2. PDL API: Check your API key and credits at peopledatalabs.com")
        print("3. Database: Ensure data/tracking.db exists and is readable")
    print("="*80)

if __name__ == "__main__":
    main()