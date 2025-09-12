"""
View and Update Employees for Testing Departures
This script helps you simulate departures for testing
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def view_employees():
    """View all active employees in the database"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    
    if not db_path.exists():
        print(f"[ERROR] Database not found at {db_path}")
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT pdl_id, name, company, title, current_company, status
        FROM tracked_employees
        WHERE status = 'active'
        ORDER BY company, name
    """)
    
    employees = cursor.fetchall()
    conn.close()
    
    if not employees:
        print("[ERROR] No active employees found in database")
        print("Please track some employees first using the web UI")
        return []
    
    print("\n" + "="*70)
    print("ACTIVE EMPLOYEES IN DATABASE")
    print("="*70)
    
    for i, (pdl_id, name, company, title, current_company, status) in enumerate(employees, 1):
        print(f"\n{i}. {name}")
        print(f"   PDL ID: {pdl_id[:30]}...")
        print(f"   Original Company: {company}")
        print(f"   Current Company: {current_company or company}")
        print(f"   Title: {title}")
        print(f"   Status: {status}")
    
    return employees

def simulate_departure(pdl_id, scenario='startup'):
    """Update an employee to simulate they left for a new company"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    scenarios = {
        'startup': {
            'company': 'TinyAI Startup',
            'data': {
                'job_company_name': 'TinyAI Startup',
                'job_company_size': '1-10',
                'job_company_founded': '2024',
                'job_title': 'CTO & Co-Founder',
                'headline': 'CTO & Co-Founder at TinyAI | Building next-gen AI tools',
                'summary': 'Excited to announce I co-founded TinyAI! We are building revolutionary AI tools.',
                'job_company_type': 'startup'
            },
            'expected': '[LEVEL 3] Alert (Startup/Founder)'
        },
        'building': {
            'company': 'Independent Consultant',
            'data': {
                'job_company_name': 'Independent Consultant', 
                'job_company_size': '',  # No size = not a startup
                'job_company_type': '',  # No type = not a startup
                'job_company_founded': '',  # No founding date
                'headline': 'Building something new in AI | Ex-OpenAI',
                'summary': 'After amazing years at my previous company, working on something exciting in stealth mode. Stay tuned!',
                'job_title': 'AI Consultant',
                'job_summary': 'Working on stealth AI project'
            },
            'expected': '[LEVEL 2] Alert (Building Signals)'
        },
        'bigtech': {
            'company': 'Microsoft',
            'data': {
                'job_company_name': 'Microsoft',
                'job_company_size': '10000+',
                'job_title': 'Principal Engineer',
                'headline': 'Principal Engineer at Microsoft',
                'job_company_type': 'technology'
            },
            'expected': '[LEVEL 1] Alert (Standard Departure)'
        }
    }
    
    if scenario not in scenarios:
        print(f"[ERROR] Invalid scenario. Choose from: {list(scenarios.keys())}")
        return False
    
    config = scenarios[scenario]
    
    # Update the employee
    cursor.execute("""
        UPDATE tracked_employees 
        SET 
            current_company = ?,
            job_last_changed = ?,
            full_data = ?
        WHERE pdl_id = ?
    """, (
        config['company'],
        datetime.now().isoformat(),
        json.dumps(config['data']),
        pdl_id
    ))
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Successfully simulated departure!")
    print(f"   Changed company to: {config['company']}")
    print(f"   Expected classification: {config['expected']}")
    
    return True

def reset_employee(pdl_id):
    """Reset an employee back to their original company"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Reset to original company
    cursor.execute("""
        UPDATE tracked_employees 
        SET 
            current_company = company,
            job_last_changed = NULL,
            full_data = NULL
        WHERE pdl_id = ?
    """, (pdl_id,))
    
    # Also clean up any test departures
    cursor.execute("DELETE FROM departures WHERE pdl_id = ?", (pdl_id,))
    
    conn.commit()
    conn.close()
    
    print(f"[SUCCESS] Reset employee to original company")

def main():
    """Interactive tool to simulate departures"""
    print("\n" + "="*60)
    print("\nDEPARTURE SIMULATION TOOL")
    print("\nThis tool helps you test the departure detection system")
    print("by manually updating employee companies in the database.")
    print("\n" + "="*60)
    
    # View employees
    employees = view_employees()
    
    if not employees:
        return
    
    print("\n" + "-"*70)
    print("WHAT WOULD YOU LIKE TO DO?")
    print("-"*70)
    print("\n1. Simulate a departure")
    print("2. Reset an employee to original company")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        # Pick employee
        emp_num = input(f"\nEnter employee number (1-{len(employees)}): ").strip()
        try:
            emp_index = int(emp_num) - 1
            if 0 <= emp_index < len(employees):
                pdl_id = employees[emp_index][0]
                name = employees[emp_index][1]
                
                print(f"\nSelected: {name}")
                print("\nChoose departure scenario:")
                print("1. Startup (Level 3 - Red Alert)")
                print("2. Building Something (Level 2 - Orange Alert)")
                print("3. Big Tech (Level 1 - Yellow Alert)")
                
                scenario_choice = input("\nEnter scenario (1-3): ").strip()
                scenario_map = {'1': 'startup', '2': 'building', '3': 'bigtech'}
                scenario = scenario_map.get(scenario_choice, 'startup')
                
                if simulate_departure(pdl_id, scenario):
                    print("\n" + "="*70)
                    print("NEXT STEPS:")
                    print("="*70)
                    print("\n1. Run the test departure check:")
                    print("   cd employee_tracker")
                    print("   python scripts/test_departure_check.py")
                    print("\n2. This will:")
                    print("   - Detect the simulated departure")
                    print("   - Classify it based on the scenario")
                    print("   - Save it to the departures table")
                    print("\n3. View results in the web UI 'Departures' tab")
        except (ValueError, IndexError):
            print("[ERROR] Invalid employee number")
    
    elif choice == '2':
        # Reset employee
        emp_num = input(f"\nEnter employee number to reset (1-{len(employees)}): ").strip()
        try:
            emp_index = int(emp_num) - 1
            if 0 <= emp_index < len(employees):
                pdl_id = employees[emp_index][0]
                reset_employee(pdl_id)
        except (ValueError, IndexError):
            print("[ERROR] Invalid employee number")

if __name__ == "__main__":
    main()