"""
Test the employee tracking system with a small batch
Uses minimal credits for testing
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from scripts.fetch_senior_employees import SeniorEmployeeFetcher
from config.target_companies import TARGET_COMPANIES

def test_small_batch():
    """Test with just 2-3 companies and 5 employees each"""
    
    print("\n" + "="*60)
    print("EMPLOYEE TRACKER - SMALL BATCH TEST")
    print("="*60)
    
    # Test with just a few companies
    test_companies = ['openai', 'anthropic', 'meta'][:2]  # Just 2 companies
    credits_per_company = 5  # Just 5 employees each
    
    print(f"\nTest Configuration:")
    print(f"  Companies: {', '.join(test_companies)}")
    print(f"  Employees per company: {credits_per_company}")
    print(f"  Total credits: {len(test_companies) * credits_per_company}")
    
    confirm = input("\nProceed with test? (y/n): ")
    if confirm.lower() != 'y':
        print("Test cancelled")
        return
    
    # Initialize fetcher
    fetcher = SeniorEmployeeFetcher()
    
    # Fetch from test companies
    all_employees = {}
    
    for company in test_companies:
        print(f"\n[TESTING] {company}")
        employees = fetcher.fetch_company_employees(company, credits_per_company)
        all_employees[company] = employees
        
        # Show sample results
        if employees:
            print(f"\n  Sample employees from {company}:")
            for emp in employees[:3]:
                name = emp.get('full_name', 'Unknown')
                title = emp.get('job_title', 'Unknown')
                print(f"    - {name}: {title}")
    
    # Save test snapshot
    if all_employees:
        fetcher.save_master_snapshot(all_employees)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print(f"Total employees fetched: {sum(len(emps) for emps in all_employees.values())}")
    print("\nNext steps:")
    print("1. Check data/snapshots/ for the saved data")
    print("2. Run monthly_tracker.py later to detect departures")
    print("="*60)

if __name__ == "__main__":
    test_small_batch()