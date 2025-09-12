"""
Revert all employees to their original companies and active status
This undoes any test modifications and restores tracking state
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

class EmployeeReverter:
    """Revert employees to original state for active tracking"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
        
        if not self.db_path.exists():
            print("[ERROR] Database not found")
            exit(1)
    
    def revert_all_employees(self):
        """Revert all employees to original companies and active status"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("REVERTING ALL EMPLOYEES TO ORIGINAL STATE")
        print("="*60)
        
        # Get all employees
        cursor.execute("""
            SELECT pdl_id, name, company, current_company, status
            FROM tracked_employees
            ORDER BY company, name
        """)
        
        employees = cursor.fetchall()
        
        if not employees:
            print("\n[ERROR] No employees found in database")
            conn.close()
            return
        
        print(f"\nFound {len(employees)} employees to process")
        print("-" * 40)
        
        reverted_count = 0
        already_correct = 0
        
        for pdl_id, name, original_company, current_company, status in employees:
            # Check if needs reverting
            needs_update = False
            changes = []
            
            if current_company != original_company:
                needs_update = True
                changes.append(f"Company: {current_company} -> {original_company}")
            
            if status != 'active':
                needs_update = True
                changes.append(f"Status: {status} -> active")
            
            if needs_update:
                print(f"\n[REVERTING] {name}")
                for change in changes:
                    print(f"  - {change}")
                
                # Update employee record
                cursor.execute("""
                    UPDATE tracked_employees
                    SET current_company = ?,
                        status = 'active',
                        last_checked = ?
                    WHERE pdl_id = ?
                """, (original_company, datetime.now(), pdl_id))
                
                # Also reset full_data to remove test modifications
                cursor.execute("""
                    SELECT full_data
                    FROM tracked_employees
                    WHERE pdl_id = ?
                """, (pdl_id,))
                
                full_data_row = cursor.fetchone()
                if full_data_row and full_data_row[0]:
                    try:
                        full_data = json.loads(full_data_row[0])
                        # Reset job company name to original
                        if 'job_company_name' in full_data:
                            full_data['job_company_name'] = original_company
                        # Remove test headlines/summaries
                        if 'headline' in full_data and 'Building something new' in full_data.get('headline', ''):
                            full_data['headline'] = f"Senior Engineer at {original_company}"
                        if 'summary' in full_data and 'stealth' in full_data.get('summary', '').lower():
                            full_data['summary'] = ""
                        
                        cursor.execute("""
                            UPDATE tracked_employees
                            SET full_data = ?
                            WHERE pdl_id = ?
                        """, (json.dumps(full_data), pdl_id))
                    except Exception as e:
                        print(f"  [Warning] Could not reset full_data: {e}")
                
                reverted_count += 1
            else:
                already_correct += 1
        
        # Clear all departures from test runs
        cursor.execute("DELETE FROM departures")
        deleted_departures = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Summary
        print("\n" + "="*60)
        print("REVERT COMPLETE")
        print("="*60)
        print(f"\nResults:")
        print(f"  - Employees reverted: {reverted_count}")
        print(f"  - Already correct: {already_correct}")
        print(f"  - Total employees: {len(employees)}")
        print(f"  - Departures cleared: {deleted_departures}")
        
        print("\n[SUCCESS] All employees are now:")
        print("  - Set to their original companies")
        print("  - Status set to 'active'")
        print("  - Ready for real departure checking")
        
        return reverted_count


def main():
    """Run the revert process"""
    print("\n[EMPLOYEE REVERT TOOL]")
    print("This will revert all employees to their original companies")
    print("and set their status to 'active' for tracking.")
    print("\nThis will also clear all test departures from the database.")
    
    response = input("\nDo you want to continue? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("\n[CANCELLED] No changes made.")
        return
    
    reverter = EmployeeReverter()
    reverter.revert_all_employees()
    
    print("\n" + "="*60)
    print("You can now run departure checks with clean data.")
    print("="*60)


if __name__ == "__main__":
    main()