"""
Import the generated SQL files to PostgreSQL
Handles connection with retry and better error handling
"""

import os
import psycopg2
from psycopg2 import sql
import time
from dotenv import load_dotenv

def execute_sql_file(connection, filename):
    """Execute SQL statements from a file"""
    cursor = connection.cursor()

    print(f"\nExecuting {filename}...")

    with open(filename, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split by semicolons but keep them
    statements = [s.strip() + ';' for s in sql_content.split(';') if s.strip()]

    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        if statement.strip() and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                success_count += 1
                if 'INSERT INTO' in statement:
                    # Extract name from INSERT statement for feedback
                    if 'tracked_employees' in statement:
                        print(".", end="", flush=True)
                        if success_count % 10 == 0:
                            print(f" [{success_count} employees]")
            except psycopg2.Error as e:
                error_count += 1
                print(f"\nError on statement {i}: {str(e)[:100]}")
                connection.rollback()
                continue

    connection.commit()
    print(f"\n✓ Executed {success_count} statements successfully")
    if error_count > 0:
        print(f"  ({error_count} statements had errors)")

    return success_count, error_count

def test_connection(database_url):
    """Test PostgreSQL connection"""
    try:
        print("Testing PostgreSQL connection...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[0][:50]}...")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def import_data():
    """Main import function"""
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL not found in .env")
        return

    print("="*60)
    print("IMPORTING DATA TO POSTGRESQL")
    print("="*60)

    # Test connection first
    if not test_connection(database_url):
        print("\nTrying alternative connection method...")
        # Try with SSL disabled
        database_url_no_ssl = database_url + "?sslmode=disable"
        if not test_connection(database_url_no_ssl):
            print("Failed to connect to PostgreSQL")
            return
        database_url = database_url_no_ssl

    try:
        # Connect and import
        conn = psycopg2.connect(database_url)

        # Import employees
        if os.path.exists('employee_inserts.sql'):
            execute_sql_file(conn, 'employee_inserts.sql')
        else:
            print("employee_inserts.sql not found!")

        # Import company configs
        if os.path.exists('company_config_inserts.sql'):
            execute_sql_file(conn, 'company_config_inserts.sql')
        else:
            print("company_config_inserts.sql not found!")

        # Verify import
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        emp_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM company_config")
        config_count = cursor.fetchone()[0]

        print("\n" + "="*60)
        print("IMPORT COMPLETE")
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

        print("\nSample imported employees:")
        for s in samples:
            print(f"  - {s[0]} | {s[1]} | {s[2][:40] if s[2] else 'N/A'}")

        conn.close()
        print("\n✅ Import completed successfully!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_data()