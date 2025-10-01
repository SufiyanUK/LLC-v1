"""
Test live API endpoints to ensure they're responding correctly
"""
import requests
import json

API_BASE = "http://localhost:8002"

print("\n" + "="*60)
print("LIVE API ENDPOINT TESTS")
print("="*60)

def test_endpoint(name, url, method="GET"):
    """Test an API endpoint"""
    print(f"\nTesting {method} {url}...")
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, timeout=5)

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Response preview: {str(data)[:200]}...")
            return True
        else:
            print(f"  Error: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Cannot connect - is the server running on port 8002?")
        return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

# Test endpoints
print("\n1. HEALTH CHECK")
test_endpoint("Health", f"{API_BASE}/health")

print("\n2. COMPANIES ENDPOINT")
success = test_endpoint("Companies", f"{API_BASE}/companies")
if success:
    try:
        response = requests.get(f"{API_BASE}/companies")
        data = response.json()
        print(f"  Companies count: {data.get('total', 0)}")
        print(f"  Employee counts: {data.get('employee_counts', {})}")
        print(f"  Default counts: {data.get('default_counts', {})}")
    except:
        pass

print("\n3. TRACKING STATUS")
success = test_endpoint("Status", f"{API_BASE}/track/status")
if success:
    try:
        response = requests.get(f"{API_BASE}/track/status")
        data = response.json()
        print(f"  Total tracked: {data.get('total_tracked', 0)}")
        print(f"  Active: {data.get('active', 0)}")
    except:
        pass

print("\n4. EMPLOYEES LIST")
success = test_endpoint("Employees", f"{API_BASE}/track/employees")
if success:
    try:
        response = requests.get(f"{API_BASE}/track/employees")
        data = response.json()
        print(f"  Total employees: {data.get('total', 0)}")
        print(f"  Active: {data.get('active', 0)}")
        if data.get('employees'):
            print(f"  Sample: {data['employees'][0]['name']} at {data['employees'][0]['company']}")
    except:
        pass

print("\n" + "="*60)
print("If all tests passed, your API is working correctly!")
print("Now open http://localhost:8002 in your browser")
print("="*60)
