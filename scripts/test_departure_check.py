"""
Test Departure Check - Uses database data instead of PDL API
Allows testing the departure detection and classification without credits
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.database_factory import TrackingDatabase
from scripts.departure_classifier import DepartureClassifier
from scripts.email_alerts import EmailAlertSender

class TestDepartureChecker:
    """Run departure checks using database data instead of PDL API"""
    
    def __init__(self):
        self.db = TrackingDatabase()
        self.classifier = DepartureClassifier()
    
    def run_test_check(self) -> List[Dict]:
        """
        Check for departures using database data
        Compares 'company' vs 'current_company' fields
        """
        print("\n" + "="*60)
        print("TEST DEPARTURE CHECK (No Credits Used)")
        print("="*60)
        
        # Get all active employees from database
        employees = self.db.get_all_employees(status='active')
        
        if not employees:
            print("[ERROR] No employees being tracked.")
            return []
        
        print(f"\n[SEARCH] Checking {len(employees)} tracked employees...")
        print("(Using database data, not PDL API)")
        print("-" * 40)
        
        departures = []
        checked = 0
        
        for emp in employees:
            checked += 1
            pdl_id = emp['pdl_id']
            name = emp['name']
            
            print(f"\n[{checked}/{len(employees)}] Checking {name}...")
            
            # Compare original company with current_company in database
            original_company = emp.get('company', '').lower()
            current_company = emp.get('current_company', '').lower()
            
            # For testing: also check if full_data has updated info
            full_data = emp.get('full_data', {})
            if isinstance(full_data, str):
                import json
                try:
                    full_data = json.loads(full_data)
                    print(f"     DEBUG - Loaded full_data with {len(full_data)} fields")
                except Exception as e:
                    print(f"     DEBUG - Error loading full_data: {e}")
                    full_data = {}
            elif full_data is None:
                print(f"     DEBUG - full_data is None")
                full_data = {}
            
            # Override current_company if full_data has job_company_name
            if full_data.get('job_company_name'):
                current_company = full_data['job_company_name'].lower()
            
            if original_company and current_company and original_company != current_company:
                # Departure detected!
                print(f"  [WARNING] DEPARTURE DETECTED!")
                print(f"     From: {emp.get('company')} -> To: {full_data.get('job_company_name', current_company)}")
                
                departure = {
                    'pdl_id': pdl_id,
                    'name': name,
                    'old_company': emp.get('company'),
                    'old_title': emp.get('title'),
                    'new_company': full_data.get('job_company_name', current_company.title()),
                    'new_title': full_data.get('job_title', emp.get('title', 'Unknown')),
                    'job_last_changed': emp.get('job_last_changed', datetime.now().isoformat()),
                    'detected_date': datetime.now().isoformat(),
                    'linkedin': emp.get('linkedin_url'),
                    # Classification fields from full_data
                    'headline': full_data.get('headline', ''),
                    'summary': full_data.get('summary', ''),
                    'job_summary': full_data.get('job_summary', ''),
                    'job_company_type': full_data.get('job_company_type', ''),
                    'job_company_size': full_data.get('job_company_size', ''),
                    'job_company_founded': full_data.get('job_company_founded', ''),
                    'job_company_industry': full_data.get('job_company_industry', '')
                }
                
                # Classify the departure
                # Debug: Print what we're passing
                if departure.get('headline'):
                    print(f"     DEBUG - Headline: {departure['headline'][:50]}...")
                if departure.get('summary'):
                    print(f"     DEBUG - Summary: {departure['summary'][:50]}...")
                
                alert_level, signals = self.classifier.classify_departure(departure)
                departure['alert_level'] = alert_level
                departure['alert_signals'] = signals
                
                # Display classification
                level_display = {
                    1: "[Level 1] (Standard)",
                    2: "[Level 2] (Building Signals)",
                    3: "[Level 3] (High Priority - Startup)"
                }
                print(f"     Alert: {level_display.get(alert_level, 'Unknown')}")
                if signals:
                    print(f"     Signals: {', '.join(signals[:3])}")
                
                departures.append(departure)
                
                # Save to database
                self.db.add_departure(departure)
                
                # Update employee status (commented out for testing)
                # self.db.update_employee_status(pdl_id, 'departed', departure['new_company'])
                
            else:
                if original_company == current_company:
                    print(f"  [OK] Still at {emp.get('company')}")
                else:
                    print(f"  [WARNING] Missing company data")
        
        # Summary
        print("\n" + "="*60)
        print("TEST CHECK SUMMARY")
        print("="*60)
        print(f"Employees checked: {checked}")
        print(f"Departures found: {len(departures)}")
        print(f"Credits used: 0 (test mode)")
        
        if departures:
            # Group by alert level
            by_level = {0: [], 1: [], 2: [], 3: []}
            for dep in departures:
                alert_level = dep.get('alert_level', 0)
                if alert_level in by_level:
                    by_level[alert_level].append(dep)
            
            print("\nDepartures by alert level:")
            if by_level[3]:
                print(f"  [LEVEL 3] High Priority: {len(by_level[3])}")
                for d in by_level[3]:
                    print(f"     - {d['name']}: {d['old_company']} -> {d['new_company']}")
            if by_level[2]:
                print(f"  [LEVEL 2] Building Signals: {len(by_level[2])}")
                for d in by_level[2]:
                    print(f"     - {d['name']}: {d['headline'][:50]}...")
            if by_level[1]:
                print(f"  [LEVEL 1] Standard: {len(by_level[1])}")
                for d in by_level[1]:
                    print(f"     - {d['name']}: {d['old_company']} -> {d['new_company']}")
        
        return departures


def main():
    """Run the test departure check"""
    print("\n[TEST] TEST MODE - DEPARTURE CHECK")
    print("This checks for departures using database data only")
    print("NO PDL credits will be used!\n")
    
    input("Press Enter to start the test check...")
    
    checker = TestDepartureChecker()
    departures = checker.run_test_check()
    
    if departures:
        print(f"\n[SUCCESS] Test complete! Found {len(departures)} departures.")
        print("\nThese have been saved to the database and classified.")
        print("You can view them in the web UI under 'Departures'.")
    else:
        print("\n[SUCCESS] Test complete! No departures detected.")
        print("\nTo test departures:")
        print("1. Manually update 'current_company' in the database")
        print("2. Run this test again")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()