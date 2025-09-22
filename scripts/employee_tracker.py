"""
Employee Tracking System
Tracks specific number of senior employees from each company
Checks monthly for departures and sends alerts
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.target_companies import (
    TARGET_COMPANIES, SENIOR_ROLES, SENIOR_LEVELS, AI_ML_KEYWORDS,
    TECHNICAL_ROLE_KEYWORDS, NON_TECHNICAL_KEYWORDS
)
from scripts.database_factory import TrackingDatabase
from scripts.departure_classifier import DepartureClassifier
from dotenv import load_dotenv

class EmployeeTracker:
    """Track specific employees and monitor for departures"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        if not self.api_key:
            raise ValueError("No API_KEY found in .env file")
        
        self.base_url = "https://api.peopledatalabs.com/v5/person/search"
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Initialize database
        self.db = TrackingDatabase()
        
        # Keep tracking dir for backwards compatibility
        self.tracking_dir = Path(__file__).parent.parent / 'data' / 'tracking'
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
    
    def get_existing_employee_ids(self, company: str) -> set:
        """Get PDL IDs of employees already tracked from this company"""
        employees = self.db.get_all_employees()
        return {emp['pdl_id'] for emp in employees if emp['company'].lower() == company.lower()}
    
    def is_technical_role(self, job_title: str) -> bool:
        """Check if a job title is technical/product focused"""
        if not job_title:
            return False

        title_lower = job_title.lower()

        # Special cases: Some titles might contain excluded words but are still technical
        # If it has "engineer" in the title, it's likely technical even with GTM/sales words
        if 'engineer' in title_lower or 'engineering' in title_lower:
            # Only exclude if it's purely sales/marketing engineer
            if 'sales engineer' in title_lower or 'solutions engineer' in title_lower:
                return False
            return True

        # First check if it's explicitly non-technical
        for keyword in NON_TECHNICAL_KEYWORDS:
            if keyword in title_lower:
                # Additional special cases
                if 'product designer' in title_lower or 'ux engineer' in title_lower:
                    continue
                return False

        # Then check if it's technical
        for keyword in TECHNICAL_ROLE_KEYWORDS:
            if keyword in title_lower:
                return True

        # If no match, default to False (exclude uncertain roles)
        return False
    
    def fetch_senior_employees(self, company: str, count: int = 5, exclude_existing: bool = True) -> List[Dict]:
        """
        Fetch top N senior employees from a company to track
        
        Args:
            company: Company name
            count: Number of employees to fetch (credits to use)
        
        Returns:
            List of senior employees
        """
        print(f"\n[FETCHING] {count} senior employees from {company}")
        
        # Check existing employees if needed
        existing_ids = set()
        if exclude_existing:
            existing_ids = self.get_existing_employee_ids(company)
            if existing_ids:
                print(f"  Found {len(existing_ids)} already tracked from {company}")
                print(f"  Will exclude these IDs from search to save credits")
        
        # Progressive query strategy - try technical filters first, fallback if needed
        approach_used = None
        
        # Approach 1: Use job_title_role filter but exclude partnerships/marketing
        sql_query_approach1 = f"""
        SELECT * FROM person
        WHERE job_company_name = '{company.lower()}'
        AND job_title_levels IN ('vp', 'director', 'principal', 'staff', 'senior', 'lead')
        AND job_title_role IN ('engineering', 'research', 'data')"""
        
        # Add exclusion for existing PDL IDs
        if existing_ids:
            id_list = "', '".join(existing_ids)
            sql_query_approach1 += f"\n        AND id NOT IN ('{id_list}')"
        
        params = {
            'sql': sql_query_approach1.strip(),
            'size': count
        }
        
        try:
            # Try Approach 1 first
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=params,
                timeout=30
            )
            
            if response.status_code == 200:
                approach_used = 1
            elif response.status_code in [400, 504]:
                # Approach 1 failed, try Approach 2
                print(f"  Approach 1 failed with {response.status_code}, trying simpler query...")
                
                sql_query_approach2 = f"""
                SELECT * FROM person
                WHERE job_company_name = '{company.lower()}'
                AND job_title_levels IN ('vp', 'director', 'principal', 'staff', 'senior', 'lead')
                AND job_title LIKE '%engineer%'"""
                
                if existing_ids:
                    id_list = "', '".join(existing_ids)
                    sql_query_approach2 += f"\n                AND id NOT IN ('{id_list}')"
                
                params = {
                    'sql': sql_query_approach2.strip(),
                    'size': count
                }
                
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    approach_used = 2
                elif response.status_code in [400, 504]:
                    # Approach 2 failed, try Approach 3 (simple query)
                    print(f"  Approach 2 failed with {response.status_code}, using simple query...")
                    
                    sql_query_approach3 = f"""
                    SELECT * FROM person
                    WHERE job_company_name = '{company.lower()}'
                    AND job_title_levels IN ('vp', 'director', 'principal', 'staff', 'senior', 'lead')"""
                    
                    if existing_ids:
                        id_list = "', '".join(existing_ids)
                        sql_query_approach3 += f"\n                    AND id NOT IN ('{id_list}')"
                    
                    params = {
                        'sql': sql_query_approach3.strip(),
                        'size': count
                    }
                    
                    response = requests.post(
                        self.base_url,
                        headers=self.headers,
                        json=params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        approach_used = 3
            
            if response.status_code == 200:
                data = response.json()
                employees = data.get('data', [])
                
                # Log which approach succeeded
                approach_desc = {
                    1: "job_title_role filter (engineering/research/data)",
                    2: "job_title LIKE filter (engineer only)",
                    3: "basic senior filter (no role filtering)"
                }
                print(f"  Query approach {approach_used}: {approach_desc.get(approach_used, 'unknown')}")
                print(f"  Fetched: {len(employees)} employees")
                
                # Filter for technical roles
                technical_employees = []
                non_technical_skipped = []
                
                for emp in employees:
                    job_title = emp.get('job_title', '')
                    if self.is_technical_role(job_title):
                        # Add tracking metadata
                        emp['_tracking_started'] = datetime.now().isoformat()
                        emp['_company'] = company
                        emp['_last_checked'] = datetime.now().isoformat()
                        emp['_status'] = 'active'
                        technical_employees.append(emp)
                    else:
                        non_technical_skipped.append(f"{emp.get('full_name', 'Unknown')}: {job_title}")
                
                print(f"  Technical roles found: {len(technical_employees)}")
                if non_technical_skipped:
                    print(f"  Skipped {len(non_technical_skipped)} non-technical roles")
                    if len(non_technical_skipped) <= 3:
                        for skip in non_technical_skipped:
                            print(f"    - {skip}")
                
                print(f"  Credits used: {len(employees)}")
                
                # Show who we're tracking
                for i, emp in enumerate(technical_employees[:3], 1):
                    print(f"  {i}. {emp.get('full_name', 'Unknown')}: {emp.get('job_title', 'Unknown')}")
                
                return technical_employees
            else:
                print(f"  ERROR: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Message: {error_data.get('error', {}).get('message', 'Unknown')}")
                except:
                    print(f"  Response: {response.text[:200]}")
                return []
                
        except requests.exceptions.Timeout:
            print(f"  TIMEOUT: Request took too long")
            return []
        except requests.exceptions.ConnectionError:
            print(f"  CONNECTION ERROR: Could not connect to PDL API")
            return []
        except Exception as e:
            print(f"  EXCEPTION: {str(e)}")
            return []
    
    def initialize_tracking(self, company_configs: Dict[str, int]) -> Dict:
        """
        Initialize tracking for multiple companies (APPENDS to existing)
        
        Args:
            company_configs: Dict of {company_name: employee_count}
        
        Returns:
            Summary of tracking operation
        """
        print("\n" + "="*60)
        print("INITIALIZING EMPLOYEE TRACKING")
        print("="*60)
        
        total_credits = sum(company_configs.values())
        print(f"\nTotal credits to use: {total_credits}")
        
        total_added = 0
        total_updated = 0
        
        for company, count in company_configs.items():
            print(f"\nTracking {count} employees from {company}...")
            
            employees = self.fetch_senior_employees(company, count)
            
            if employees:
                # Add to database (this APPENDS, doesn't overwrite)
                added, updated = self.db.add_employees(employees, company)
                total_added += added
                total_updated += updated
                
                print(f"  Added {added} new employees, updated {updated} existing")
                
                # Show sample of who we're tracking
                for emp in employees[:3]:
                    print(f"    - {emp.get('full_name')}: {emp.get('job_title')}")
        
        # Get updated statistics
        stats = self.db.get_statistics()
        
        print(f"\n[COMPLETE]")
        print(f"  New employees added: {total_added}")
        print(f"  Existing updated: {total_updated}")
        print(f"  Total now tracking: {stats['total_tracked']}")
        
        return {
            'total_tracked': stats['total_tracked'],
            'new_added': total_added,
            'updated': total_updated,
            'companies': stats['companies']
        }
    
    def monthly_check(self) -> List[Dict]:
        """
        Check all tracked employees for departures
        Returns list of departures detected
        """
        print("\n" + "="*60)
        print("MONTHLY DEPARTURE CHECK")
        print("="*60)
        
        # Load current tracking data
        tracking_data = self.load_tracking_data()
        if not tracking_data:
            print("[ERROR] No tracking data found. Run initialization first.")
            return []
        
        print(f"Checking {tracking_data['total_tracked']} tracked employees...")
        
        departures = []
        checked = 0
        credits_used = 0
        
        # Check each tracked employee
        for pdl_id, employee_data in tracking_data['by_pdl_id'].items():
            if employee_data['status'] != 'active':
                continue  # Skip if already departed
            
            checked += 1
            print(f"\n[{checked}] Checking {employee_data['name']}...")
            
            # Query current status
            current_status = self.check_employee_status(pdl_id)
            credits_used += 1
            
            if current_status:
                old_company = employee_data['current_company'].lower()
                new_company = current_status.get('job_company_name', '').lower()
                
                if old_company != new_company:
                    # They left! Capture comprehensive data for alert classification
                    departure = {
                        'pdl_id': pdl_id,
                        'name': employee_data['name'],
                        'old_company': employee_data['company'],
                        'old_title': employee_data['title'],
                        'new_company': current_status.get('job_company_name', 'Unknown'),
                        'new_title': current_status.get('job_title', 'Unknown'),
                        'job_last_changed': current_status.get('job_last_changed'),
                        'detected_date': datetime.now().isoformat(),
                        'linkedin': employee_data.get('linkedin'),
                        # New fields for alert classification
                        'headline': current_status.get('headline', ''),
                        'summary': current_status.get('summary', ''),
                        'job_summary': current_status.get('job_summary', ''),
                        'job_company_type': current_status.get('job_company_type', ''),
                        'job_company_size': current_status.get('job_company_size', ''),
                        'job_company_founded': current_status.get('job_company_founded', ''),
                        'job_company_industry': current_status.get('job_company_industry', ''),
                        'alert_level': None,  # Will be set by classifier
                        'alert_signals': []  # Will be populated by classifier
                    }
                    
                    departures.append(departure)
                    
                    # Update tracking data
                    tracking_data['by_pdl_id'][pdl_id]['status'] = 'departed'
                    tracking_data['by_pdl_id'][pdl_id]['departure_date'] = datetime.now().isoformat()
                    tracking_data['by_pdl_id'][pdl_id]['new_company'] = departure['new_company']
                    
                    # IMPORTANT: Update database status to 'departed'
                    self.db.update_employee_status(pdl_id, 'departed', departure['new_company'])
                    
                    print(f"  ⚠️ DEPARTURE DETECTED!")
                    print(f"     {departure['name']} left {departure['old_company']}")
                    print(f"     Now at: {departure['new_company']}")
                else:
                    print(f"  ✓ Still at {employee_data['company']}")
                    tracking_data['by_pdl_id'][pdl_id]['last_checked'] = datetime.now().isoformat()
            else:
                print(f"  ⚠️ Could not check status")
        
        # Save updated tracking data
        self.save_tracking_data(tracking_data)
        
        # Classify departures by alert level
        if departures:
            print(f"\n[CLASSIFYING] Analyzing {len(departures)} departures...")
            classifier = DepartureClassifier()
            departures = classifier.classify_all_departures(departures)
            
            # Save departures to history (now with alert levels)
            self.save_departure_history(departures)
            
            # Send email alerts for Level 2 and Level 3 departures
            try:
                from send_departure_alerts import send_alerts_sync
                print(f"\n[EMAIL ALERTS] Processing alerts...")
                send_alerts_sync(departures)
            except Exception as e:
                print(f"[EMAIL ALERTS] Failed to send: {e}")
        
        print(f"\n[SUMMARY]")
        print(f"  Employees checked: {checked}")
        print(f"  Credits used: {credits_used}")
        print(f"  Departures detected: {len(departures)}")
        
        return departures
    
    def check_employee_status(self, pdl_id: str) -> Optional[Dict]:
        """Check current status of a specific employee"""
        
        query = f"SELECT * FROM person WHERE id = '{pdl_id}'"
        
        params = {
            'sql': query,
            'size': 1
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=params)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                return records[0] if records else None
            else:
                return None
                
        except Exception as e:
            print(f"  Error checking {pdl_id}: {str(e)}")
            return None
    
    def add_company_to_tracking(self, company: str, count: int) -> Dict:
        """Add employees from a company (APPENDS to existing tracking)"""
        
        print(f"\n[ADDING] {count} employees from {company}")
        
        # Fetch new employees
        employees = self.fetch_senior_employees(company, count)
        
        if employees:
            # Add to database (this APPENDS, doesn't overwrite)
            added, updated = self.db.add_employees(employees, company)
            
            print(f"  Added {added} new, updated {updated} existing")
            
            # Get updated stats
            stats = self.db.get_statistics()
            
            return {
                'success': True,
                'added': added,
                'updated': updated,
                'total_tracked': stats['total_tracked']
            }
        
        return {'success': False, 'added': 0, 'updated': 0}
    
    def get_tracking_status(self) -> Dict:
        """Get current tracking status and statistics"""
        
        # Get stats from database
        stats = self.db.get_statistics()
        
        return {
            'total_tracked': stats['total_tracked'],
            'active': stats['active'],
            'departed': stats['departed'],
            'companies': stats['companies'],
            'total_credits_used': stats['total_credits_used'],
            'last_fetch': stats['last_fetch']
        }
    
    def save_tracking_data(self, data: Dict):
        """Legacy method - data now saved in database"""
        # Data is now automatically saved in the database
        pass
    
    def load_tracking_data(self) -> Optional[Dict]:
        """Load tracking data from database"""
        employees = self.db.get_all_employees()
        if not employees:
            return None
        
        # Convert to old format for compatibility
        tracking_data = {
            'total_tracked': len(employees),
            'by_pdl_id': {},
            'companies': {}
        }
        
        for emp in employees:
            tracking_data['by_pdl_id'][emp['pdl_id']] = {
                'name': emp['name'],
                'company': emp['company'],
                'title': emp['title'],
                'status': emp['status'],
                'current_company': emp['current_company'] or emp['company'],
                'linkedin': emp.get('linkedin_url'),
                'last_checked': emp['last_checked']
            }
            
            # Count by company
            company = emp['company']
            if company not in tracking_data['companies']:
                tracking_data['companies'][company] = {'count': 0}
            tracking_data['companies'][company]['count'] += 1
        
        return tracking_data
    
    def save_departure_history(self, departures: List[Dict]):
        """Save departures to database"""
        for dep in departures:
            self.db.add_departure(dep)
    
    def get_scheduler_state(self) -> Dict:
        """Get the current scheduler state"""
        return self.db.get_scheduler_state()
    
    def update_scheduler_state(self, last_check: datetime = None, next_check: datetime = None,
                              enabled: bool = None, increment_count: bool = False):
        """Update the scheduler state"""
        return self.db.update_scheduler_state(last_check, next_check, enabled, increment_count)