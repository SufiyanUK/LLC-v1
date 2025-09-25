"""
Migration script to transfer tracked employees from SQLite to PostgreSQL
Transfers all data from local SQLite database to Railway PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import Json
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_postgres_tables(pg_conn):
    """Create tables in PostgreSQL if they don't exist"""
    cursor = pg_conn.cursor()

    # Create tracked_employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_employees (
            pdl_id TEXT PRIMARY KEY,
            name TEXT,
            company TEXT,
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

    # Create company_config table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_config (
            company TEXT PRIMARY KEY,
            employee_count INTEGER DEFAULT 5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create departures table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departures (
            id SERIAL PRIMARY KEY,
            pdl_id TEXT,
            name TEXT,
            original_company TEXT,
            new_company TEXT,
            detected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            job_change_date TEXT,
            alert_sent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (pdl_id) REFERENCES tracked_employees(pdl_id)
        )
    """)

    # Create fetch_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fetch_history (
            id SERIAL PRIMARY KEY,
            company TEXT,
            fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            employees_fetched INTEGER,
            credits_used INTEGER,
            status TEXT
        )
    """)

    # Create scheduler_state table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduler_state (
            id SERIAL PRIMARY KEY,
            last_check TIMESTAMP,
            next_check TIMESTAMP,
            check_interval_hours INTEGER DEFAULT 24,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)

    pg_conn.commit()
    print("✓ PostgreSQL tables created/verified")

def migrate_tracked_employees(sqlite_conn, pg_conn):
    """Migrate tracked_employees table"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all employees from SQLite
    sqlite_cursor.execute("""
        SELECT pdl_id, name, company, title, linkedin_url,
               tracking_started, last_checked, status, current_company,
               job_last_changed, full_data, added_date
        FROM tracked_employees
    """)

    employees = sqlite_cursor.fetchall()
    print(f"\nFound {len(employees)} employees to migrate")

    # Insert into PostgreSQL
    migrated = 0
    skipped = 0

    for emp in employees:
        try:
            # Parse JSON data if it's a string
            full_data = emp[10]
            if isinstance(full_data, str):
                full_data = json.loads(full_data) if full_data else None

            pg_cursor.execute("""
                INSERT INTO tracked_employees
                (pdl_id, name, company, title, linkedin_url, tracking_started,
                 last_checked, status, current_company, job_last_changed, full_data, added_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pdl_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    title = EXCLUDED.title,
                    last_checked = EXCLUDED.last_checked,
                    status = EXCLUDED.status,
                    current_company = EXCLUDED.current_company,
                    job_last_changed = EXCLUDED.job_last_changed,
                    full_data = EXCLUDED.full_data
            """, (
                emp[0], emp[1], emp[2], emp[3], emp[4], emp[5],
                emp[6], emp[7], emp[8], emp[9], Json(full_data), emp[11]
            ))
            migrated += 1
            print(f"  ✓ Migrated: {emp[1]} ({emp[2]})")
        except Exception as e:
            print(f"  ✗ Failed to migrate {emp[1]}: {e}")
            skipped += 1

    pg_conn.commit()
    print(f"\nMigrated {migrated} employees, skipped {skipped}")
    return migrated

def migrate_company_config(sqlite_conn, pg_conn):
    """Migrate company_config table"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all company configs from SQLite
    sqlite_cursor.execute("SELECT company, employee_count, last_updated FROM company_config")
    configs = sqlite_cursor.fetchall()

    print(f"\nFound {len(configs)} company configurations to migrate")

    for config in configs:
        try:
            pg_cursor.execute("""
                INSERT INTO company_config (company, employee_count, last_updated)
                VALUES (%s, %s, %s)
                ON CONFLICT (company) DO UPDATE SET
                    employee_count = EXCLUDED.employee_count,
                    last_updated = EXCLUDED.last_updated
            """, config)
            print(f"  ✓ Migrated config: {config[0]} ({config[1]} employees)")
        except Exception as e:
            print(f"  ✗ Failed to migrate config {config[0]}: {e}")

    pg_conn.commit()

def verify_migration(pg_conn):
    """Verify the migration was successful"""
    cursor = pg_conn.cursor()

    print("\n" + "="*60)
    print("MIGRATION VERIFICATION")
    print("="*60)

    # Check tracked_employees
    cursor.execute("SELECT COUNT(*) FROM tracked_employees")
    emp_count = cursor.fetchone()[0]
    print(f"✓ Tracked employees in PostgreSQL: {emp_count}")

    # Check company_config
    cursor.execute("SELECT COUNT(*) FROM company_config")
    config_count = cursor.fetchone()[0]
    print(f"✓ Company configurations: {config_count}")

    # Show sample employees
    cursor.execute("""
        SELECT name, company, title
        FROM tracked_employees
        LIMIT 5
    """)
    samples = cursor.fetchall()
    print("\nSample migrated employees:")
    for sample in samples:
        print(f"  - {sample[0]} | {sample[1]} | {sample[2][:40] if sample[2] else 'N/A'}")

    # Show companies
    cursor.execute("SELECT company, employee_count FROM company_config ORDER BY company")
    companies = cursor.fetchall()
    print("\nCompanies configured:")
    for company in companies:
        print(f"  - {company[0]}: {company[1]} employees")

def main():
    """Main migration function"""
    print("="*60)
    print("SQLITE TO POSTGRESQL MIGRATION")
    print("="*60)

    # Get database connection strings
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: No DATABASE_URL found in .env file")
        print("Please ensure your .env file contains the PostgreSQL connection string")
        return

    sqlite_db_path = 'data/tracking.db'

    if not os.path.exists(sqlite_db_path):
        print(f"ERROR: SQLite database not found at {sqlite_db_path}")
        return

    print(f"Source: {sqlite_db_path}")
    print(f"Target: PostgreSQL (Railway)")
    print()

    try:
        # Connect to databases
        print("Connecting to databases...")
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        pg_conn = psycopg2.connect(database_url)
        print("✓ Connected to both databases")

        # Create tables in PostgreSQL
        create_postgres_tables(pg_conn)

        # Migrate data
        migrate_tracked_employees(sqlite_conn, pg_conn)
        migrate_company_config(sqlite_conn, pg_conn)

        # Verify migration
        verify_migration(pg_conn)

        print("\n" + "="*60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)

    except Exception as e:
        print(f"\nERROR during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main()