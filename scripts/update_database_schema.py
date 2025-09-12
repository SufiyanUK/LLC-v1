"""
Update Database Schema - Add Alert Level Columns
This script adds the missing columns needed for the 3-level alert system
"""

import sqlite3
from pathlib import Path

def update_database_schema():
    """Add alert level columns to existing database"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE SCHEMA UPDATE")
    print("="*60)
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(departures)")
    columns = [col[1] for col in cursor.fetchall()]
    
    updates_needed = []
    
    # List of columns to add if they don't exist
    new_columns = [
        ('alert_level', 'INTEGER DEFAULT 1'),
        ('alert_signals', 'JSON'),
        ('headline', 'TEXT'),
        ('summary', 'TEXT'),
        ('job_summary', 'TEXT'),
        ('job_company_type', 'TEXT'),
        ('job_company_size', 'TEXT'),
        ('job_company_founded', 'TEXT'),
        ('job_company_industry', 'TEXT')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            updates_needed.append((col_name, col_type))
    
    if not updates_needed:
        print("\n[OK] Database schema is already up to date!")
        return True
    
    # Add missing columns
    print(f"\n[INFO] Adding {len(updates_needed)} missing columns...")
    
    for col_name, col_type in updates_needed:
        try:
            cursor.execute(f"ALTER TABLE departures ADD COLUMN {col_name} {col_type}")
            print(f"  [OK] Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"  [INFO] Column {col_name} already exists")
            else:
                print(f"  [ERROR] Error adding {col_name}: {e}")
    
    # Also check tracked_employees table for full_data column
    cursor.execute("PRAGMA table_info(tracked_employees)")
    emp_columns = [col[1] for col in cursor.fetchall()]
    
    if 'full_data' not in emp_columns:
        try:
            cursor.execute("ALTER TABLE tracked_employees ADD COLUMN full_data JSON")
            print(f"  [OK] Added column: full_data to tracked_employees")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  [ERROR] Error adding full_data: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify the update
    print("\n[VERIFY] Verifying schema update...")
    cursor.execute("PRAGMA table_info(departures)")
    final_columns = [col[1] for col in cursor.fetchall()]
    
    if 'alert_level' in final_columns and 'alert_signals' in final_columns:
        print("[SUCCESS] Schema update successful!")
        
        # Show current schema
        print("\n[INFO] Current departures table columns:")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
        return True
    else:
        print("[ERROR] Schema update may have failed")
        return False
    
    conn.close()

def check_and_fix_existing_departures():
    """Update existing departures with default alert levels"""
    db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for existing departures without alert levels
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM departures 
            WHERE alert_level IS NULL OR alert_level = 0
        """)
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"\n[INFO] Found {count} departures without alert levels")
            print("  Setting them to Level 1 (standard departure)...")
            
            cursor.execute("""
                UPDATE departures 
                SET alert_level = 1 
                WHERE alert_level IS NULL OR alert_level = 0
            """)
            conn.commit()
            print(f"  [OK] Updated {count} departures")
    except sqlite3.OperationalError:
        # Column doesn't exist yet, will be added
        pass
    
    conn.close()

def main():
    """Run the database update"""
    print("\n[UPDATE] DATABASE SCHEMA UPDATER")
    print("This will add the missing columns needed for the alert system")
    
    # Update schema
    if update_database_schema():
        # Fix existing records
        check_and_fix_existing_departures()
        
        print("\n" + "="*60)
        print("[SUCCESS] DATABASE UPDATE COMPLETE!")
        print("="*60)
        print("\nYour database now supports the 3-level alert system:")
        print("  [LEVEL 3] - Startup/Founder alerts")
        print("  [LEVEL 2] - Building signals alerts")
        print("  [LEVEL 1] - Standard departure alerts")
        print("\nYou can now run departure checks without errors!")
    else:
        print("\n[ERROR] Database update failed")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()