"""
SQLite database for persistent employee tracking
Ensures data is never lost and properly appended
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class TrackingDatabase:
    """SQLite database for employee tracking with proper history"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'tracking.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main tracking table
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
                full_data JSON,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Scheduler state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_state (
                id INTEGER PRIMARY KEY DEFAULT 1,
                last_check_date TIMESTAMP,
                next_check_date TIMESTAMP,
                scheduler_enabled BOOLEAN DEFAULT 0,
                check_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (id = 1)
            )
        """)
        
        # Initialize scheduler state if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO scheduler_state (id, scheduler_enabled)
            VALUES (1, 0)
        """)
        
        # Departure history table (enhanced with alert levels)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdl_id TEXT,
                name TEXT,
                old_company TEXT,
                old_title TEXT,
                new_company TEXT,
                new_title TEXT,
                departure_date TEXT,
                detected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_level INTEGER DEFAULT 1,
                alert_signals JSON,
                headline TEXT,
                summary TEXT,
                job_summary TEXT,
                job_company_type TEXT,
                job_company_size TEXT,
                FOREIGN KEY (pdl_id) REFERENCES tracked_employees(pdl_id)
            )
        """)
        
        # Company tracking configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_config (
                company TEXT PRIMARY KEY,
                employee_count INTEGER,
                default_employee_count INTEGER DEFAULT 5,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fetch history for audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                employees_fetched INTEGER,
                credits_used INTEGER,
                fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_employees(self, employees: List[Dict], company: str) -> int:
        """Add employees to tracking (APPEND, not overwrite)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        added_count = 0
        updated_count = 0
        
        for emp in employees:
            pdl_id = emp.get('id') or emp.get('pdl_id')
            if not pdl_id:
                continue
            
            # Check if employee already exists
            cursor.execute("SELECT pdl_id FROM tracked_employees WHERE pdl_id = ?", (pdl_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing employee
                cursor.execute("""
                    UPDATE tracked_employees 
                    SET last_checked = ?, full_data = ?
                    WHERE pdl_id = ?
                """, (datetime.now(), json.dumps(emp), pdl_id))
                updated_count += 1
            else:
                # Add new employee
                # Fix LinkedIn URL to include https://
                linkedin_url = emp.get('linkedin_url', '')
                if linkedin_url and not linkedin_url.startswith('http'):
                    if linkedin_url.startswith('linkedin.com/in/'):
                        linkedin_url = f'https://www.{linkedin_url}'
                    elif linkedin_url.startswith('www.linkedin.com/in/'):
                        linkedin_url = f'https://{linkedin_url}'
                    elif '/in/' in linkedin_url:
                        linkedin_url = f'https://www.linkedin.com{linkedin_url if linkedin_url.startswith("/") else "/" + linkedin_url}'
                    else:
                        # Just a username/profile ID
                        linkedin_url = f'https://www.linkedin.com/in/{linkedin_url}'
                
                cursor.execute("""
                    INSERT INTO tracked_employees 
                    (pdl_id, name, company, title, linkedin_url, tracking_started, 
                     last_checked, status, current_company, job_last_changed, full_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pdl_id,
                    emp.get('full_name', 'Unknown'),
                    company,
                    emp.get('job_title', 'Unknown'),
                    linkedin_url,
                    datetime.now(),
                    datetime.now(),
                    'active',
                    emp.get('job_company_name'),
                    emp.get('job_last_changed'),
                    json.dumps(emp)
                ))
                added_count += 1
        
        # Update company config - preserve default_employee_count
        cursor.execute("""
            INSERT INTO company_config (company, employee_count, default_employee_count, last_updated)
            VALUES (?, ?, 5, ?)
            ON CONFLICT(company) DO UPDATE SET
                employee_count = COALESCE(employee_count, 0) + ?,
                last_updated = ?
        """, (company, added_count, datetime.now(), added_count, datetime.now()))
        
        # Add to fetch history
        cursor.execute("""
            INSERT INTO fetch_history (company, employees_fetched, credits_used, success)
            VALUES (?, ?, ?, ?)
        """, (company, added_count, len(employees), True))
        
        conn.commit()
        conn.close()
        
        return added_count, updated_count
    
    def get_all_employees(self, status: Optional[str] = None) -> List[Dict]:
        """Get all tracked employees"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT pdl_id, name, company, title, status, current_company, 
                       tracking_started, last_checked, linkedin_url, full_data
                FROM tracked_employees 
                WHERE status = ?
                ORDER BY company, name
            """, (status,))
        else:
            cursor.execute("""
                SELECT pdl_id, name, company, title, status, current_company, 
                       tracking_started, last_checked, linkedin_url, full_data
                FROM tracked_employees 
                ORDER BY company, name
            """)
        
        columns = ['pdl_id', 'name', 'company', 'title', 'status', 'current_company',
                   'tracking_started', 'last_checked', 'linkedin_url', 'full_data']
        
        employees = []
        for row in cursor.fetchall():
            emp = dict(zip(columns, row))
            # Parse full_data JSON if present
            if emp.get('full_data'):
                try:
                    emp['full_data'] = json.loads(emp['full_data'])
                except:
                    emp['full_data'] = {}
            # Fix LinkedIn URL if needed
            if emp.get('linkedin_url'):
                url = emp['linkedin_url']
                if not url.startswith('http'):
                    if url.startswith('linkedin.com'):
                        emp['linkedin_url'] = f'https://www.{url}'
                    elif url.startswith('www.linkedin.com'):
                        emp['linkedin_url'] = f'https://{url}'
                    else:
                        emp['linkedin_url'] = f'https://www.linkedin.com/in/{url}'
            employees.append(emp)
        
        conn.close()
        return employees
    
    def get_employee_by_id(self, pdl_id: str) -> Optional[Dict]:
        """Get specific employee by PDL ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pdl_id, name, company, title, status, current_company, 
                   full_data, last_checked
            FROM tracked_employees 
            WHERE pdl_id = ?
        """, (pdl_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'pdl_id': row[0],
                'name': row[1],
                'company': row[2],
                'title': row[3],
                'status': row[4],
                'current_company': row[5],
                'full_data': json.loads(row[6]) if row[6] else {},
                'last_checked': row[7]
            }
        return None
    
    def update_employee_status(self, pdl_id: str, new_status: str, new_company: Optional[str] = None):
        """Update employee status (e.g., when they leave)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if new_company:
            cursor.execute("""
                UPDATE tracked_employees 
                SET status = ?, current_company = ?, last_checked = ?
                WHERE pdl_id = ?
            """, (new_status, new_company, datetime.now(), pdl_id))
        else:
            cursor.execute("""
                UPDATE tracked_employees 
                SET status = ?, last_checked = ?
                WHERE pdl_id = ?
            """, (new_status, datetime.now(), pdl_id))
        
        conn.commit()
        conn.close()
    
    def soft_delete_employee(self, pdl_id: str) -> bool:
        """Soft delete employee (mark as deleted but keep in database)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tracked_employees 
            SET status = 'deleted', last_checked = ?
            WHERE pdl_id = ? AND status != 'deleted'
        """, (datetime.now(), pdl_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def restore_employee(self, pdl_id: str) -> bool:
        """Restore a soft-deleted employee back to active tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tracked_employees 
            SET status = 'active', last_checked = ?
            WHERE pdl_id = ? AND status = 'deleted'
        """, (datetime.now(), pdl_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_deleted_employees(self) -> List[Dict]:
        """Get all soft-deleted employees for backup/restore"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pdl_id, name, company, title, status, current_company, 
                   tracking_started, last_checked, linkedin_url
            FROM tracked_employees 
            WHERE status = 'deleted'
            ORDER BY last_checked DESC
        """)
        
        columns = ['pdl_id', 'name', 'company', 'title', 'status', 'current_company',
                   'tracking_started', 'last_checked', 'linkedin_url', 'full_data']
        
        employees = []
        for row in cursor.fetchall():
            emp = dict(zip(columns, row))
            # Parse full_data JSON if present
            if emp.get('full_data'):
                try:
                    emp['full_data'] = json.loads(emp['full_data'])
                except:
                    emp['full_data'] = {}
            # Fix LinkedIn URL if needed
            if emp.get('linkedin_url'):
                url = emp['linkedin_url']
                if not url.startswith('http'):
                    if url.startswith('linkedin.com'):
                        emp['linkedin_url'] = f'https://www.{url}'
                    elif url.startswith('www.linkedin.com'):
                        emp['linkedin_url'] = f'https://{url}'
                    else:
                        emp['linkedin_url'] = f'https://www.linkedin.com/in/{url}'
            employees.append(emp)
        
        conn.close()
        return employees
    
    def add_departure(self, departure: Dict):
        """Record a departure with alert level"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO departures 
            (pdl_id, name, old_company, old_title, new_company, new_title, 
             departure_date, alert_level, alert_signals, headline, summary, 
             job_summary, job_company_type, job_company_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            departure.get('pdl_id'),
            departure.get('name'),
            departure.get('old_company'),
            departure.get('old_title'),
            departure.get('new_company'),
            departure.get('new_title'),
            departure.get('departure_date') or departure.get('job_last_changed'),
            departure.get('alert_level', 1),
            json.dumps(departure.get('alert_signals', [])),
            departure.get('headline'),
            departure.get('summary'),
            departure.get('job_summary'),
            departure.get('job_company_type'),
            departure.get('job_company_size')
        ))
        
        conn.commit()
        conn.close()
    
    def get_departures(self, limit: int = 100) -> List[Dict]:
        """Get departure history with alert levels"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pdl_id, name, old_company, old_title, new_company, 
                   new_title, departure_date, detected_date, alert_level,
                   alert_signals, headline, summary, job_company_type
            FROM departures 
            ORDER BY alert_level DESC, detected_date DESC
            LIMIT ?
        """, (limit,))
        
        columns = ['pdl_id', 'name', 'old_company', 'old_title', 'new_company',
                   'new_title', 'departure_date', 'detected_date', 'alert_level',
                   'alert_signals', 'headline', 'summary', 'job_company_type']
        
        departures = []
        for row in cursor.fetchall():
            dep = dict(zip(columns, row))
            # Parse JSON alert_signals
            if dep.get('alert_signals'):
                try:
                    dep['alert_signals'] = json.loads(dep['alert_signals'])
                except:
                    dep['alert_signals'] = []
            departures.append(dep)
        
        conn.close()
        return departures
    
    def get_statistics(self) -> Dict:
        """Get tracking statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total employees
        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        total = cursor.fetchone()[0]
        
        # Active employees
        cursor.execute("SELECT COUNT(*) FROM tracked_employees WHERE status = 'active'")
        active = cursor.fetchone()[0]
        
        # Departed employees
        cursor.execute("SELECT COUNT(*) FROM tracked_employees WHERE status = 'departed'")
        departed = cursor.fetchone()[0]
        
        # Deleted employees
        cursor.execute("SELECT COUNT(*) FROM tracked_employees WHERE status = 'deleted'")
        deleted = cursor.fetchone()[0]
        
        # By company
        cursor.execute("""
            SELECT company, COUNT(*) as count 
            FROM tracked_employees 
            WHERE status = 'active'
            GROUP BY company
        """)
        by_company = dict(cursor.fetchall())
        
        # Fetch history
        cursor.execute("""
            SELECT SUM(credits_used) as total_credits,
                   COUNT(DISTINCT company) as companies_tracked,
                   MAX(fetch_date) as last_fetch
            FROM fetch_history
            WHERE success = 1
        """)
        history = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_tracked': total,
            'active': active,
            'departed': departed,
            'deleted': deleted,
            'companies': by_company,
            'total_credits_used': history[0] or 0,
            'companies_tracked': history[1] or 0,
            'last_fetch': history[2]
        }
    
    def get_fetch_history(self, limit: int = 50) -> List[Dict]:
        """Get history of all fetches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT company, employees_fetched, credits_used, fetch_date, success
            FROM fetch_history
            ORDER BY fetch_date DESC
            LIMIT ?
        """, (limit,))
        
        columns = ['company', 'employees_fetched', 'credits_used', 'fetch_date', 'success']
        
        history = []
        for row in cursor.fetchall():
            history.append(dict(zip(columns, row)))
        
        conn.close()
        return history

    def get_all_companies(self) -> List[Dict]:
        """Get all companies from company_config table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company, employee_count, last_updated
            FROM company_config
            ORDER BY company
        """)

        companies = []
        for row in cursor.fetchall():
            companies.append({
                'company': row[0],
                'employee_count': row[1],
                'last_updated': row[2]
            })

        conn.close()
        return companies

    def delete_company(self, company_name: str) -> bool:
        """Delete a company and all its tracked employees"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Delete all employees from this company
            cursor.execute("""
                DELETE FROM tracked_employees
                WHERE company = ?
            """, (company_name,))

            employees_deleted = cursor.rowcount

            # Delete company from company_config
            cursor.execute("""
                DELETE FROM company_config
                WHERE company = ?
            """, (company_name,))

            # Delete from fetch_history
            cursor.execute("""
                DELETE FROM fetch_history
                WHERE company = ?
            """, (company_name,))

            # Delete from departures
            cursor.execute("""
                DELETE FROM departures
                WHERE old_company = ? OR new_company = ?
            """, (company_name, company_name))

            conn.commit()
            conn.close()

            print(f"[DATABASE] Deleted company '{company_name}' and {employees_deleted} employees")
            return True

        except Exception as e:
            print(f"[DATABASE] Error deleting company: {e}")
            conn.rollback()
            conn.close()
            return False

    def get_company_employee_counts(self) -> dict:
        """Get count of tracked employees for each company"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company, COUNT(*) as employee_count
            FROM tracked_employees
            WHERE status != 'deleted'
            GROUP BY company
            ORDER BY company
        """)

        counts = {}
        for row in cursor.fetchall():
            counts[row[0]] = row[1]

        conn.close()
        return counts

    def set_company_default_count(self, company: str, default_count: int) -> bool:
        """Set the default employee count for a company"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO company_config (company, default_employee_count, employee_count, last_updated)
                VALUES (?, ?, 0, ?)
                ON CONFLICT(company) DO UPDATE SET
                    default_employee_count = ?,
                    last_updated = ?
            """, (company, default_count, datetime.now(), default_count, datetime.now()))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DATABASE] Error setting default count: {e}")
            conn.close()
            return False

    def get_company_default_count(self, company: str) -> Optional[int]:
        """Get the default employee count for a company"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT default_employee_count
            FROM company_config
            WHERE company = ?
        """, (company,))

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None

    def get_all_company_defaults(self) -> Dict[str, int]:
        """Get all companies with their default counts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company, default_employee_count
            FROM company_config
            WHERE default_employee_count IS NOT NULL
        """)

        defaults = {}
        for row in cursor.fetchall():
            defaults[row[0]] = row[1]

        conn.close()
        return defaults

    def fix_existing_linkedin_urls(self):
        """One-time fix for existing LinkedIn URLs in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all employees with LinkedIn URLs
        cursor.execute("""
            SELECT pdl_id, linkedin_url
            FROM tracked_employees
            WHERE linkedin_url IS NOT NULL AND linkedin_url != ''
        """)
        
        updates = []
        for pdl_id, url in cursor.fetchall():
            if url and not url.startswith('http'):
                if url.startswith('linkedin.com/in/'):
                    new_url = f'https://www.{url}'
                elif url.startswith('www.linkedin.com/in/'):
                    new_url = f'https://{url}'
                elif '/in/' in url:
                    # Already has /in/ path
                    new_url = f'https://www.linkedin.com{url if url.startswith("/") else "/" + url}'
                else:
                    # Just a username/profile ID
                    new_url = f'https://www.linkedin.com/in/{url}'
                updates.append((new_url, pdl_id))
        
        # Update all URLs
        for new_url, pdl_id in updates:
            cursor.execute("""
                UPDATE tracked_employees
                SET linkedin_url = ?
                WHERE pdl_id = ?
            """, (new_url, pdl_id))
        
        conn.commit()
        conn.close()
    
    def get_scheduler_state(self) -> Dict:
        """Get the current scheduler state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT last_check_date, next_check_date, scheduler_enabled, check_count
            FROM scheduler_state
            WHERE id = 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'last_check_date': row[0],
                'next_check_date': row[1],
                'scheduler_enabled': bool(row[2]),
                'check_count': row[3]
            }
        return {
            'last_check_date': None,
            'next_check_date': None,
            'scheduler_enabled': False,
            'check_count': 0
        }
    
    def update_scheduler_state(self, last_check: datetime = None, next_check: datetime = None, 
                              enabled: bool = None, increment_count: bool = False):
        """Update the scheduler state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if last_check is not None:
            updates.append("last_check_date = ?")
            params.append(last_check.isoformat())
        
        if next_check is not None:
            updates.append("next_check_date = ?")
            params.append(next_check.isoformat())
        
        if enabled is not None:
            updates.append("scheduler_enabled = ?")
            params.append(1 if enabled else 0)
        
        if increment_count:
            updates.append("check_count = check_count + 1")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        
        if updates:
            query = f"UPDATE scheduler_state SET {', '.join(updates)} WHERE id = 1"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        
        return len(updates)