"""
Test adding employees with filter bypass to ensure it works
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_with_all_employees():
    """Test without filtering to see if employees can be added"""

    print("\n" + "="*60)
    print("TESTING WITH FILTER BYPASS")
    print("="*60)

    from scripts.employee_tracker import EmployeeTracker

    tracker = EmployeeTracker()

    # Temporarily bypass the technical filter
    original_filter = tracker.is_technical_role
    tracker.is_technical_role = lambda x: True  # Accept all roles

    print("\n✓ Bypassed technical role filter - accepting all employees")

    # Try fetching and adding employees
    print("\nFetching 3 employees from OpenAI...")

    employees = tracker.fetch_senior_employees('openai', 3)

    if employees:
        print(f"✓ Fetched {len(employees)} employees:")
        for emp in employees:
            print(f"  - {emp.get('full_name')}: {emp.get('job_title')}")

        # Add to database
        print("\nAdding to database...")
        added, updated = tracker.db.add_employees(employees, 'openai')

        print(f"✓ Database result: added={added}, updated={updated}")

        # Check if they're in the database
        all_employees = tracker.db.get_all_employees()
        print(f"\nTotal employees in database now: {len(all_employees)}")

        if all_employees:
            print("Employees in database:")
            for emp in all_employees[:5]:
                print(f"  - {emp.get('name')} ({emp.get('company')}) - Status: {emp.get('status')}")
    else:
        print("✗ No employees fetched even with filter bypass!")
        print("  Check API_KEY and PDL credits")

    # Restore original filter
    tracker.is_technical_role = original_filter

def test_with_fixed_filter():
    """Test with the updated filter logic"""

    print("\n" + "="*60)
    print("TESTING WITH UPDATED FILTER")
    print("="*60)

    from scripts.employee_tracker import EmployeeTracker

    tracker = EmployeeTracker()

    print("\nTesting specific job titles:")
    test_titles = [
        "senior gtm systems engineer",
        "senior software engineer",
        "sales engineer",
        "machine learning engineer",
        "product marketing manager",
        "engineering manager"
    ]

    for title in test_titles:
        is_tech = tracker.is_technical_role(title)
        print(f"  '{title}': {'✓ Technical' if is_tech else '✗ Non-technical'}")

    # Now try fetching with the new logic
    print("\nFetching 2 employees from OpenAI with updated filter...")

    employees = tracker.fetch_senior_employees('openai', 2)

    if employees:
        print(f"✓ Fetched {len(employees)} employees:")
        for emp in employees:
            print(f"  - {emp.get('full_name')}: {emp.get('job_title')}")

        # Add to database
        added, updated = tracker.db.add_employees(employees, 'openai')
        print(f"✓ Added: {added}, Updated: {updated}")
    else:
        print("Still no employees - trying with bypass...")
        test_with_all_employees()

if __name__ == "__main__":
    # First test with the updated filter
    test_with_fixed_filter()

    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    print("\nIf employees are still being filtered out incorrectly:")
    print("1. Run with bypass to populate database initially")
    print("2. Adjust filter rules in is_technical_role()")
    print("3. Or use a less strict filter for initial population")
    print("\nThe key is to get SOME employees in the database first!")