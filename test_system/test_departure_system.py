"""
Test Departure Detection and Alert System
Uses the EXACT same logic as production but with mock data
No PDL credits used!
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import production modules (using the REAL classifier)
from scripts.departure_classifier import DepartureClassifier
from mock_pdl_data import MockPDLData

class DepartureSystemTester:
    """Test the complete departure detection and alert system"""
    
    def __init__(self):
        self.mock_data = MockPDLData()
        self.classifier = DepartureClassifier()  # Using REAL classifier
        self.test_results = []
        
    def simulate_initial_tracking(self):
        """Simulate initial employee tracking"""
        print("\n" + "="*60)
        print("STEP 1: INITIAL TRACKING SIMULATION")
        print("="*60)
        
        employees = self.mock_data.get_test_employees()
        
        print(f"\n[INFO] Simulating tracking of {len(employees)} employees:")
        print("-" * 40)
        
        for emp in employees:
            print(f"[OK] {emp['full_name']}")
            print(f"  Position: {emp['job_title']} at {emp['job_company_name']}")
            print(f"  Scenario: {emp['_test_scenario'].replace('_', ' ').title()}")
        
        print(f"\n[CREDITS] Credits that would be used: {len(employees)}")
        return employees
    
    def simulate_departure_check(self, initial_employees):
        """Simulate monthly departure check"""
        print("\n" + "="*60)
        print("STEP 2: DEPARTURE CHECK SIMULATION")
        print("="*60)
        
        departure_data = self.mock_data.get_departure_checks()
        expected_results = self.mock_data.get_expected_results()
        
        departures = []
        checked = 0
        
        print(f"\n[SEARCH] Checking {len(initial_employees)} employees for departures...")
        print("-" * 40)
        
        for emp in initial_employees:
            pdl_id = emp['id']
            checked += 1
            
            print(f"\n[{checked}/{len(initial_employees)}] Checking {emp['full_name']}...")
            
            # Get "updated" data (simulating PDL API check)
            current_status = departure_data.get(pdl_id)
            
            if current_status:
                old_company = emp['job_company_name'].lower()
                new_company = current_status.get('job_company_name', '').lower()
                
                # USING EXACT SAME LOGIC AS PRODUCTION
                if old_company != new_company:
                    # Departure detected!
                    departure = {
                        'pdl_id': pdl_id,
                        'name': emp['full_name'],
                        'old_company': emp['job_company_name'],
                        'old_title': emp['job_title'],
                        'new_company': current_status.get('job_company_name', 'Unknown'),
                        'new_title': current_status.get('job_title', 'Unknown'),
                        'job_last_changed': current_status.get('job_last_changed'),
                        'detected_date': datetime.now().isoformat(),
                        'linkedin': f"https://www.{emp.get('linkedin_url')}",
                        # New fields for classification
                        'headline': current_status.get('headline', ''),
                        'summary': current_status.get('summary', ''),
                        'job_summary': current_status.get('job_summary', ''),
                        'job_company_type': current_status.get('job_company_type', ''),
                        'job_company_size': current_status.get('job_company_size', ''),
                        'job_company_founded': current_status.get('job_company_founded', ''),
                        'job_company_industry': current_status.get('job_company_industry', '')
                    }
                    
                    departures.append(departure)
                    
                    print(f"  [WARNING] DEPARTURE DETECTED!")
                    print(f"     From: {emp['job_company_name']} -> To: {departure['new_company']}")
                else:
                    print(f"  [OK] Still at {emp['job_company_name']}")
        
        print(f"\n[CREDITS] Credits that would be used: {checked}")
        return departures
    
    def test_alert_classification(self, departures):
        """Test the alert classification system"""
        print("\n" + "="*60)
        print("STEP 3: ALERT CLASSIFICATION TEST")
        print("="*60)
        
        if not departures:
            print("\n[ERROR] No departures to classify")
            return []
        
        print(f"\n[TARGET] Classifying {len(departures)} departures...")
        print("-" * 40)
        
        # Use REAL classifier
        classified_departures = self.classifier.classify_all_departures(departures)
        
        # Group by level
        by_level = {1: [], 2: [], 3: []}
        for dep in classified_departures:
            level = dep.get('alert_level', 1)
            by_level[level].append(dep)
        
        # Display results
        print("\n[INFO] CLASSIFICATION RESULTS:")
        print("-" * 40)
        
        if by_level[3]:
            print(f"\n[LEVEL 3] LEVEL 3 - STARTUP/FOUNDER ({len(by_level[3])} alerts)")
            for dep in by_level[3]:
                print(f"\n  • {dep['name']}")
                print(f"    From: {dep['old_company']} -> To: {dep['new_company']}")
                if dep.get('headline'):
                    print(f"    Headline: \"{dep['headline']}\"")
                if dep.get('alert_signals'):
                    print(f"    Signals: {', '.join(dep['alert_signals'][:3])}")
        
        if by_level[2]:
            print(f"\n[LEVEL 2] LEVEL 2 - BUILDING SIGNALS ({len(by_level[2])} alerts)")
            for dep in by_level[2]:
                print(f"\n  • {dep['name']}")
                print(f"    From: {dep['old_company']} -> To: {dep['new_company']}")
                if dep.get('headline'):
                    print(f"    Headline: \"{dep['headline']}\"")
                if dep.get('alert_signals'):
                    print(f"    Signals: {', '.join(dep['alert_signals'][:3])}")
        
        if by_level[1]:
            print(f"\n[LEVEL 1] LEVEL 1 - STANDARD DEPARTURE ({len(by_level[1])} alerts)")
            for dep in by_level[1]:
                print(f"\n  • {dep['name']}")
                print(f"    From: {dep['old_company']} -> To: {dep['new_company']}")
        
        return classified_departures
    
    def test_email_alerts(self, classified_departures):
        """Test email alert generation (without sending)"""
        print("\n" + "="*60)
        print("STEP 4: EMAIL ALERT SIMULATION")
        print("="*60)
        
        if not classified_departures:
            print("\n[ERROR] No departures to send alerts for")
            return
        
        # Group by alert level
        by_level = {1: [], 2: [], 3: []}
        for dep in classified_departures:
            level = dep.get('alert_level', 1)
            by_level[level].append(dep)
        
        print("\n[EMAIL] Email alerts that would be sent:")
        print("-" * 40)
        
        # Level 3 - Immediate alerts
        if by_level[3]:
            print(f"\n[HIGH PRIORITY] HIGH PRIORITY EMAIL")
            print(f"  Subject: [HIGH PRIORITY] HIGH PRIORITY - Startup Departure: {len(by_level[3])} from Multiple")
            print(f"  Recipients: alerts@yourcompany.com")
            print(f"  Priority: HIGH (X-Priority: 1)")
            print(f"  Content:")
            for dep in by_level[3]:
                print(f"    - {dep['name']}: {dep['old_company']} -> {dep['new_company']}")
                if dep.get('alert_signals'):
                    print(f"      Signals: {', '.join(dep['alert_signals'][:2])}")
        
        # Level 2 - Important alerts
        if by_level[2]:
            print(f"\n[WARNING] IMPORTANT EMAIL")
            print(f"  Subject: [WARNING] IMPORTANT - Building Signals: {len(by_level[2])} from Multiple")
            print(f"  Recipients: alerts@yourcompany.com")
            print(f"  Content:")
            for dep in by_level[2]:
                print(f"    - {dep['name']}: {dep.get('headline', 'No headline')}")
        
        # Level 1 - Standard alerts
        if by_level[1]:
            print(f"\n[ALERT] STANDARD EMAIL")
            print(f"  Subject: [ALERT] Departure Alert: {len(by_level[1])} from Multiple")
            print(f"  Recipients: alerts@yourcompany.com")
            print(f"  Content:")
            for dep in by_level[1]:
                print(f"    - {dep['name']}: {dep['old_company']} -> {dep['new_company']}")
    
    def validate_results(self, classified_departures):
        """Validate test results against expected outcomes"""
        print("\n" + "="*60)
        print("STEP 5: VALIDATION")
        print("="*60)
        
        expected = self.mock_data.get_expected_results()
        
        print("\n[SUCCESS] Validating results against expected outcomes...")
        print("-" * 40)
        
        all_passed = True
        
        for dep in classified_departures:
            pdl_id = dep['pdl_id']
            expected_result = expected.get(pdl_id)
            
            if expected_result:
                actual_level = dep.get('alert_level', 0)
                expected_level = expected_result['alert_level']
                
                if actual_level == expected_level:
                    print(f"[OK] {dep['name']}: Level {actual_level} (CORRECT)")
                else:
                    print(f"[X] {dep['name']}: Expected Level {expected_level}, Got Level {actual_level} (FAILED)")
                    all_passed = False
        
        # Check for missed departures
        for pdl_id, exp in expected.items():
            if exp['departure'] and not any(d['pdl_id'] == pdl_id for d in classified_departures):
                print(f"[X] Missed departure: {pdl_id} (FAILED)")
                all_passed = False
        
        if all_passed:
            print("\n[COMPLETE] ALL TESTS PASSED!")
        else:
            print("\n[ERROR] SOME TESTS FAILED - Review the logic")
        
        return all_passed
    
    def run_complete_test(self):
        """Run the complete test suite"""
        print("\n" + "="*60)
        print("\nDEPARTURE DETECTION & ALERT SYSTEM TEST")
        print("\n" + "="*60)
        
        print("\nThis test simulates the EXACT production logic without using PDL credits")
        print("Testing all 3 alert levels and email notifications")
        
        # Step 1: Initial tracking
        initial_employees = self.simulate_initial_tracking()
        
        # Step 2: Departure check
        departures = self.simulate_departure_check(initial_employees)
        
        # Step 3: Alert classification
        classified_departures = self.test_alert_classification(departures)
        
        # Step 4: Email alerts
        self.test_email_alerts(classified_departures)
        
        # Step 5: Validation
        all_passed = self.validate_results(classified_departures)
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        print(f"\n[INFO] Results:")
        print(f"  • Employees tracked: {len(initial_employees)}")
        print(f"  • Departures detected: {len(departures)}")
        print(f"  • Level 3 alerts: {sum(1 for d in classified_departures if d.get('alert_level') == 3)}")
        print(f"  • Level 2 alerts: {sum(1 for d in classified_departures if d.get('alert_level') == 2)}")
        print(f"  • Level 1 alerts: {sum(1 for d in classified_departures if d.get('alert_level') == 1)}")
        print(f"  • Test status: {'[SUCCESS] PASSED' if all_passed else '[ERROR] FAILED'}")
        
        print(f"\n[CREDITS] Credits that would be used in production:")
        print(f"  • Initial tracking: {len(initial_employees)} credits")
        print(f"  • Monthly check: {len(initial_employees)} credits")
        print(f"  • Total: {len(initial_employees) * 2} credits")
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        
        return all_passed


def main():
    """Run the test"""
    tester = DepartureSystemTester()
    success = tester.run_complete_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()