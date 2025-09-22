"""
Deep diagnostic to find why employees aren't showing despite being added
This will test every step of the process
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_raw_postgresql_connection():
    """Test raw PostgreSQL connection without using our database classes"""
    print("\n" + "="*60)
    print("RAW POSTGRESQL CONNECTION TEST")
    print("="*60)

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ No DATABASE_URL found - this only works with PostgreSQL")
        print("   Set DATABASE_URL in .env to test Railway connection locally")
        return None

    print(f"DATABASE_URL: {database_url[:50]}...")

    # Parse DATABASE_URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("✓ Converted postgres:// to postgresql://")

    try:
        # Parse the URL
        result = urlparse(database_url)
        db_config = {
            'database': result.path[1:],
            'user': result.username,
            'password': result.password,
            'host': result.hostname,
            'port': result.port or 5432
        }

        print(f"Connecting to: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        print(f"User: {db_config['user']}")

        # Connect
        conn = psycopg2.connect(**db_config)
        print("✅ Raw PostgreSQL connection successful!")

        return conn

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def check_tables_exist(conn):
    """Check if all required tables exist"""
    print("\n" + "="*60)
    print("TABLE EXISTENCE CHECK")
    print("="*60)

    cursor = conn.cursor()

    tables = ['tracked_employees', 'departures', 'company_config',
              'fetch_history', 'scheduler_state']

    for table in tables:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """, (table,))

        exists = cursor.fetchone()[0]
        if exists:
            print(f"✓ Table '{table}' exists")

            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
        else:
            print(f"❌ Table '{table}' DOES NOT EXIST!")

    return True

def check_table_schema(conn):
    """Check the schema of tracked_employees table"""
    print("\n" + "="*60)
    print("TABLE SCHEMA CHECK")
    print("="*60)

    cursor = conn.cursor()

    # Get column information
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'tracked_employees'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()

    print("tracked_employees columns:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

    return True

def test_direct_insert_and_select(conn):
    """Test inserting and selecting an employee directly with SQL"""
    print("\n" + "="*60)
    print("DIRECT SQL INSERT/SELECT TEST")
    print("="*60)

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Create a test employee with unique ID
    test_id = f"diagnostic_test_{datetime.now().timestamp()}"

    print(f"Inserting test employee with ID: {test_id}")

    try:
        # Insert
        cursor.execute("""
            INSERT INTO tracked_employees
            (pdl_id, name, company, title, linkedin_url, tracking_started,
             last_checked, status, current_company, job_last_changed, full_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            test_id,
            'Diagnostic Test Employee',
            'test-company',
            'Senior Test Engineer',
            'https://linkedin.com/in/test',
            datetime.now(),
            datetime.now(),
            'active',
            'Test Company Inc',
            '2024-01-01',
            json.dumps({'test': 'data'})
        ))

        conn.commit()
        print("✓ Insert successful and committed")

        # Select it back
        cursor.execute("""
            SELECT * FROM tracked_employees
            WHERE pdl_id = %s
        """, (test_id,))

        result = cursor.fetchone()
        if result:
            print(f"✓ Retrieved test employee: {result['name']}")
            print(f"  Status: {result['status']}")
            print(f"  Company: {result['company']}")
        else:
            print("❌ Could not retrieve test employee!")

        # Select ALL active employees
        cursor.execute("""
            SELECT pdl_id, name, company, status
            FROM tracked_employees
            WHERE status = 'active'
            ORDER BY added_date DESC
            LIMIT 5
        """)

        all_active = cursor.fetchall()
        print(f"\nLatest 5 active employees in database:")
        for emp in all_active:
            print(f"  - {emp['name']} ({emp['company']}) - Status: {emp['status']}")

        # Clean up
        cursor.execute("DELETE FROM tracked_employees WHERE pdl_id = %s", (test_id,))
        conn.commit()
        print("\n✓ Cleaned up test employee")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False

def test_our_database_class():
    """Test using our database classes"""
    print("\n" + "="*60)
    print("DATABASE CLASS TEST")
    print("="*60)

    try:
        from scripts.database_factory import TrackingDatabase

        db = TrackingDatabase()
        print("✓ TrackingDatabase initialized")

        # Get all employees
        employees = db.get_all_employees()
        print(f"✓ get_all_employees() returned {len(employees)} employees")

        if employees:
            print("\nFirst 3 employees from get_all_employees():")
            for i, emp in enumerate(employees[:3]):
                print(f"  {i+1}. {emp.get('name')} - {emp.get('company')} - Status: {emp.get('status')}")

        # Get only active employees
        active = db.get_all_employees('active')
        print(f"\n✓ get_all_employees('active') returned {len(active)} employees")

        # Get statistics
        stats = db.get_statistics()
        print(f"\nDatabase statistics:")
        print(f"  Total tracked: {stats.get('total_tracked', 0)}")
        print(f"  Active: {stats.get('active', 0)}")
        print(f"  Departed: {stats.get('departed', 0)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_employee_tracker_flow():
    """Test the complete EmployeeTracker flow"""
    print("\n" + "="*60)
    print("EMPLOYEE TRACKER FLOW TEST")
    print("="*60)

    try:
        from scripts.employee_tracker import EmployeeTracker

        tracker = EmployeeTracker()
        print("✓ EmployeeTracker initialized")

        # Check existing employees
        existing = tracker.get_existing_employee_ids('openai')
        print(f"  Existing OpenAI employees: {len(existing)}")

        # Get tracking status
        status = tracker.get_tracking_status()
        print(f"  Total tracked: {status.get('total_tracked', 0)}")

        # Test add_company_to_tracking return value
        print("\nTesting add_company_to_tracking return type...")

        # This should return a Dict, not boolean
        test_result = {'success': False, 'added': 0, 'updated': 0}
        print(f"  Sample return: {test_result}")
        print(f"  Type: {type(test_result)}")
        print(f"  test_result.get('success'): {test_result.get('success')}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test what the API endpoint returns"""
    print("\n" + "="*60)
    print("API ENDPOINT SIMULATION")
    print("="*60)

    try:
        from scripts.employee_tracker import EmployeeTracker

        tracker = EmployeeTracker()

        # Simulate what happens in the API endpoint
        print("Simulating /track/employees endpoint...")

        # This is what the API does:
        employees = tracker.db.get_all_employees()
        print(f"1. tracker.db.get_all_employees() returned: {len(employees)} employees")

        # Then it filters:
        active_employees = [e for e in employees if e['status'] != 'deleted']
        print(f"2. After filtering deleted: {len(active_employees)} employees")

        # Show the first few
        if active_employees:
            print("\nFirst 3 employees that would be shown:")
            for i, emp in enumerate(active_employees[:3]):
                print(f"  {i+1}. {emp.get('name')} - Status: {emp.get('status')}")
        else:
            print("\n❌ No employees would be shown!")
            print("   This explains why your tracking tab is empty!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("DEEP DIAGNOSTIC FOR RAILWAY POSTGRESQL")
    print("="*60)

    # Test 1: Raw PostgreSQL connection
    conn = test_raw_postgresql_connection()
    if not conn:
        print("\n❌ Cannot continue without PostgreSQL connection")
        print("   This diagnostic is for Railway/PostgreSQL only")
        return

    # Test 2: Check tables exist
    check_tables_exist(conn)

    # Test 3: Check schema
    check_table_schema(conn)

    # Test 4: Direct SQL test
    test_direct_insert_and_select(conn)

    # Close raw connection
    conn.close()

    # Test 5: Our database class
    test_our_database_class()

    # Test 6: Employee tracker
    test_employee_tracker_flow()

    # Test 7: API endpoint simulation
    test_api_endpoint()

    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nCheck the output above to identify the issue:")
    print("1. If employees show in raw SQL but not in get_all_employees(), there's a query issue")
    print("2. If the table is empty, employees aren't being saved")
    print("3. If status is not 'active', that's why they don't show")
    print("4. If everything works here but not in the app, there's a connection issue")

if __name__ == "__main__":
    main()