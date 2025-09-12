"""
Fixed Manual Database Test for Departure Detection
Works with the actual departure check logic
"""

import sys
import sqlite3
import json
import requests
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class ManualDatabaseTesterFixed:
    """Test departure detection using the test endpoint"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
        self.api_base = "http://localhost:8002"
        
        if not self.db_path.exists():
            print(f"❌ Database not found at {self.db_path}")
            print("Please run the main system at least once to create the database.")
            sys.exit(1)
    
    def check_api_running(self):
        """Check if the API server is running"""
        try:
            response = requests.get(f"{self.api_base}/api")
            return response.status_code == 200
        except:
            return False
    
    def run_test_departure_check(self):
        """Use the test endpoint that simulates departures"""
        print("\n🔍 Running TEST departure check (no credits used)...")
        
        try:
            response = requests.post(f"{self.api_base}/check/test")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Test check complete!")
                
                if data.get('simulated_departure'):
                    dep = data['simulated_departure']
                    print(f"\n📊 Simulated Departure:")
                    print(f"  Name: {dep['name']}")
                    print(f"  From: {dep['old_company']} → To: {dep['new_company']}")
                    
                    # Check the departure history to see classification
                    history_response = requests.get(f"{self.api_base}/check/history")
                    if history_response.status_code == 200:
                        history = history_response.json()
                        if history['departures']:
                            latest = history['departures'][0]
                            level = latest.get('alert_level', 1)
                            
                            if level == 3:
                                print(f"  Alert: 🔴 Level 3 (HIGH PRIORITY)")
                            elif level == 2:
                                print(f"  Alert: 🟠 Level 2 (BUILDING SIGNALS)")
                            else:
                                print(f"  Alert: 🟡 Level 1 (STANDARD)")
                            
                            if latest.get('alert_signals'):
                                print(f"  Signals: {', '.join(latest['alert_signals'][:3])}")
                
                return True
            else:
                print(f"❌ Test check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error running test check: {e}")
            return False
    
    def get_tracked_employees(self):
        """Get list of tracked employees from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT pdl_id, name, company, title, status
                FROM tracked_employees
                WHERE status = 'active'
                LIMIT 10
            """)
            
            employees = cursor.fetchall()
            
            if employees:
                print("\n📋 Currently tracked employees:")
                print("-" * 40)
                for i, (pdl_id, name, company, title, status) in enumerate(employees, 1):
                    print(f"{i}. {name}")
                    print(f"   Company: {company}")
                    print(f"   Title: {title}")
                    print(f"   PDL ID: {pdl_id[:20]}...")
                
                return employees
            else:
                print("\n⚠️ No active employees being tracked.")
                print("Please add some employees first using the web UI.")
                return []
                
        except Exception as e:
            print(f"❌ Error getting employees: {e}")
            return []
        finally:
            conn.close()
    
    def view_departure_history(self):
        """View all departures from the API"""
        try:
            response = requests.get(f"{self.api_base}/check/history")
            if response.status_code == 200:
                data = response.json()
                
                print("\n📊 Departure History:")
                print("-" * 60)
                
                if data['total'] == 0:
                    print("No departures detected yet.")
                else:
                    print(f"Total departures: {data['total']}")
                    print(f"  🔴 Level 3 (High Priority): {data['counts']['level_3']}")
                    print(f"  🟠 Level 2 (Building Signals): {data['counts']['level_2']}")
                    print(f"  🟡 Level 1 (Standard): {data['counts']['level_1']}")
                    
                    # Show recent departures
                    print("\nRecent departures:")
                    for dep in data['departures'][:5]:
                        level = dep.get('alert_level', 1)
                        level_icon = {1: "🟡", 2: "🟠", 3: "🔴"}.get(level, "⚪")
                        
                        print(f"\n  {level_icon} {dep['name']}")
                        print(f"     From: {dep['old_company']} → To: {dep['new_company']}")
                        if dep.get('alert_signals'):
                            print(f"     Signals: {', '.join(dep['alert_signals'][:3])}")
                        print(f"     Detected: {dep['detected_date'][:10]}")
                
                return True
            else:
                print(f"❌ Failed to get history: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting history: {e}")
            return False
    
    def run_interactive_test(self):
        """Run an interactive test session"""
        print("\n" + "="*60)
        print("DEPARTURE DETECTION TEST SYSTEM")
        print("="*60)
        
        # Check API is running
        if not self.check_api_running():
            print("\n❌ API server is not running!")
            print("Please start it first with:")
            print("  cd employee_tracker")
            print("  python api_v2.py")
            return
        
        print("\n✅ API server is running at http://localhost:8002")
        
        while True:
            print("\n" + "-"*40)
            print("Choose an option:")
            print("  1. Run TEST departure check (simulates departure, no credits)")
            print("  2. View tracked employees")
            print("  3. View departure history")
            print("  4. Exit")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                self.run_test_departure_check()
            elif choice == '2':
                self.get_tracked_employees()
            elif choice == '3':
                self.view_departure_history()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")


def main():
    """Run the manual database test"""
    print("\n🔧 MANUAL TEST SYSTEM FOR DEPARTURE DETECTION")
    print("="*60)
    print("\nThis test uses the /check/test endpoint which simulates")
    print("departures without using PDL credits.")
    print("\nThe test endpoint:")
    print("• Picks a random tracked employee")
    print("• Simulates them leaving to a startup")
    print("• Runs classification logic")
    print("• Shows what alert would be sent")
    print("\nNO CREDITS ARE USED!")
    
    tester = ManualDatabaseTesterFixed()
    tester.run_interactive_test()


if __name__ == "__main__":
    main()