#!/usr/bin/env python3
"""
Initialize and debug PostgreSQL database on Railway
Run this script on Railway to ensure database is properly set up
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from datetime import datetime

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

def test_connection(db_config):
    """Test database connection"""
    try:
        print(f"Testing connection to {db_config['host']}:{db_config['port']}/{db_config['database']}...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"   PostgreSQL version: {version}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_tables(db_config):
    """Check existing tables in database"""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} rows")

        conn.close()
        return len(tables) > 0
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def create_tables(db_config):
    """Create all required tables"""
    try:
        print("\n🔨 Creating database tables...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Main tracking table
        print("   Creating tracked_employees table...")
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

        # Create index for company queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tracked_employees_company
            ON tracked_employees(company)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tracked_employees_status
            ON tracked_employees(status)
        """)

        # Scheduler state table
        print("   Creating scheduler_state table...")
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

        # Initialize scheduler state
        cursor.execute("""
            INSERT INTO scheduler_state (id, scheduler_enabled)
            VALUES (1, false)
            ON CONFLICT (id) DO NOTHING
        """)

        # Departure history table
        print("   Creating departures table...")
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
                job_company_size TEXT,
                FOREIGN KEY (pdl_id) REFERENCES tracked_employees(pdl_id)
            )
        """)

        # Company tracking configuration
        print("   Creating company_config table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_config (
                company TEXT PRIMARY KEY,
                employee_count INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Fetch history for audit trail
        print("   Creating fetch_history table...")
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

        conn.commit()
        print("✅ All tables created successfully!")

        # Verify tables were created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        created_tables = [t[0] for t in cursor.fetchall()]
        print(f"   Verified tables: {', '.join(created_tables)}")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_test_data(db_config):
    """Insert test data to verify everything works"""
    try:
        print("\n🧪 Inserting test data...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Check if test data already exists
        cursor.execute("SELECT COUNT(*) FROM tracked_employees WHERE pdl_id = 'test_001'")
        if cursor.fetchone()[0] > 0:
            print("   Test data already exists, skipping...")
            conn.close()
            return True

        # Insert test employee
        cursor.execute("""
            INSERT INTO tracked_employees
            (pdl_id, name, company, title, linkedin_url, tracking_started, last_checked, status)
            VALUES
            ('test_001', 'Test User', 'Railway Test Company', 'Test Engineer',
             'https://linkedin.com/in/test', %s, %s, 'active')
        """, (datetime.now(), datetime.now()))

        # Insert test company config
        cursor.execute("""
            INSERT INTO company_config (company, employee_count)
            VALUES ('Railway Test Company', 1)
            ON CONFLICT (company) DO UPDATE SET employee_count = 1
        """)

        conn.commit()
        print("✅ Test data inserted successfully!")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        count = cursor.fetchone()[0]
        print(f"   Total employees in database: {count}")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error inserting test data: {e}")
        return False

def main():
    """Main initialization function"""
    print("=" * 60)
    print("RAILWAY POSTGRESQL DATABASE INITIALIZATION")
    print("=" * 60)

    # Get DATABASE_URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("\n❌ DATABASE_URL environment variable not found!")
        print("   This script should be run on Railway.")
        print("\n   For local testing, set DATABASE_URL to your PostgreSQL connection string.")
        sys.exit(1)

    print(f"\n📌 DATABASE_URL found: {database_url[:30]}...")

    # Parse connection details
    db_config = parse_database_url(database_url)
    print(f"\n🔗 Connection details:")
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")

    # Test connection
    if not test_connection(db_config):
        sys.exit(1)

    # Check existing tables
    has_tables = check_tables(db_config)

    if not has_tables:
        print("\n⚠️  No tables found in database!")
        # Create tables
        if not create_tables(db_config):
            sys.exit(1)

        # Insert test data
        insert_test_data(db_config)
    else:
        print("\n✅ Database already has tables configured")

    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION COMPLETE")
    print("=" * 60)
    print("\nYour Railway PostgreSQL database is ready!")
    print("The application should now work correctly.")

    # Final check
    print("\n📊 Final database status:")
    check_tables(db_config)

if __name__ == "__main__":
    main()