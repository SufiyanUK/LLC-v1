"""
Test API endpoints to ensure they return correct data
Run this after starting your local server
"""

import requests
import json

def test_endpoint(url, method='GET', data=None):
    """Test an API endpoint and show results"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)

        print(f"\n{'='*60}")
        print(f"Testing: {method} {url}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:500]}...")
                return True
            except:
                print(f"Response (text): {response.text[:200]}...")
                return True
        else:
            print(f"Error: {response.text[:200]}...")
            return False

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {url}")
        print("Make sure your server is running!")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Test key API endpoints"""
    base_url = "http://localhost:8000"  # Change port if needed

    print("API ENDPOINT TESTING")
    print("="*60)
    print("Make sure your server is running with:")
    print("  python api_v2.py")
    print("  OR uvicorn api_v2:app --reload --port 8000")

    # Test endpoints
    endpoints = [
        "/health",
        "/companies",
        "/track/status",
        "/track/employees",
        "/api"
    ]

    results = {}
    for endpoint in endpoints:
        url = base_url + endpoint
        results[endpoint] = test_endpoint(url)

    # Test a POST endpoint
    print(f"\n{'='*60}")
    print("Testing POST /track/add-company")

    test_data = {
        "company": "test-company",
        "employee_count": 3
    }

    url = base_url + "/track/add-company"
    results["/track/add-company"] = test_endpoint(url, method='POST', data=test_data)

    # Summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for endpoint, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{endpoint:<25}: {status}")

    print(f"\nOverall: {passed}/{total} endpoints working")

    if passed == total:
        print("\n🎉 All endpoints working! Your API is healthy.")
    else:
        print("\n⚠️  Some endpoints failed. Check server logs for details.")

    # Specific guidance
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print("="*60)

    if not results.get("/companies", False):
        print("❌ Company endpoint failed:")
        print("   - Check if TARGET_COMPANIES is imported correctly")
        print("   - Verify config/target_companies.py exists")

    if not results.get("/health", False):
        print("❌ Health endpoint failed:")
        print("   - Check if database connection is working")
        print("   - Verify data/tracking.db exists")

    if not results.get("/track/employees", False):
        print("❌ Employees endpoint failed:")
        print("   - Database might be empty or corrupted")
        print("   - Try running debug_issues.py to fix")

    print("\nTo test PDL API functionality, run:")
    print("  python debug_issues.py")

if __name__ == "__main__":
    main()