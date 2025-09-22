"""
Quick check to see what's actually in your Railway PostgreSQL database
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def quick_check():
    """Quick check of what's in the database"""

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ No DATABASE_URL found")
        print("\nTo test your Railway database locally:")
        print("1. Copy the DATABASE_URL from Railway dashboard")
        print("2. Add to .env file: DATABASE_URL=postgresql://...")
        print("3. Run this script again")
        return

    # Fix postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print(f"Connecting to: {database_url[:50]}...")

    try:
        # Parse URL
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port or 5432
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print("\n" + "="*60)
        print("EMPLOYEES IN DATABASE")
        print("="*60)

        # Count all employees
        cursor.execute("SELECT COUNT(*) as count FROM tracked_employees")
        total = cursor.fetchone()['count']
        print(f"\nTotal employees in database: {total}")

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM tracked_employees
            GROUP BY status
        """)

        print("\nBy status:")
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['count']}")

        # Get latest 10 employees
        cursor.execute("""
            SELECT pdl_id, name, company, status, tracking_started, added_date
            FROM tracked_employees
            ORDER BY added_date DESC NULLS LAST, tracking_started DESC NULLS LAST
            LIMIT 10
        """)

        employees = cursor.fetchall()

        if employees:
            print(f"\nLatest {len(employees)} employees added:")
            for i, emp in enumerate(employees, 1):
                added = emp.get('added_date') or emp.get('tracking_started')
                print(f"{i}. {emp['name']}")
                print(f"   Company: {emp['company']}")
                print(f"   Status: {emp['status']}")
                print(f"   PDL ID: {emp['pdl_id']}")
                print(f"   Added: {added}")
                print()
        else:
            print("\n❌ No employees found in database!")

        # Check if there are any rows with NULL or empty status
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tracked_employees
            WHERE status IS NULL OR status = ''
        """)
        null_status = cursor.fetchone()['count']

        if null_status > 0:
            print(f"⚠️  WARNING: {null_status} employees have NULL or empty status!")
            print("   This might be why they don't show up!")

        # Check company_config
        cursor.execute("SELECT * FROM company_config")
        configs = cursor.fetchall()

        if configs:
            print("\n" + "="*60)
            print("COMPANY CONFIGURATIONS")
            print("="*60)
            for config in configs:
                print(f"  {config['company']}: {config['employee_count']} employees")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_our_classes():
    """Test using our database classes"""
    print("\n" + "="*60)
    print("TESTING OUR DATABASE CLASSES")
    print("="*60)

    try:
        from scripts.database_factory import TrackingDatabase

        db = TrackingDatabase()

        # Test get_all_employees
        all_employees = db.get_all_employees()
        print(f"db.get_all_employees() returns: {len(all_employees)} employees")

        # Test get_all_employees('active')
        active = db.get_all_employees('active')
        print(f"db.get_all_employees('active') returns: {len(active)} employees")

        # Test get_statistics
        stats = db.get_statistics()
        print(f"\ndb.get_statistics():")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_check()
    test_our_classes()

    print("\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)
    print("\nIf employees are in the database but don't show in the UI:")
    print("1. Check their status - must be 'active' to show")
    print("2. Check if get_all_employees() is returning them")
    print("3. Check for NULL values in critical fields")
    print("\nIf the database is empty:")
    print("1. Check API_KEY is set in Railway")
    print("2. Check PDL API is returning employees")
    print("3. Check for errors in Railway logs")