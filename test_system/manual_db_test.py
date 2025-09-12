"""
Manual Database Test for Departure Detection
Tests the real system without using PDL credits
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class ManualDatabaseTester:
    """Test departure detection by manually modifying the database"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
        if not self.db_path.exists():
            print(f"❌ Database not found at {self.db_path}")
            print("Please run the main system at least once to create the database.")
            sys.exit(1)
    
    def add_test_employee(self):
        """Add a test employee to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        test_employee = {
            'pdl_id': 'test_manual_001',
            'name': 'Test Employee (Manual)',
            'company': 'OpenAI',
            'title': 'Senior Engineer',
            'linkedin_url': 'linkedin.com/in/testemployee',
            'current_company': 'OpenAI',
            'status': 'active',
            'tracking_started': datetime.now().isoformat()
        }
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO tracked_employees 
                (pdl_id, name, company, title, linkedin_url, current_company, status, tracking_started)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_employee['pdl_id'],
                test_employee['name'],
                test_employee['company'],
                test_employee['title'],
                test_employee['linkedin_url'],
                test_employee['current_company'],
                test_employee['status'],
                test_employee['tracking_started']
            ))
            conn.commit()
            print(f"✅ Added test employee: {test_employee['name']}")
            return test_employee['pdl_id']
        except Exception as e:
            print(f"❌ Error adding test employee: {e}")
            return None
        finally:
            conn.close()
    
    def simulate_departure(self, pdl_id, scenario='level_3'):
        """Simulate different departure scenarios"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        scenarios = {
            'level_1': {
                'current_company': 'Microsoft',
                'full_data': {
                    'job_company_size': '10000+',
                    'job_company_type': 'technology',
                    'job_title': 'Principal Engineer',
                    'headline': 'Principal Engineer at Microsoft',
                    'summary': 'Joining Microsoft Azure team'
                }
            },
            'level_2': {
                'current_company': 'Stealth Startup',
                'full_data': {
                    'job_company_size': '',
                    'job_company_type': '',
                    'job_title': 'Founder',
                    'headline': 'Building something new in AI | Ex-OpenAI',
                    'summary': 'After years at OpenAI, working on an exciting new project in stealth mode'
                }
            },
            'level_3': {
                'current_company': 'TinyAI Startup',
                'full_data': {
                    'job_company_size': '1-10',
                    'job_company_type': 'startup',
                    'job_title': 'CTO & Co-Founder',
                    'job_company_founded': '2024',
                    'headline': 'CTO & Co-Founder at TinyAI | Building next-gen AI tools',
                    'summary': 'Excited to announce I co-founded TinyAI!'
                }
            }
        }
        
        if scenario not in scenarios:
            print(f"❌ Invalid scenario. Choose from: {list(scenarios.keys())}")
            return False
        
        update_data = scenarios[scenario]
        
        try:
            cursor.execute("""
                UPDATE tracked_employees 
                SET 
                    current_company = ?,
                    job_last_changed = ?,
                    full_data = ?
                WHERE pdl_id = ?
            """, (
                update_data['current_company'],
                datetime.now().isoformat(),
                json.dumps(update_data['full_data']),
                pdl_id
            ))
            conn.commit()
            
            print(f"✅ Simulated {scenario} departure:")
            print(f"   Changed company to: {update_data['current_company']}")
            if scenario == 'level_3':
                print(f"   Expected: 🔴 Level 3 Alert (HIGH PRIORITY)")
            elif scenario == 'level_2':
                print(f"   Expected: 🟠 Level 2 Alert (BUILDING SIGNALS)")
            else:
                print(f"   Expected: 🟡 Level 1 Alert (STANDARD)")
            
            return True
        except Exception as e:
            print(f"❌ Error simulating departure: {e}")
            return False
        finally:
            conn.close()
    
    def check_results(self, pdl_id):
        """Check if departure was detected and classified"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check departures table
            cursor.execute("""
                SELECT * FROM departures 
                WHERE pdl_id = ?
                ORDER BY detected_date DESC
                LIMIT 1
            """, (pdl_id,))
            
            departure = cursor.fetchone()
            
            if departure:
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                dep_dict = dict(zip(columns, departure))
                
                print("\n📊 Departure Detection Results:")
                print("-" * 40)
                print(f"Name: {dep_dict.get('name', 'Unknown')}")
                print(f"Old Company: {dep_dict.get('old_company', 'Unknown')}")
                print(f"New Company: {dep_dict.get('new_company', 'Unknown')}")
                
                alert_level = dep_dict.get('alert_level', 0)
                if alert_level == 3:
                    print(f"Alert Level: 🔴 Level 3 (HIGH PRIORITY)")
                elif alert_level == 2:
                    print(f"Alert Level: 🟠 Level 2 (BUILDING SIGNALS)")
                elif alert_level == 1:
                    print(f"Alert Level: 🟡 Level 1 (STANDARD)")
                else:
                    print(f"Alert Level: Unknown ({alert_level})")
                
                signals = dep_dict.get('alert_signals')
                if signals:
                    try:
                        signals_list = json.loads(signals) if isinstance(signals, str) else signals
                        if signals_list:
                            print(f"Signals Detected: {', '.join(signals_list[:3])}")
                    except:
                        pass
                
                print(f"Detected: {dep_dict.get('detected_date', 'Unknown')}")
                return True
            else:
                print("\n⚠️ No departure found in database yet.")
                print("Run the departure check through the API or UI to detect it.")
                return False
                
        except Exception as e:
            print(f"❌ Error checking results: {e}")
            return False
        finally:
            conn.close()
    
    def cleanup(self, pdl_id):
        """Clean up test data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM tracked_employees WHERE pdl_id = ?", (pdl_id,))
            cursor.execute("DELETE FROM departures WHERE pdl_id = ?", (pdl_id,))
            conn.commit()
            print(f"✅ Cleaned up test data for {pdl_id}")
        except Exception as e:
            print(f"❌ Error cleaning up: {e}")
        finally:
            conn.close()
    
    def run_interactive_test(self):
        """Run an interactive test session"""
        print("\n" + "="*60)
        print("MANUAL DATABASE TEST - Departure Detection")
        print("="*60)
        print("\nThis test modifies your real database to test departure detection")
        print("without using any PDL credits.\n")
        
        # Step 1: Add test employee
        print("Step 1: Adding test employee to database...")
        pdl_id = self.add_test_employee()
        if not pdl_id:
            return
        
        # Step 2: Choose scenario
        print("\nStep 2: Choose departure scenario to test:")
        print("  1. Level 1 - Standard (OpenAI → Microsoft)")
        print("  2. Level 2 - Building Signals (OpenAI → Stealth)")
        print("  3. Level 3 - Startup (OpenAI → TinyAI Startup)")
        
        choice = input("\nEnter choice (1-3): ").strip()
        scenario_map = {'1': 'level_1', '2': 'level_2', '3': 'level_3'}
        scenario = scenario_map.get(choice, 'level_3')
        
        # Step 3: Simulate departure
        print(f"\nStep 3: Simulating {scenario} departure...")
        if not self.simulate_departure(pdl_id, scenario):
            return
        
        # Step 4: Instructions
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("\n1. Run the departure check using one of these methods:")
        print("   a) Web UI: Click 'Check for Departures' button")
        print("   b) API: POST http://localhost:8000/track/departure-check")
        print("   c) Script: python scripts/employee_tracker.py")
        print("\n2. After running the check, press Enter to see results...")
        
        input()
        
        # Step 5: Check results
        print("\nStep 5: Checking results...")
        self.check_results(pdl_id)
        
        # Step 6: Cleanup
        print("\n" + "="*60)
        cleanup = input("\nClean up test data? (y/n): ").strip().lower()
        if cleanup == 'y':
            self.cleanup(pdl_id)
        else:
            print(f"Test data left in database. PDL ID: {pdl_id}")
        
        print("\n✅ Test complete!")


def main():
    """Run the manual database test"""
    tester = ManualDatabaseTester()
    tester.run_interactive_test()


if __name__ == "__main__":
    main()