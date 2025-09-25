#!/usr/bin/env python3
"""
Simple migration script without Unicode characters
"""

import os
import sys
import json
import sqlite3
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

# Hardcoded Railway PostgreSQL URL
DATABASE_URL = "postgresql://postgres:nIQohizFkyhIJrZZFNTnbSSrIITShtmz@shuttle.proxy.rlwy.net:47970/railway"

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
    print("\n[READ] Reading from SQLite database...")

    db_path = Path('data/tracking.db')
    if not db_path.exists():
        print(f"[ERROR] SQLite database not found at {db_path}")
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    data = {}

    cursor.execute("SELECT * FROM tracked_employees")
    employees = [dict(row) for row in cursor.fetchall()]
    data['employees'] = employees
    print(f"   Found {len(employees)} employees")

    cursor.execute("SELECT * FROM departures")
    departures = [dict(row) for row in cursor.fetchall()]
    data['departures'] = departures
    print(f"   Found {len(departures)} departures")

    cursor.execute("SELECT * FROM company_config")
    companies = [dict(row) for row in cursor.fetchall()]
    data['companies'] = companies
    print(f"   Found {len(companies)} company configurations")

    cursor.execute("SELECT * FROM fetch_history")
    fetch_history = [dict(row) for row in cursor.fetchall()]
    data['fetch_history'] = fetch_history
    print(f"   Found {len(fetch_history)} fetch history records")

    conn.close()
    return data

def migrate_to_postgresql(db_config, data):
    """Migrate data to PostgreSQL"""
    print("\n[MIGRATE] Migrating to PostgreSQL...")

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Create tables first
        print("\n   Creating tables...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracked_employees (
                pdl_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                title TEXT,
                linkedin_url TEXT,
                tracking_started TIMESTAMP,
                last_checked TIMESTAMP,
                status TEXT DEFAULT 'active',
                current_company TEXT,
                job_last_changed TEXT,
                full_data JSONB,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departures (
                id SERIAL PRIMARY KEY,
                pdl_id TEXT,
                name TEXT,
                old_company TEXT,
                old_title TEXT,
                new_company TEXT,
                new_title TEXT,
                departure_date TEXT,
                detected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_level INTEGER DEFAULT 1,
                alert_signals JSONB,
                headline TEXT,
                summary TEXT,
                job_summary TEXT,
                job_company_type TEXT,
                job_company_size TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_config (
                company TEXT PRIMARY KEY,
                employee_count INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_history (
                id SERIAL PRIMARY KEY,
                company TEXT,
                employees_fetched INTEGER,
                credits_used INTEGER,
                fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_state (
                id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                last_check_date TIMESTAMP,
                next_check_date TIMESTAMP,
                scheduler_enabled BOOLEAN DEFAULT false,
                check_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT INTO scheduler_state (id, scheduler_enabled)
            VALUES (1, false)
            ON CONFLICT (id) DO NOTHING
        """)

        # Migrate employees
        print("\n   Migrating employees...")
        migrated = 0
        for emp in data['employees']:
            try:
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
                        last_checked = EXCLUDED.last_checked,
                        status = EXCLUDED.status,
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
                migrated += 1
            except Exception as e:
                print(f"      Warning: Failed to migrate {emp.get('name')}: {e}")

        print(f"      [OK] Migrated {migrated}/{len(data['employees'])} employees")

        # Migrate companies
        print("\n   Migrating company configurations...")
        migrated = 0
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
                migrated += 1
            except Exception as e:
                print(f"      Warning: Failed to migrate company {company.get('company')}: {e}")

        print(f"      [OK] Migrated {migrated}/{len(data['companies'])} companies")

        conn.commit()
        print("\n[SUCCESS] Migration completed!")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        emp_count = cursor.fetchone()[0]
        print(f"\n[VERIFY] Employees in PostgreSQL: {emp_count}")

        cursor.execute("SELECT COUNT(DISTINCT company) FROM tracked_employees")
        company_count = cursor.fetchone()[0]
        print(f"[VERIFY] Companies tracked: {company_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("SQLITE TO POSTGRESQL MIGRATION")
    print("=" * 60)

    print(f"\n[TARGET] Railway PostgreSQL")

    db_config = parse_database_url(DATABASE_URL)

    # Test connection
    try:
        print("\n[TEST] Testing PostgreSQL connection...")
        conn = psycopg2.connect(**db_config)
        conn.close()
        print("   [OK] Connection successful!")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")
        sys.exit(1)

    # Get SQLite data
    data = get_sqlite_data()
    if not data:
        sys.exit(1)

    # Show summary
    print("\n[SUMMARY] Migration Summary:")
    print(f"   Employees to migrate: {len(data['employees'])}")
    print(f"   Companies to migrate: {len(data['companies'])}")

    # Run migration
    success = migrate_to_postgresql(db_config, data)

    if success:
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print("\n[SUCCESS] Your data has been migrated to Railway PostgreSQL!")
    else:
        print("\n[ERROR] Migration failed. Check the error messages above.")

if __name__ == "__main__":
    main()