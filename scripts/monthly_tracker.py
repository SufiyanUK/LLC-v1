"""
Monthly tracker to detect employee departures
Compares current employees with previous snapshot to find departures
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.target_companies import TARGET_COMPANIES
from dotenv import load_dotenv

class DepartureTracker:
    """Track employee departures by comparing snapshots"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        if not self.api_key:
            raise ValueError("No API_KEY found in .env file")
        
        self.base_url = "https://api.peopledatalabs.com/v5/person/search"
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Directories
        self.snapshots_dir = Path(__file__).parent.parent / 'data' / 'snapshots'
        self.departures_dir = Path(__file__).parent.parent / 'data' / 'departures'
        self.alerts_dir = Path(__file__).parent.parent / 'data' / 'alerts'
    
    def load_latest_snapshot(self) -> Dict[str, Dict]:
        """Load the most recent snapshot of employees"""
        
        # Find latest master snapshot
        snapshot_files = list(self.snapshots_dir.glob('master_snapshot_*.jsonl'))
        if not snapshot_files:
            print("[ERROR] No previous snapshot found. Run fetch_senior_employees.py first.")
            return {}
        
        latest_snapshot = max(snapshot_files, key=lambda p: p.stat().st_mtime)
        print(f"[LOADING] Previous snapshot: {latest_snapshot.name}")
        
        # Load employees indexed by PDL ID
        employees_by_id = {}
        
        with open(latest_snapshot, 'r', encoding='utf-8') as f:
            for line in f:
                emp = json.loads(line)
                pdl_id = emp.get('id') or emp.get('pdl_id')
                if pdl_id:
                    employees_by_id[pdl_id] = emp
        
        print(f"  Loaded {len(employees_by_id)} employees from snapshot")
        return employees_by_id
    
    def check_current_status(self, employee: Dict) -> Dict:
        """Check if an employee is still at their company"""
        
        pdl_id = employee.get('id') or employee.get('pdl_id')
        if not pdl_id:
            return {'status': 'unknown', 'employee': employee}
        
        # Query PDL for current status
        query = f"SELECT * FROM person WHERE id = '{pdl_id}'"
        
        params = {
            'sql': query,
            'size': 1
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=params)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                
                if records:
                    current = records[0]
                    old_company = employee.get('job_company_name', '').lower()
                    new_company = current.get('job_company_name', '').lower()
                    
                    if old_company != new_company:
                        # They left!
                        return {
                            'status': 'departed',
                            'employee': employee,
                            'old_company': old_company,
                            'new_company': new_company,
                            'new_title': current.get('job_title'),
                            'job_last_changed': current.get('job_last_changed'),
                            'current_data': current
                        }
                    else:
                        return {'status': 'still_there', 'employee': employee}
                else:
                    return {'status': 'not_found', 'employee': employee}
            else:
                return {'status': 'error', 'employee': employee}
                
        except Exception as e:
            print(f"  Error checking {pdl_id}: {str(e)}")
            return {'status': 'error', 'employee': employee}
    
    def check_all_employees(self, sample_size: int = None) -> List[Dict]:
        """Check all employees for departures"""
        
        # Load previous snapshot
        previous_employees = self.load_latest_snapshot()
        if not previous_employees:
            return []
        
        departures = []
        checked = 0
        credits_used = 0
        
        # Sample if specified
        if sample_size:
            import random
            employee_ids = random.sample(list(previous_employees.keys()), 
                                        min(sample_size, len(previous_employees)))
        else:
            employee_ids = list(previous_employees.keys())
        
        print(f"\n[CHECKING] {len(employee_ids)} employees for departures...")
        
        for pdl_id in employee_ids:
            employee = previous_employees[pdl_id]
            checked += 1
            
            if checked % 10 == 0:
                print(f"  Progress: {checked}/{len(employee_ids)} checked, {len(departures)} departures found")
            
            # Check current status
            result = self.check_current_status(employee)
            credits_used += 1
            
            if result['status'] == 'departed':
                departures.append(result)
                print(f"  DEPARTURE: {employee.get('full_name')} left {result['old_company']} -> {result['new_company']}")
        
        print(f"\n[COMPLETE]")
        print(f"  Employees checked: {checked}")
        print(f"  Departures found: {len(departures)}")
        print(f"  Credits used: {credits_used}")
        
        return departures
    
    def save_departures(self, departures: List[Dict]):
        """Save detected departures"""
        if not departures:
            print("[NO DEPARTURES] No departures to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed departure data
        departures_file = self.departures_dir / f"departures_{timestamp}.jsonl"
        
        with open(departures_file, 'w', encoding='utf-8') as f:
            for dep in departures:
                f.write(json.dumps(dep) + '\n')
        
        print(f"\n[SAVED] Departures: {departures_file.name}")
        
        # Create summary
        summary = {
            'timestamp': timestamp,
            'total_departures': len(departures),
            'by_company': {},
            'departures': []
        }
        
        for dep in departures:
            old_company = dep['old_company']
            if old_company not in summary['by_company']:
                summary['by_company'][old_company] = []
            
            departure_info = {
                'name': dep['employee'].get('full_name', 'Unknown'),
                'old_company': old_company,
                'old_title': dep['employee'].get('job_title'),
                'new_company': dep['new_company'],
                'new_title': dep.get('new_title'),
                'job_last_changed': dep.get('job_last_changed')
            }
            
            summary['by_company'][old_company].append(departure_info)
            summary['departures'].append(departure_info)
        
        # Save summary
        summary_file = self.departures_dir / f"departures_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"  Summary: {summary_file.name}")
        
        return departures_file, summary_file
    
    def generate_alerts(self, departures: List[Dict]):
        """Generate alerts for departures"""
        if not departures:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # High priority departures (from key companies)
        key_companies = ['openai', 'anthropic', 'deepmind', 'meta', 'google']
        
        high_priority = []
        normal_priority = []
        
        for dep in departures:
            old_company = dep['old_company']
            if any(key in old_company for key in key_companies):
                high_priority.append(dep)
            else:
                normal_priority.append(dep)
        
        # Create alert file
        alerts = {
            'timestamp': timestamp,
            'total_departures': len(departures),
            'high_priority_count': len(high_priority),
            'high_priority': [],
            'normal_priority': []
        }
        
        # Format high priority alerts
        for dep in high_priority:
            alerts['high_priority'].append({
                'name': dep['employee'].get('full_name'),
                'left': dep['old_company'],
                'joined': dep['new_company'],
                'new_role': dep.get('new_title'),
                'linkedin': dep['employee'].get('linkedin_url'),
                'alert_level': 'HIGH',
                'reason': f"Left key company {dep['old_company']}"
            })
        
        # Format normal priority alerts  
        for dep in normal_priority:
            alerts['normal_priority'].append({
                'name': dep['employee'].get('full_name'),
                'left': dep['old_company'],
                'joined': dep['new_company'],
                'new_role': dep.get('new_title'),
                'linkedin': dep['employee'].get('linkedin_url'),
                'alert_level': 'NORMAL'
            })
        
        # Save alerts
        alerts_file = self.alerts_dir / f"departure_alerts_{timestamp}.json"
        with open(alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=2)
        
        print(f"\n[ALERTS GENERATED]")
        print(f"  File: {alerts_file.name}")
        print(f"  High Priority: {len(high_priority)} departures from key companies")
        print(f"  Normal Priority: {len(normal_priority)} departures")
        
        # Print high priority alerts
        if high_priority:
            print(f"\n[HIGH PRIORITY ALERTS]")
            for alert in alerts['high_priority'][:5]:  # Show first 5
                print(f"  - {alert['name']}: {alert['left']} -> {alert['joined']}")
        
        return alerts_file

def main():
    """Main function to run monthly tracking"""
    
    tracker = DepartureTracker()
    
    print("\n" + "="*60)
    print("MONTHLY DEPARTURE TRACKER")
    print("="*60)
    print("\nThis will check tracked employees for departures")
    
    # Ask for sample size
    sample = input("\nCheck all employees or sample? (all/sample): ").strip().lower()
    
    if sample == 'sample':
        size = input("Sample size (default 50): ").strip()
        sample_size = int(size) if size else 50
    else:
        sample_size = None
        print("\n[WARNING] Checking all employees will use many credits!")
        confirm = input("Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return
    
    # Check for departures
    departures = tracker.check_all_employees(sample_size)
    
    if departures:
        # Save departures
        tracker.save_departures(departures)
        
        # Generate alerts
        tracker.generate_alerts(departures)
    else:
        print("\n[NO DEPARTURES DETECTED]")
    
    print("\n" + "="*60)
    print("TRACKING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()