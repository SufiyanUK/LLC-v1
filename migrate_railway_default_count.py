#!/usr/bin/env python3
"""
Railway Migration: Add default_employee_count column to company_config table

This script can be run manually on Railway or locally to add the missing column
to an existing PostgreSQL database.

Usage:
  python migrate_railway_default_count.py
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

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

def main():
    print("\n" + "="*60)
    print("RAILWAY MIGRATION: Add default_employee_count Column")
    print("="*60)

    # Get DATABASE_URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("\n[ERROR] DATABASE_URL environment variable not found!")
        print("  For Railway: This should be set automatically")
        print("  For local: Set DATABASE_URL to your PostgreSQL connection string")
        sys.exit(1)

    print(f"\n[INFO] Connecting to database...")

    # Parse and connect
    db_config = parse_database_url(database_url)

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        print(f"[OK] Connected to {db_config['host']}/{db_config['database']}")

        # Check if company_config table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'company_config'
            )
        """)

        if not cursor.fetchone()[0]:
            print("\n[ERROR] company_config table does not exist!")
            print("  Run init_railway_db.py first to create tables")
            sys.exit(1)

        print("[OK] company_config table found")

        # Check if default_employee_count column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'company_config'
            AND column_name = 'default_employee_count'
        """)

        if cursor.fetchone() is not None:
            print("\n[SKIP] Column 'default_employee_count' already exists!")
            print("  No migration needed - database is up to date")

            # Show current schema
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'company_config'
                ORDER BY ordinal_position
            """)

            print("\n  Current company_config schema:")
            for row in cursor.fetchall():
                print(f"    - {row[0]} ({row[1]}) DEFAULT {row[2]}")

            conn.close()
            return

        # Add the column
        print("\n[MIGRATION] Adding default_employee_count column...")
        cursor.execute("""
            ALTER TABLE company_config
            ADD COLUMN default_employee_count INTEGER DEFAULT 5
        """)

        conn.commit()
        print("[OK] Column added successfully!")

        # Verify the addition
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'company_config'
            ORDER BY ordinal_position
        """)

        print("\n  Updated company_config schema:")
        for row in cursor.fetchall():
            print(f"    - {row[0]} ({row[1]}) DEFAULT {row[2]}")

        # Check data
        cursor.execute("SELECT COUNT(*) FROM company_config")
        company_count = cursor.fetchone()[0]

        if company_count > 0:
            print(f"\n[INFO] Found {company_count} companies in database")
            print("  All existing companies now have default_employee_count = 5")

            # Show sample
            cursor.execute("""
                SELECT company, employee_count, default_employee_count
                FROM company_config
                LIMIT 5
            """)
            print("\n  Sample companies:")
            for row in cursor.fetchall():
                print(f"    - {row[0]}: employees={row[1]}, default={row[2]}")

        conn.close()

        print("\n" + "="*60)
        print("[SUCCESS] Migration completed successfully!")
        print("="*60)
        print("\nYour Railway database now supports default employee counts.")
        print("Redeploy your application for changes to take effect.")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
