"""
Test the exact flow when adding employees to find where it breaks
This simulates what happens when you click "Add Company" in the UI
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_complete_flow():
    """Test the complete flow of adding employees"""

    print("\n" + "="*60)
    print("TESTING COMPLETE ADD EMPLOYEE FLOW")
    print("="*60)

    # Check environment
    database_url = os.getenv('DATABASE_URL')
    api_key = os.getenv('API_KEY')

    print(f"\n1. Environment Check:")
    print(f"   DATABASE_URL: {'✓ Present' if database_url else '✗ Missing'}")
    print(f"   API_KEY: {'✓ Present' if api_key else '✗ Missing'}")

    if not api_key:
        print("\n❌ Cannot continue without API_KEY")
        return

    # Import classes
    try:
        from scripts.employee_tracker import EmployeeTracker
        from scripts.database_factory import TrackingDatabase

        print(f"\n2. Module Import: ✓ Success")
    except Exception as e:
        print(f"\n2. Module Import: ✗ Failed - {e}")
        return

    # Initialize tracker
    try:
        tracker = EmployeeTracker()
        print(f"\n3. EmployeeTracker Init: ✓ Success")
    except Exception as e:
        print(f"\n3. EmployeeTracker Init: ✗ Failed - {e}")
        return

    # Test fetching employees from PDL
    print(f"\n4. Testing PDL API Fetch:")
    print(f"   Fetching 1 employee from 'openai'...")

    try:
        # Use a small number to save credits
        employees = tracker.fetch_senior_employees('openai', 1)

        if employees and len(employees) > 0:
            print(f"   ✓ Fetched {len(employees)} employee(s)")
            emp = employees[0]
            print(f"\n   Employee details:")
            print(f"   - ID: {emp.get('id', 'MISSING')}")
            print(f"   - Name: {emp.get('full_name', 'MISSING')}")
            print(f"   - Title: {emp.get('job_title', 'MISSING')}")
            print(f"   - Company: {emp.get('job_company_name', 'MISSING')}")

            # Check for critical fields
            if not emp.get('id'):
                print(f"   ⚠️ WARNING: Employee has no 'id' field!")
        else:
            print(f"   ✗ No employees returned from PDL API")
            print(f"   Check if API_KEY is valid and has credits")
            return

    except Exception as e:
        print(f"   ✗ PDL API fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test adding to database
    print(f"\n5. Testing Database Add:")

    try:
        added, updated = tracker.db.add_employees(employees, 'openai')
        print(f"   Result: added={added}, updated={updated}")

        if added > 0:
            print(f"   ✓ Successfully added {added} employee(s)")
        elif updated > 0:
            print(f"   ⚠️ Employee already exists, updated {updated}")
        else:
            print(f"   ✗ No employees were added or updated")

    except Exception as e:
        print(f"   ✗ Database add failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test retrieving from database
    print(f"\n6. Testing Database Retrieve:")

    try:
        # Get the PDL ID we just added
        pdl_id = employees[0].get('id')

        if pdl_id:
            # Try to get this specific employee
            emp_data = tracker.db.get_employee_by_id(pdl_id)

            if emp_data:
                print(f"   ✓ Retrieved employee: {emp_data.get('name')}")
                print(f"   - Status: {emp_data.get('status')}")
                print(f"   - Company: {emp_data.get('company')}")
            else:
                print(f"   ✗ Could not retrieve employee with ID: {pdl_id}")

    except Exception as e:
        print(f"   ✗ Retrieve failed: {e}")
        import traceback
        traceback.print_exc()

    # Test get_all_employees
    print(f"\n7. Testing get_all_employees:")

    try:
        all_employees = tracker.db.get_all_employees()
        print(f"   Total employees: {len(all_employees)}")

        # Check if our test employee is in the list
        if pdl_id:
            found = any(e.get('pdl_id') == pdl_id for e in all_employees)
            if found:
                print(f"   ✓ Test employee found in all_employees")
            else:
                print(f"   ✗ Test employee NOT found in all_employees")
                print(f"   This is likely the issue!")

    except Exception as e:
        print(f"   ✗ get_all_employees failed: {e}")
        import traceback
        traceback.print_exc()

    # Test the complete add_company_to_tracking flow
    print(f"\n8. Testing add_company_to_tracking:")

    try:
        result = tracker.add_company_to_tracking('openai', 1)
        print(f"   Result: {result}")

        if result and result.get('success'):
            print(f"   ✓ add_company_to_tracking succeeded")
            print(f"   - Added: {result.get('added')}")
            print(f"   - Updated: {result.get('updated')}")
            print(f"   - Total tracked: {result.get('total_tracked')}")
        else:
            print(f"   ✗ add_company_to_tracking failed")

    except Exception as e:
        print(f"   ✗ add_company_to_tracking error: {e}")
        import traceback
        traceback.print_exc()

    # Test what the API endpoint would return
    print(f"\n9. Testing API Endpoint Simulation:")

    try:
        # This is what /track/employees does
        employees = tracker.db.get_all_employees()
        active_employees = [e for e in employees if e['status'] != 'deleted']

        print(f"   get_all_employees: {len(employees)} employees")
        print(f"   After filtering deleted: {len(active_employees)} employees")

        if len(active_employees) == 0:
            print(f"   ✗ This is why your tracking tab is empty!")

            # Let's check what statuses employees have
            if employees:
                statuses = {}
                for e in employees:
                    status = e.get('status', 'NULL')
                    statuses[status] = statuses.get(status, 0) + 1

                print(f"\n   Employee statuses:")
                for status, count in statuses.items():
                    print(f"   - {status}: {count}")
        else:
            print(f"   ✓ Employees would show in tracking tab")

    except Exception as e:
        print(f"   ✗ API simulation failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the test"""
    test_complete_flow()

    print(f"\n" + "="*60)
    print("DIAGNOSIS COMPLETE")
    print("="*60)
    print("\nCheck the output above to find where the flow breaks.")
    print("The ✗ marks indicate where the problem is.")

if __name__ == "__main__":
    main()