"""
Complete Test for Level 2 Alert Generation
This demonstrates that Level 2 alerts work correctly
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.database import TrackingDatabase
from scripts.departure_classifier import DepartureClassifier

def test_level2_complete():
    """Test Level 2 alert generation end-to-end"""
    
    print("\n" + "="*60)
    print("LEVEL 2 ALERT TEST")
    print("="*60)
    
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    
    if not db_path.exists():
        print("[ERROR] Database not found. Please track some employees first.")
        return
    
    # Step 1: Add a test employee
    print("\n[STEP 1] Adding test employee to database...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    test_employee = {
        'pdl_id': 'test_level2_001',
        'name': 'Test Level2 User',
        'company': 'OpenAI',
        'title': 'Senior Engineer',
        'current_company': 'OpenAI',  # Initially same as company
        'status': 'active',
        'tracking_started': datetime.now().isoformat()
    }
    
    # Insert or update
    cursor.execute("""
        INSERT OR REPLACE INTO tracked_employees 
        (pdl_id, name, company, title, current_company, status, tracking_started)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        test_employee['pdl_id'],
        test_employee['name'],
        test_employee['company'],
        test_employee['title'],
        test_employee['current_company'],
        test_employee['status'],
        test_employee['tracking_started']
    ))
    conn.commit()
    
    print(f"  Added: {test_employee['name']} at {test_employee['company']}")
    
    # Step 2: Simulate Level 2 departure
    print("\n[STEP 2] Simulating Level 2 departure (Building signals)...")
    
    level2_data = {
        'job_company_name': 'Independent Consultant',
        'job_company_size': '',
        'job_company_type': '',
        'job_title': 'AI Consultant',
        'headline': 'Building something new in AI | Ex-OpenAI',
        'summary': 'Working on exciting stealth project. Stay tuned!',
        'job_summary': 'Developing next-gen AI tools'
    }
    
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
        test_employee['pdl_id']
    ))
    conn.commit()
    
    print(f"  Changed company to: {level2_data['job_company_name']}")
    print(f"  Headline: {level2_data['headline']}")
    
    # Step 3: Run departure detection
    print("\n[STEP 3] Running departure detection...")
    
    # Get the employee from database
    cursor.execute("""
        SELECT * FROM tracked_employees WHERE pdl_id = ?
    """, (test_employee['pdl_id'],))
    
    row = cursor.fetchone()
    if not row:
        print("[ERROR] Employee not found")
        return
    
    # Parse the data
    columns = [desc[0] for desc in cursor.description]
    emp = dict(zip(columns, row))
    
    # Check for departure
    original_company = emp['company'].lower()
    current_company = emp['current_company'].lower()
    
    if original_company != current_company:
        print(f"  [DEPARTURE DETECTED]")
        print(f"    From: {emp['company']} -> To: {emp['current_company']}")
        
        # Parse full_data
        full_data = json.loads(emp['full_data']) if emp['full_data'] else {}
        
        # Create departure record
        departure = {
            'pdl_id': emp['pdl_id'],
            'name': emp['name'],
            'old_company': emp['company'],
            'new_company': emp['current_company'],
            'headline': full_data.get('headline', ''),
            'summary': full_data.get('summary', ''),
            'job_summary': full_data.get('job_summary', ''),
            'job_company_type': full_data.get('job_company_type', ''),
            'job_company_size': full_data.get('job_company_size', ''),
            'job_title': full_data.get('job_title', ''),
            'new_title': full_data.get('job_title', '')
        }
        
        # Step 4: Classify the departure
        print("\n[STEP 4] Classifying departure...")
        
        classifier = DepartureClassifier()
        alert_level, signals = classifier.classify_departure(departure)
        
        print(f"  Alert Level: {alert_level}")
        print(f"  Classification: ", end="")
        
        if alert_level == 3:
            print("[LEVEL 3] Startup/Founder")
        elif alert_level == 2:
            print("[LEVEL 2] Building Signals")
        elif alert_level == 1:
            print("[LEVEL 1] Standard Departure")
        else:
            print("[LEVEL 0] No Alert")
        
        if signals:
            print(f"  Signals detected:")
            for signal in signals[:5]:
                print(f"    - {signal}")
        
        # Verify it's Level 2
        if alert_level == 2:
            print("\n[SUCCESS] Level 2 alert correctly generated!")
        else:
            print(f"\n[ERROR] Expected Level 2, got Level {alert_level}")
    else:
        print("[ERROR] No departure detected")
    
    # Step 5: Clean up
    print("\n[STEP 5] Cleaning up test data...")
    cursor.execute("DELETE FROM tracked_employees WHERE pdl_id = ?", (test_employee['pdl_id'],))
    cursor.execute("DELETE FROM departures WHERE pdl_id = ?", (test_employee['pdl_id'],))
    conn.commit()
    conn.close()
    
    print("  Test data cleaned up")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_level2_complete()