"""
Test the exact endpoints your UI is calling
Run this while your server is running
"""

import requests
import json

def test_ui_endpoints():
    """Test the endpoints the frontend needs"""
    base_url = "http://localhost:8001"

    print("TESTING UI ENDPOINTS")
    print("="*50)
    print("Make sure your server is running: python api_v2.py")
    print()

    # Test /companies endpoint
    try:
        print("Testing /companies endpoint...")
        response = requests.get(f"{base_url}/companies", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✓ /companies endpoint working!")
            print(f"  Found {len(data.get('companies', []))} companies")
            print(f"  Companies: {data.get('companies', [])[:5]}...")
        else:
            print(f"✗ /companies failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server!")
        print("  Start server with: python api_v2.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Test /company-suggestions endpoint
    try:
        print("\\nTesting /company-suggestions endpoint...")
        response = requests.get(f"{base_url}/company-suggestions", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✓ /company-suggestions endpoint working!")
            print(f"  Found suggestions for {len(data.get('suggestions', {}))} companies")
            # Show sample suggestion
            suggestions = data.get('suggestions', {})
            if suggestions:
                sample_company = list(suggestions.keys())[0]
                sample_data = suggestions[sample_company]
                print(f"  Sample: {sample_company} -> {sample_data}")
        else:
            print(f"✗ /company-suggestions failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test health endpoint
    try:
        print("\\nTesting /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✓ /health endpoint working!")
            print(f"  Status: {data.get('status')}")
            print(f"  Database: {data.get('database', {}).get('connected', False)}")
        else:
            print(f"✗ /health failed: {response.status_code}")

    except Exception as e:
        print(f"✗ Health check error: {e}")

    # Test track/status (shows companies with employees)
    try:
        print("\\nTesting /track/status endpoint...")
        response = requests.get(f"{base_url}/track/status", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✓ /track/status endpoint working!")
            print(f"  Total employees: {data.get('total_employees', 0)}")
            print(f"  Companies tracked: {data.get('companies_tracked', 0)}")

            # Show companies with employees
            companies_with_employees = data.get('companies_with_employees', [])
            if companies_with_employees:
                print("  Companies with employees:")
                for company_data in companies_with_employees[:5]:
                    company_name = company_data.get('company', 'Unknown')
                    employee_count = company_data.get('employee_count', 0)
                    print(f"    - {company_name}: {employee_count} employees")
        else:
            print(f"✗ /track/status failed: {response.status_code}")

    except Exception as e:
        print(f"✗ Track status error: {e}")

    print("\\n" + "="*50)
    print("NEXT STEPS:")
    print("1. If all endpoints work, the issue is in the frontend")
    print("2. Open browser dev tools (F12) and check console for errors")
    print("3. Visit http://localhost:8000 and check Network tab")
    print("4. Look for JavaScript errors in the Console tab")

if __name__ == "__main__":
    test_ui_endpoints()