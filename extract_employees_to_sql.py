"""
Extract employees from SQLite and generate PostgreSQL INSERT statements
Simple copy approach - generates SQL that can be run directly
"""

import sqlite3
import json
from datetime import datetime

def escape_string(s):
    """Escape single quotes for SQL"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def format_json(data):
    """Format JSON data for PostgreSQL"""
    if data is None:
        return 'NULL'
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return 'NULL'
    return "'" + json.dumps(data).replace("'", "''") + "'::jsonb"

def extract_employees():
    """Extract all employees from SQLite and generate SQL"""
    conn = sqlite3.connect('data/tracking.db')
    cursor = conn.cursor()

    # Get all employees
    cursor.execute("""
        SELECT pdl_id, name, company, title, linkedin_url,
               tracking_started, last_checked, status, current_company,
               job_last_changed, full_data, added_date
        FROM tracked_employees
    """)

    employees = cursor.fetchall()
    print(f"Found {len(employees)} employees to copy\n")

    # Generate SQL file
    with open('employee_inserts.sql', 'w', encoding='utf-8') as f:
        # Create table if not exists
        f.write("""-- Create tracked_employees table if it doesn't exist
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
);

-- Clear existing data (optional - comment out if you want to keep existing)
-- TRUNCATE TABLE tracked_employees;

-- Insert employees
""")

        for emp in employees:
            pdl_id = escape_string(emp[0])
            name = escape_string(emp[1])
            company = escape_string(emp[2])
            title = escape_string(emp[3])
            linkedin_url = escape_string(emp[4])
            tracking_started = escape_string(emp[5])
            last_checked = escape_string(emp[6])
            status = escape_string(emp[7])
            current_company = escape_string(emp[8])
            job_last_changed = escape_string(emp[9])
            full_data = format_json(emp[10])
            added_date = escape_string(emp[11])

            insert_sql = f"""
INSERT INTO tracked_employees
(pdl_id, name, company, title, linkedin_url, tracking_started,
 last_checked, status, current_company, job_last_changed, full_data, added_date)
VALUES (
    {pdl_id}, {name}, {company}, {title}, {linkedin_url},
    {tracking_started}, {last_checked}, {status}, {current_company},
    {job_last_changed}, {full_data}, {added_date}
) ON CONFLICT (pdl_id) DO UPDATE SET
    name = EXCLUDED.name,
    title = EXCLUDED.title,
    last_checked = EXCLUDED.last_checked,
    status = EXCLUDED.status,
    current_company = EXCLUDED.current_company,
    job_last_changed = EXCLUDED.job_last_changed,
    full_data = EXCLUDED.full_data;
"""
            f.write(insert_sql)
            try:
                print(f"  Prepared: {emp[1]} ({emp[2]})")
            except UnicodeEncodeError:
                print(f"  Prepared: {emp[1].encode('ascii', 'ignore').decode('ascii')} ({emp[2]})")

    # Also extract company configs
    cursor.execute("SELECT company, employee_count, last_updated FROM company_config")
    configs = cursor.fetchall()

    with open('company_config_inserts.sql', 'w', encoding='utf-8') as f:
        f.write("""-- Create company_config table if it doesn't exist
CREATE TABLE IF NOT EXISTS company_config (
    company TEXT PRIMARY KEY,
    employee_count INTEGER DEFAULT 5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert company configurations
""")

        for config in configs:
            company = escape_string(config[0])
            employee_count = config[1] if config[1] is not None else 5
            last_updated = escape_string(config[2])

            insert_sql = f"""
INSERT INTO company_config (company, employee_count, last_updated)
VALUES ({company}, {employee_count}, {last_updated})
ON CONFLICT (company) DO UPDATE SET
    employee_count = EXCLUDED.employee_count,
    last_updated = EXCLUDED.last_updated;
"""
            f.write(insert_sql)

    conn.close()

    print(f"\n[SUCCESS] Generated SQL files:")
    print(f"  - employee_inserts.sql ({len(employees)} employees)")
    print(f"  - company_config_inserts.sql ({len(configs)} companies)")
    print(f"\nTo import to PostgreSQL, run:")
    print(f"  psql DATABASE_URL < employee_inserts.sql")
    print(f"  psql DATABASE_URL < company_config_inserts.sql")

    # Also create a simple text list for manual reference
    with open('employee_list.txt', 'w', encoding='utf-8') as f:
        f.write("TRACKED EMPLOYEES LIST\n")
        f.write("=" * 80 + "\n\n")
        for emp in employees:
            f.write(f"Name: {emp[1]}\n")
            f.write(f"Company: {emp[2]}\n")
            f.write(f"Title: {emp[3] or 'N/A'}\n")
            f.write(f"LinkedIn: {emp[4] or 'N/A'}\n")
            f.write(f"PDL ID: {emp[0]}\n")
            f.write("-" * 40 + "\n")

    print(f"  - employee_list.txt (human-readable list)")

if __name__ == "__main__":
    extract_employees()