"""
Fix Departed Employee Status
This script finds employees who have departures but are still marked as 'active'
and updates their status to 'departed'
"""

import sqlite3
from pathlib import Path

def fix_departed_status():
    """Find and fix inconsistent status for departed employees"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    
    if not db_path.exists():
        print(f"[ERROR] Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("FIXING DEPARTED EMPLOYEE STATUS")
    print("="*60)
    
    # Find employees who have departures but are still marked as active
    cursor.execute("""
        SELECT DISTINCT 
            te.pdl_id,
            te.name,
            te.company,
            te.status,
            te.current_company,
            d.new_company,
            d.detected_date
        FROM tracked_employees te
        INNER JOIN departures d ON te.pdl_id = d.pdl_id
        WHERE te.status = 'active'
        ORDER BY d.detected_date DESC
    """)
    
    inconsistent = cursor.fetchall()
    
    if not inconsistent:
        print("\n[OK] No inconsistent statuses found!")
        print("All departed employees are properly marked.")
        return
    
    print(f"\n[WARNING] Found {len(inconsistent)} employees with inconsistent status:")
    print("-" * 60)
    
    for pdl_id, name, old_company, status, current_company, new_company, detected_date in inconsistent:
        print(f"\n{name}")
        print(f"  PDL ID: {pdl_id[:30]}...")
        print(f"  Original Company: {old_company}")
        print(f"  New Company: {new_company}")
        print(f"  Current Status: {status} (INCORRECT)")
        print(f"  Departure Detected: {detected_date[:10] if detected_date else 'Unknown'}")
    
    # Ask for confirmation
    print("\n" + "-"*60)
    fix = input("\nDo you want to fix these statuses? (y/n): ").strip().lower()
    
    if fix == 'y':
        fixed_count = 0
        for pdl_id, name, _, _, _, new_company, _ in inconsistent:
            cursor.execute("""
                UPDATE tracked_employees 
                SET status = 'departed', 
                    current_company = ?
                WHERE pdl_id = ?
            """, (new_company, pdl_id))
            fixed_count += 1
            print(f"  [FIXED] {name} - status updated to 'departed'")
        
        conn.commit()
        print(f"\n[SUCCESS] Fixed {fixed_count} employee statuses")
    else:
        print("\n[CANCELLED] No changes made")
    
    # Also check for orphaned departures (departures without tracked employees)
    print("\n" + "-"*60)
    print("Checking for orphaned departures...")
    
    cursor.execute("""
        SELECT COUNT(*) FROM departures d
        LEFT JOIN tracked_employees te ON d.pdl_id = te.pdl_id
        WHERE te.pdl_id IS NULL
    """)
    
    orphaned_count = cursor.fetchone()[0]
    
    if orphaned_count > 0:
        print(f"[WARNING] Found {orphaned_count} departure records without tracked employees")
        clean = input("Do you want to remove these orphaned records? (y/n): ").strip().lower()
        
        if clean == 'y':
            cursor.execute("""
                DELETE FROM departures 
                WHERE pdl_id NOT IN (SELECT pdl_id FROM tracked_employees)
            """)
            conn.commit()
            print(f"[SUCCESS] Removed {orphaned_count} orphaned departure records")
    else:
        print("[OK] No orphaned departures found")
    
    conn.close()
    
    print("\n" + "="*60)
    print("STATUS FIX COMPLETE")
    print("="*60)

def show_statistics():
    """Show current database statistics"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count by status
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM tracked_employees 
        GROUP BY status
    """)
    
    status_counts = cursor.fetchall()
    
    print("\n[STATISTICS]")
    print("-" * 40)
    print("Employee Status Distribution:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    # Count departures
    cursor.execute("SELECT COUNT(*) FROM departures")
    departure_count = cursor.fetchone()[0]
    print(f"\nTotal Departures Recorded: {departure_count}")
    
    # Count by alert level
    cursor.execute("""
        SELECT alert_level, COUNT(*) 
        FROM departures 
        WHERE alert_level IS NOT NULL
        GROUP BY alert_level
    """)
    
    alert_counts = cursor.fetchall()
    
    if alert_counts:
        print("\nDepartures by Alert Level:")
        for level, count in alert_counts:
            level_name = {1: "Level 1 (Standard)", 2: "Level 2 (Building)", 3: "Level 3 (Startup)"}
            print(f"  {level_name.get(level, f'Level {level}')}: {count}")
    
    conn.close()

def main():
    """Run the status fix utility"""
    print("\n[EMPLOYEE STATUS FIX UTILITY]")
    print("This tool ensures departed employees are properly marked")
    
    # Show current statistics
    show_statistics()
    
    # Fix inconsistent statuses
    fix_departed_status()
    
    # Show updated statistics
    print("\n[UPDATED STATISTICS]")
    show_statistics()

if __name__ == "__main__":
    main()