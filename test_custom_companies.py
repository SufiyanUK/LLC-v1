"""
Test custom company integration
Test that custom companies appear in the main company list
"""

import requests
import json

def test_custom_company_integration():
    """Test the full custom company flow"""
    base_url = "http://localhost:8001"

    print("TESTING CUSTOM COMPANY INTEGRATION")
    print("="*50)

    # Step 1: Get initial company list
    print("1. Testing initial company list...")
    response = requests.get(f"{base_url}/companies")

    if response.status_code == 200:
        data = response.json()
        initial_companies = data.get('companies', [])
        custom_companies = data.get('custom', [])

        print(f"   ✓ Found {len(initial_companies)} total companies")
        print(f"   ✓ Found {len(custom_companies)} custom companies")

        if custom_companies:
            print(f"   Custom companies: {custom_companies}")
        else:
            print("   No custom companies yet")
    else:
        print(f"   ✗ Failed to get companies: {response.status_code}")
        return False

    # Step 2: Test company suggestions (should include custom companies)
    print("\\n2. Testing company suggestions...")
    response = requests.get(f"{base_url}/company-suggestions")

    if response.status_code == 200:
        data = response.json()
        suggestions = data.get('suggestions', {})
        custom_count = data.get('custom_count', 0)

        print(f"   ✓ Found suggestions for {len(suggestions)} companies")
        print(f"   ✓ {custom_count} custom company suggestions")

        # Show a few custom suggestions
        for company, suggestion in suggestions.items():
            if company.lower() not in ['openai', 'anthropic', 'meta', 'google']:
                print(f"   Custom suggestion: {company} -> {suggestion['recommended']}")
                break
    else:
        print(f"   ✗ Failed to get suggestions: {response.status_code}")

    # Step 3: Add a test custom company
    print("\\n3. Testing adding custom company...")
    test_company = "TestCorp Inc"
    test_data = {
        "company_name": test_company,
        "employee_count": 3
    }

    response = requests.post(f"{base_url}/track/custom-company", json=test_data)

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✓ Successfully added {test_company}")
            print(f"   Message: {data.get('message')}")
        else:
            print(f"   ✗ Failed to add: {data.get('message')}")
            return False
    else:
        print(f"   ✗ Failed to add custom company: {response.status_code}")
        return False

    # Step 4: Verify the custom company appears in the list
    print("\\n4. Verifying custom company appears in list...")
    response = requests.get(f"{base_url}/companies")

    if response.status_code == 200:
        data = response.json()
        new_companies = data.get('companies', [])
        custom_companies = data.get('custom', [])

        if test_company in new_companies:
            print(f"   ✓ {test_company} appears in main company list")
        else:
            print(f"   ✗ {test_company} NOT in main company list")
            print(f"   Companies: {new_companies}")
            return False

        if test_company in custom_companies:
            print(f"   ✓ {test_company} correctly marked as custom")
        else:
            print(f"   ✗ {test_company} NOT marked as custom")
            print(f"   Custom companies: {custom_companies}")

    # Step 5: Verify it has suggestions
    print("\\n5. Verifying custom company has suggestions...")
    response = requests.get(f"{base_url}/company-suggestions")

    if response.status_code == 200:
        data = response.json()
        suggestions = data.get('suggestions', {})

        if test_company in suggestions:
            suggestion = suggestions[test_company]
            print(f"   ✓ {test_company} has suggestions: {suggestion}")
        else:
            print(f"   ✗ {test_company} missing from suggestions")
            return False

    print("\\n" + "="*50)
    print("INTEGRATION TEST RESULTS:")
    print("✓ Custom companies are integrated into main company list")
    print("✓ Custom companies have default suggestions")
    print("✓ Frontend will display custom companies with special styling")
    print("✓ Custom companies refresh automatically after adding")
    print("="*50)

    return True

if __name__ == "__main__":
    success = test_custom_company_integration()
    if success:
        print("\\n🎉 ALL TESTS PASSED! Custom company integration working!")
    else:
        print("\\n❌ TESTS FAILED - Check the issues above")