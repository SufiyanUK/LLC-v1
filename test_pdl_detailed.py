"""
Detailed PDL API testing and debugging
Tests various aspects of PDL API integration
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_api_key():
    """Check if API key is properly configured"""
    print("CHECKING API KEY CONFIGURATION")
    print("="*50)

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        print("✗ No API_KEY found in environment")
        print("\nPlease check:")
        print("1. .env file exists in current directory")
        print("2. .env file contains: API_KEY=your_actual_key")
        print("3. No spaces around the = sign")
        return None

    print(f"✓ API key found")
    print(f"  Length: {len(api_key)} characters")
    print(f"  Starts with: {api_key[:10]}...")
    print(f"  Ends with: ...{api_key[-10:]}")

    return api_key

def test_basic_connectivity(api_key):
    """Test basic PDL API connectivity"""
    print("\nTESTING BASIC PDL CONNECTIVITY")
    print("="*50)

    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    # Test with simplest possible query
    test_query = {
        'sql': 'SELECT * FROM person LIMIT 1',
        'size': 1
    }

    try:
        print("Sending basic test query...")
        response = requests.post(
            'https://api.peopledatalabs.com/v5/person/search',
            headers=headers,
            json=test_query,
            timeout=30
        )

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print("✓ Basic connectivity successful!")
            print(f"  Records returned: {len(data.get('data', []))}")
            return True

        elif response.status_code == 401:
            print("✗ Authentication failed (401)")
            print("  Your API key is invalid or expired")
            try:
                error = response.json()
                print(f"  Error details: {error}")
            except:
                pass
            return False

        elif response.status_code == 402:
            print("✗ Payment required (402)")
            print("  You have no credits remaining")
            try:
                error = response.json()
                print(f"  Error details: {error}")
            except:
                pass
            return False

        elif response.status_code == 429:
            print("✗ Rate limited (429)")
            print("  Too many requests - wait and try again")
            return False

        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"  Response text: {response.text[:300]}")
            return False

    except requests.exceptions.Timeout:
        print("✗ Request timeout")
        print("  PDL API took too long to respond")
        return False

    except requests.exceptions.ConnectionError:
        print("✗ Connection error")
        print("  Could not connect to PDL servers")
        print("  Check your internet connection")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_company_queries(api_key):
    """Test company-specific queries like the ones used in the app"""
    print("\nTESTING COMPANY-SPECIFIC QUERIES")
    print("="*50)

    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    test_companies = ['openai', 'anthropic', 'meta']

    for company in test_companies:
        print(f"\nTesting queries for: {company}")
        print("-" * 30)

        # Test 1: Basic company query
        query1 = {
            'sql': f'SELECT * FROM person WHERE job_company_name = "{company}" LIMIT 2',
            'size': 2
        }

        try:
            response = requests.post(
                'https://api.peopledatalabs.com/v5/person/search',
                headers=headers,
                json=query1,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                employees = data.get('data', [])
                print(f"  ✓ Basic query: Found {len(employees)} employees")

                if employees:
                    emp = employees[0]
                    print(f"    Sample: {emp.get('full_name', 'Unknown')} - {emp.get('job_title', 'Unknown')}")

            else:
                print(f"  ✗ Basic query failed: {response.status_code}")

        except Exception as e:
            print(f"  ✗ Basic query error: {e}")

        # Test 2: Senior roles query (like in the app)
        query2 = {
            'sql': f'''
            SELECT * FROM person
            WHERE job_company_name = "{company}"
            AND job_title_levels IN ("vp", "director", "senior", "lead")
            LIMIT 2
            '''.strip(),
            'size': 2
        }

        try:
            response = requests.post(
                'https://api.peopledatalabs.com/v5/person/search',
                headers=headers,
                json=query2,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                employees = data.get('data', [])
                print(f"  ✓ Senior query: Found {len(employees)} senior employees")

                if employees:
                    emp = employees[0]
                    print(f"    Sample: {emp.get('full_name', 'Unknown')} - {emp.get('job_title', 'Unknown')}")

            else:
                print(f"  ✗ Senior query failed: {response.status_code}")
                if response.status_code == 400:
                    try:
                        error = response.json()
                        print(f"    Error: {error.get('error', {}).get('message', 'Unknown')}")
                    except:
                        pass

        except Exception as e:
            print(f"  ✗ Senior query error: {e}")

def test_employee_tracker_integration(api_key):
    """Test the EmployeeTracker class with PDL"""
    print("\nTESTING EMPLOYEE TRACKER INTEGRATION")
    print("="*50)

    try:
        from scripts.employee_tracker import EmployeeTracker

        # Create instance
        tracker = EmployeeTracker()
        print("✓ EmployeeTracker created successfully")

        # Test database connection
        stats = tracker.db.get_statistics()
        print(f"✓ Database connected - {stats.get('total_employees', 0)} employees tracked")

        # Test a small fetch (only 1 employee to save credits)
        print(f"\nTesting small fetch from OpenAI (1 employee)...")

        employees = tracker.fetch_senior_employees('openai', count=1, exclude_existing=True)

        if employees:
            print(f"✓ Fetch successful! Got {len(employees)} employee(s)")
            emp = employees[0]
            print(f"  Name: {emp.get('full_name', 'Unknown')}")
            print(f"  Title: {emp.get('job_title', 'Unknown')}")
            print(f"  Company: {emp.get('job_company_name', 'Unknown')}")
        else:
            print("✗ Fetch returned no employees")
            print("  This could be due to:")
            print("  - All employees already tracked")
            print("  - Query filters too restrictive")
            print("  - API issues")

        return len(employees) > 0

    except Exception as e:
        print(f"✗ EmployeeTracker error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_recommendations():
    """Show recommendations based on test results"""
    print("\nRECOMMENDATIONS")
    print("="*50)

    print("For Company Display Issues:")
    print("1. Run: python fix_company_display.py")
    print("2. Start server: python api_v2.py")
    print("3. Visit: http://localhost:8000/companies")
    print("4. Check database: data/tracking.db should exist")

    print("\nFor PDL API Issues:")
    print("1. Check API key at: https://www.peopledatalabs.com/")
    print("2. Verify credits remaining in your PDL account")
    print("3. Ensure .env file has correct API_KEY")
    print("4. Try smaller queries first (size=1)")

    print("\nFor Integration Issues:")
    print("1. Run: python debug_issues.py")
    print("2. Check logs when running fetch operations")
    print("3. Start with test companies: openai, anthropic")

def main():
    """Run comprehensive PDL testing"""
    print("PDL API COMPREHENSIVE TESTING")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Test 1: API Key
    api_key = check_api_key()
    if not api_key:
        show_recommendations()
        return

    # Test 2: Basic connectivity
    connectivity_ok = test_basic_connectivity(api_key)
    if not connectivity_ok:
        show_recommendations()
        return

    # Test 3: Company queries
    test_company_queries(api_key)

    # Test 4: Integration test
    integration_ok = test_employee_tracker_integration(api_key)

    # Summary
    print("\n" + "="*60)
    print("PDL TESTING SUMMARY")
    print("="*60)

    if connectivity_ok and integration_ok:
        print("🎉 PDL API is working correctly!")
        print("Your employee tracking system should work properly.")
    else:
        print("⚠️  Issues found with PDL integration.")
        show_recommendations()

if __name__ == "__main__":
    main()