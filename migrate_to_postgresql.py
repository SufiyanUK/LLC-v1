#!/usr/bin/env python3
"""
Migrate data from local SQLite to Railway PostgreSQL
This script transfers all employee tracking data to Railway
"""

import os
import sys
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

def parse_database_url(database_url):
    """Parse DATABASE_URL into connection parameters"""
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    result = urlparse(database_url)
    return {
        'database': result.path[1:],
        'user': result.username,
        'password': result.password,
        'host': result.hostname,
        'port': result.port or 5432
    }

def get_sqlite_data():
    """Get all data from SQLite database"""
    print("\n📖 Reading from SQLite database...")

    # Find SQLite database
    db_path = Path('data/tracking.db')
    if not db_path.exists():
        print(f"❌ SQLite database not found at {db_path}")
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    data = {}

    # Get tracked employees
    cursor.execute("SELECT * FROM tracked_employees")
    employees = [dict(row) for row in cursor.fetchall()]
    data['employees'] = employees
    print(f"   Found {len(employees)} employees")

    # Get departures
    cursor.execute("SELECT * FROM departures")
    departures = [dict(row) for row in cursor.fetchall()]
    data['departures'] = departures
    print(f"   Found {len(departures)} departures")

    # Get company config
    cursor.execute("SELECT * FROM company_config")
    companies = [dict(row) for row in cursor.fetchall()]
    data['companies'] = companies
    print(f"   Found {len(companies)} company configurations")

    # Get fetch history
    cursor.execute("SELECT * FROM fetch_history")
    fetch_history = [dict(row) for row in cursor.fetchall()]
    data['fetch_history'] = fetch_history
    print(f"   Found {len(fetch_history)} fetch history records")

    # Get scheduler state
    cursor.execute("SELECT * FROM scheduler_state")
    scheduler = cursor.fetchone()
    data['scheduler'] = dict(scheduler) if scheduler else None

    conn.close()
    return data

def migrate_to_postgresql(db_config, data):
    """Migrate data to PostgreSQL"""
    print("\n📝 Migrating to PostgreSQL...")

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Migrate employees
        print("\n   Migrating employees...")
        migrated_employees = 0
        for emp in data['employees']:
            try:
                # Parse JSON data
                full_data = emp.get('full_data')
                if full_data and isinstance(full_data, str):
                    try:
                        full_data = json.loads(full_data)
                    except:
                        full_data = {}

                cursor.execute("""
                    INSERT INTO tracked_employees
                    (pdl_id, name, company, title, linkedin_url, tracking_started,
                     last_checked, status, current_company, job_last_changed, full_data, added_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pdl_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        company = EXCLUDED.company,
                        title = EXCLUDED.title,
                        linkedin_url = EXCLUDED.linkedin_url,
                        last_checked = EXCLUDED.last_checked,
                        status = EXCLUDED.status,
                        current_company = EXCLUDED.current_company,
                        job_last_changed = EXCLUDED.job_last_changed,
                        full_data = EXCLUDED.full_data
                """, (
                    emp.get('pdl_id'),
                    emp.get('name'),
                    emp.get('company'),
                    emp.get('title'),
                    emp.get('linkedin_url'),
                    emp.get('tracking_started'),
                    emp.get('last_checked'),
                    emp.get('status', 'active'),
                    emp.get('current_company'),
                    emp.get('job_last_changed'),
                    json.dumps(full_data) if full_data else None,
                    emp.get('added_date')
                ))
                migrated_employees += 1
            except Exception as e:
                print(f"      Warning: Failed to migrate employee {emp.get('name')}: {e}")

        print(f"      ✅ Migrated {migrated_employees}/{len(data['employees'])} employees")

        # Migrate departures
        print("\n   Migrating departures...")
        migrated_departures = 0
        for dep in data['departures']:
            try:
                # Parse JSON data
                alert_signals = dep.get('alert_signals')
                if alert_signals and isinstance(alert_signals, str):
                    try:
                        alert_signals = json.loads(alert_signals)
                    except:
                        alert_signals = []

                cursor.execute("""
                    INSERT INTO departures
                    (pdl_id, name, old_company, old_title, new_company, new_title,
                     departure_date, detected_date, alert_level, alert_signals,
                     headline, summary, job_summary, job_company_type, job_company_size)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    dep.get('pdl_id'),
                    dep.get('name'),
                    dep.get('old_company'),
                    dep.get('old_title'),
                    dep.get('new_company'),
                    dep.get('new_title'),
                    dep.get('departure_date'),
                    dep.get('detected_date'),
                    dep.get('alert_level', 1),
                    json.dumps(alert_signals) if alert_signals else None,
                    dep.get('headline'),
                    dep.get('summary'),
                    dep.get('job_summary'),
                    dep.get('job_company_type'),
                    dep.get('job_company_size')
                ))
                migrated_departures += 1
            except Exception as e:
                print(f"      Warning: Failed to migrate departure: {e}")

        print(f"      ✅ Migrated {migrated_departures}/{len(data['departures'])} departures")

        # Migrate company config
        print("\n   Migrating company configurations...")
        migrated_companies = 0
        for company in data['companies']:
            try:
                cursor.execute("""
                    INSERT INTO company_config (company, employee_count, last_updated)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (company) DO UPDATE SET
                        employee_count = EXCLUDED.employee_count,
                        last_updated = EXCLUDED.last_updated
                """, (
                    company.get('company'),
                    company.get('employee_count'),
                    company.get('last_updated', datetime.now())
                ))
                migrated_companies += 1
            except Exception as e:
                print(f"      Warning: Failed to migrate company {company.get('company')}: {e}")

        print(f"      ✅ Migrated {migrated_companies}/{len(data['companies'])} company configurations")

        # Migrate fetch history
        print("\n   Migrating fetch history...")
        migrated_history = 0
        for history in data['fetch_history']:
            try:
                cursor.execute("""
                    INSERT INTO fetch_history
                    (company, employees_fetched, credits_used, fetch_date, success)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    history.get('company'),
                    history.get('employees_fetched'),
                    history.get('credits_used'),
                    history.get('fetch_date'),
                    history.get('success', True)
                ))
                migrated_history += 1
            except Exception as e:
                print(f"      Warning: Failed to migrate fetch history: {e}")

        print(f"      ✅ Migrated {migrated_history}/{len(data['fetch_history'])} fetch history records")

        # Update scheduler state
        if data['scheduler']:
            print("\n   Migrating scheduler state...")
            try:
                cursor.execute("""
                    UPDATE scheduler_state SET
                        last_check_date = %s,
                        next_check_date = %s,
                        scheduler_enabled = %s,
                        check_count = %s
                    WHERE id = 1
                """, (
                    data['scheduler'].get('last_check_date'),
                    data['scheduler'].get('next_check_date'),
                    data['scheduler'].get('scheduler_enabled', False),
                    data['scheduler'].get('check_count', 0)
                ))
                print("      ✅ Scheduler state updated")
            except Exception as e:
                print(f"      Warning: Failed to update scheduler state: {e}")

        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Verify migration
        print("\n📊 Verification:")
        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        emp_count = cursor.fetchone()[0]
        print(f"   Employees in PostgreSQL: {emp_count}")

        cursor.execute("SELECT COUNT(DISTINCT company) FROM tracked_employees")
        company_count = cursor.fetchone()[0]
        print(f"   Companies tracked: {company_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("SQLITE TO POSTGRESQL MIGRATION")
    print("=" * 60)

    # Get DATABASE_URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("\n⚠️  DATABASE_URL not found!")
        print("   To migrate to Railway, set DATABASE_URL environment variable")
        print("   Example: DATABASE_URL=postgresql://user:pass@host:5432/dbname")
        print("\n   You can find this in your Railway PostgreSQL plugin settings.")
        sys.exit(1)

    print(f"\n📌 Target PostgreSQL: {database_url[:30]}...")

    # Parse connection details
    db_config = parse_database_url(database_url)

    # Test PostgreSQL connection
    try:
        print("\n🔗 Testing PostgreSQL connection...")
        conn = psycopg2.connect(**db_config)
        conn.close()
        print("   ✅ Connection successful!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        sys.exit(1)

    # Get SQLite data
    data = get_sqlite_data()
    if not data:
        sys.exit(1)

    # Show summary
    print("\n📋 Migration Summary:")
    print(f"   Employees to migrate: {len(data['employees'])}")
    print(f"   Departures to migrate: {len(data['departures'])}")
    print(f"   Companies to migrate: {len(data['companies'])}")
    print(f"   Fetch history records: {len(data['fetch_history'])}")

    # Confirm migration
    print("\n⚠️  This will migrate all data to PostgreSQL.")
    response = input("   Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("   Migration cancelled.")
        sys.exit(0)

    # Run migration
    success = migrate_to_postgresql(db_config, data)

    if success:
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print("\n🎉 Your data has been successfully migrated to PostgreSQL!")
        print("   You can now deploy to Railway with all your existing data.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")

if __name__ == "__main__":
    main()