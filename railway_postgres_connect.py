"""
Connect to Railway PostgreSQL from local machine using Railway CLI proxy
This script helps you connect and import data to your Railway PostgreSQL
"""

import os
import subprocess
import psycopg2
from psycopg2.extras import Json
import json
import time
from dotenv import load_dotenv

def setup_railway_proxy():
    """
    Set up Railway CLI proxy to connect to PostgreSQL
    Returns the local proxy connection string
    """
    print("="*60)
    print("RAILWAY POSTGRESQL CONNECTION SETUP")
    print("="*60)

    print("\n1. First, install Railway CLI if not already installed:")
    print("   npm install -g @railway/cli")

    print("\n2. Login to Railway:")
    print("   railway login")

    print("\n3. Link to your project:")
    print("   railway link")

    print("\n4. Start the PostgreSQL proxy:")
    print("   railway connect postgres")
    print("   (This will give you a local connection string)")

    print("\n5. The proxy will provide a connection like:")
    print("   postgresql://postgres:password@localhost:RANDOM_PORT/railway")

    # Get the proxied connection string from user
    proxy_url = input("\nPaste the proxied DATABASE_URL here: ").strip()

    return proxy_url

def import_data_to_railway(connection_string):
    """Import the SQLite data to Railway PostgreSQL"""

    try:
        print("\nConnecting to Railway PostgreSQL via proxy...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ Connected to PostgreSQL: {version[0][:50]}...")

        # Create tables
        print("\nCreating tables if not exist...")

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_config (
                company TEXT PRIMARY KEY,
                employee_count INTEGER DEFAULT 5,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        conn.commit()
        print("✓ Tables created/verified")

        # Import from SQL files if they exist
        if os.path.exists('employee_inserts.sql'):
            print("\nImporting employees from employee_inserts.sql...")
            with open('employee_inserts.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Execute statements
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

            imported = 0
            for stmt in statements:
                if 'INSERT INTO' in stmt:
                    try:
                        cursor.execute(stmt + ';')
                        imported += 1
                        if imported % 10 == 0:
                            print(f"  Imported {imported} employees...")
                    except Exception as e:
                        if 'duplicate key' not in str(e).lower():
                            print(f"  Warning: {str(e)[:100]}")
                        conn.rollback()
                        continue

            conn.commit()
            print(f"✓ Imported {imported} employees")

        if os.path.exists('company_config_inserts.sql'):
            print("\nImporting company configs...")
            with open('company_config_inserts.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()

            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

            for stmt in statements:
                if 'INSERT INTO' in stmt:
                    try:
                        cursor.execute(stmt + ';')
                    except Exception as e:
                        if 'duplicate key' not in str(e).lower():
                            print(f"  Warning: {str(e)[:100]}")
                        conn.rollback()
                        continue

            conn.commit()
            print("✓ Company configs imported")

        # Verify import
        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        emp_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM company_config")
        config_count = cursor.fetchone()[0]

        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"✓ Employees in PostgreSQL: {emp_count}")
        print(f"✓ Company configs: {config_count}")

        # Show sample
        cursor.execute("""
            SELECT name, company, title
            FROM tracked_employees
            LIMIT 5
        """)
        samples = cursor.fetchall()

        if samples:
            print("\nSample imported employees:")
            for s in samples:
                print(f"  - {s[0]} | {s[1]} | {(s[2][:40] if s[2] else 'N/A')}")

        conn.close()
        print("\n✅ Import completed successfully!")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False

def get_railway_database_url():
    """Get DATABASE_URL from Railway service"""
    print("\n" + "="*60)
    print("HOW TO GET YOUR RAILWAY DATABASE_URL")
    print("="*60)

    print("\n1. Go to your Railway Dashboard")
    print("2. Click on your PostgreSQL service")
    print("3. Go to the 'Variables' tab")
    print("4. Copy the DATABASE_URL value")
    print("\n5. OR use Railway CLI:")
    print("   railway variables")
    print("   (This will show all variables including DATABASE_URL)")

    print("\n" + "="*60)
    print("OPTION A: Direct Connection (Usually Won't Work from Local)")
    print("="*60)
    print("This typically fails due to network restrictions")

    database_url = input("\nPaste your DATABASE_URL (or press Enter to skip): ").strip()

    if database_url:
        # Try direct connection
        try:
            print("\nTrying direct connection...")
            conn = psycopg2.connect(database_url)
            print("✓ Direct connection successful!")
            conn.close()
            return database_url
        except Exception as e:
            print(f"✗ Direct connection failed: {str(e)[:100]}")
            print("\nDirect connection failed (expected). Use Railway CLI proxy instead.")

    print("\n" + "="*60)
    print("OPTION B: Railway CLI Proxy (Recommended)")
    print("="*60)

    return setup_railway_proxy()

def main():
    """Main function"""

    print("RAILWAY POSTGRESQL DATA IMPORT TOOL")
    print("="*60)

    print("\nThis tool will help you:")
    print("1. Connect to your Railway PostgreSQL")
    print("2. Import the 36 tracked employees")
    print("3. Set up company configurations")

    # Check for SQL files
    if not os.path.exists('employee_inserts.sql'):
        print("\n⚠ employee_inserts.sql not found!")
        print("Run 'python extract_employees_to_sql.py' first to generate SQL files")
        return

    # Get connection method
    print("\nChoose connection method:")
    print("1. Use Railway CLI proxy (recommended for local development)")
    print("2. Try direct connection (usually fails from local)")
    print("3. Get connection instructions only")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        proxy_url = setup_railway_proxy()
        if proxy_url:
            import_data_to_railway(proxy_url)
    elif choice == "2":
        database_url = get_railway_database_url()
        if database_url:
            import_data_to_railway(database_url)
    else:
        print("\n" + "="*60)
        print("MANUAL IMPORT INSTRUCTIONS")
        print("="*60)
        print("\n1. Go to Railway Dashboard → PostgreSQL service")
        print("2. Click on 'Query' tab")
        print("3. Copy content from 'employee_inserts.sql'")
        print("4. Paste and run in Query interface")
        print("5. Repeat for 'company_config_inserts.sql'")
        print("\nThis is the easiest method if you don't need local access!")

if __name__ == "__main__":
    main()