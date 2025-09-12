"""
Simulate Level 2 departure for an existing employee
This will update an employee to show Level 2 building signals
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

def simulate_level2_for_first_employee():
    """Simulate Level 2 departure for the first active employee"""
    
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    
    if not db_path.exists():
        print("[ERROR] Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get first active employee
    cursor.execute("""
        SELECT pdl_id, name, company 
        FROM tracked_employees 
        WHERE status = 'active' 
        LIMIT 1
    """)
    
    employee = cursor.fetchone()
    
    if not employee:
        print("[ERROR] No active employees found")
        return
    
    pdl_id, name, company = employee
    
    print("\n" + "="*60)
    print("SIMULATING LEVEL 2 DEPARTURE")
    print("="*60)
    
    print(f"\nEmployee: {name}")
    print(f"Current Company: {company}")
    
    # Level 2 scenario data
    level2_data = {
        'job_company_name': 'Independent Consultant',
        'job_company_size': '',
        'job_company_type': '',
        'job_company_founded': '',
        'job_title': 'AI Consultant',
        'headline': 'Building something new in AI | Ex-' + company,
        'summary': 'After amazing years at ' + company + ', working on something exciting in stealth mode. Stay tuned!',
        'job_summary': 'Working on stealth AI project'
    }
    
    # Update the employee
    cursor.execute("""
        UPDATE tracked_employees 
        SET 
            current_company = ?,
            job_last_changed = ?,
            full_data = ?
        WHERE pdl_id = ?
    """, (
        level2_data['job_company_name'],
        datetime.now().isoformat(),
        json.dumps(level2_data),
        pdl_id
    ))
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Simulated Level 2 departure!")
    print(f"  New Company: {level2_data['job_company_name']}")
    print(f"  Headline: {level2_data['headline']}")
    print(f"  Expected Alert: [LEVEL 2] Building Signals")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("\n1. Run the departure check:")
    print("   cd employee_tracker")
    print("   python scripts/test_departure_check.py")
    print("\n2. The system should detect:")
    print("   - Departure from", company, "to Independent Consultant")
    print("   - Classification as Level 2 (Building Signals)")
    print("   - Signals: 'building something new', 'stealth mode'")
    print("\n3. Check the web UI 'Departures' tab to see the Level 2 alert")

if __name__ == "__main__":
    simulate_level2_for_first_employee()