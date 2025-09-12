"""
Fetch senior AI/ML employees from target companies
Optimized for tracking departures
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.target_companies import TARGET_COMPANIES, SENIOR_ROLES, SENIOR_LEVELS, AI_ML_KEYWORDS, AI_ML_SKILLS
from dotenv import load_dotenv

class SeniorEmployeeFetcher:
    """Fetch and track senior AI/ML employees from major tech companies"""
    
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
        
        # Directories
        self.snapshots_dir = Path(__file__).parent.parent / 'data' / 'snapshots'
        self.departures_dir = Path(__file__).parent.parent / 'data' / 'departures'
        self.alerts_dir = Path(__file__).parent.parent / 'data' / 'alerts'
        
        # Create directories
        for dir_path in [self.snapshots_dir, self.departures_dir, self.alerts_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def fetch_company_employees(self, company: str, max_credits: int = 50) -> List[Dict]:
        """
        Fetch senior AI/ML employees from a specific company
        """
        print(f"\n[FETCHING] Senior AI/ML employees from {company}")
        print(f"  Max credits: {max_credits}")
        
        # Build query for senior AI/ML employees currently at the company
        query = self._build_employee_query(company)
        
        params = {
            'sql': query,
            'size': max_credits
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=params)
            
            if response.status_code == 200:
                data = response.json()
                employees = data.get('data', [])
                total_available = data.get('total', 0)
                
                print(f"  Found: {len(employees)} employees")
                print(f"  Total available: {total_available}")
                
                # Filter for AI/ML relevance
                ai_ml_employees = self._filter_ai_ml_employees(employees)
                print(f"  AI/ML relevant: {len(ai_ml_employees)} employees")
                
                return ai_ml_employees
            else:
                print(f"  ERROR: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  EXCEPTION: {str(e)}")
            return []
    
    def _build_employee_query(self, company: str) -> str:
        """Build SQL query for fetching employees"""
        
        # Build role conditions
        roles_condition = " OR ".join([f"job_title_role = '{role}'" for role in SENIOR_ROLES])
        levels_condition = " OR ".join([f"job_title_levels = '{level}'" for level in SENIOR_LEVELS])
        
        query = f"""
        SELECT * FROM person 
        WHERE job_company_name = '{company.lower()}'
        AND ({roles_condition} OR {levels_condition})
        """
        
        return query.strip()
    
    def _filter_ai_ml_employees(self, employees: List[Dict]) -> List[Dict]:
        """Filter employees for AI/ML relevance"""
        ai_ml_employees = []
        
        for emp in employees:
            # Check job title
            job_title = (emp.get('job_title', '') or '').lower()
            job_summary = (emp.get('job_summary', '') or '').lower()
            
            # Check if title/summary contains AI/ML keywords
            is_ai_ml = any(keyword in job_title for keyword in AI_ML_KEYWORDS)
            is_ai_ml = is_ai_ml or any(keyword in job_summary for keyword in AI_ML_KEYWORDS)
            
            # Check skills
            skills = emp.get('skills', []) or []
            if skills and not is_ai_ml:
                skills_lower = [s.lower() for s in skills if s]
                is_ai_ml = any(skill in skills_lower for skill in AI_ML_SKILLS)
            
            if is_ai_ml:
                # Add tracking metadata
                emp['_tracked_company'] = emp.get('job_company_name', '')
                emp['_snapshot_date'] = datetime.now().isoformat()
                emp['_is_ai_ml'] = True
                ai_ml_employees.append(emp)
        
        return ai_ml_employees
    
    def fetch_all_companies(self, credits_per_company: int = 30) -> Dict[str, List[Dict]]:
        """
        Fetch employees from all target companies
        """
        all_employees = {}
        total_credits_used = 0
        
        print("\n" + "="*60)
        print("FETCHING SENIOR AI/ML EMPLOYEES FROM TARGET COMPANIES")
        print("="*60)
        
        for company in TARGET_COMPANIES:
            employees = self.fetch_company_employees(company, credits_per_company)
            all_employees[company] = employees
            total_credits_used += len(employees)
            
            # Save snapshot for this company
            self.save_company_snapshot(company, employees)
        
        print(f"\n[SUMMARY]")
        print(f"  Companies processed: {len(TARGET_COMPANIES)}")
        print(f"  Total employees tracked: {sum(len(emps) for emps in all_employees.values())}")
        print(f"  Total credits used: {total_credits_used}")
        
        return all_employees
    
    def save_company_snapshot(self, company: str, employees: List[Dict]):
        """Save a snapshot of employees for a company"""
        if not employees:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{company}_{timestamp}.jsonl"
        filepath = self.snapshots_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for emp in employees:
                f.write(json.dumps(emp) + '\n')
        
        print(f"  Saved: {filepath.name} ({len(employees)} employees)")
    
    def save_master_snapshot(self, all_employees: Dict[str, List[Dict]]):
        """Save a master snapshot of all employees"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSONL
        master_file = self.snapshots_dir / f"master_snapshot_{timestamp}.jsonl"
        
        with open(master_file, 'w', encoding='utf-8') as f:
            for company, employees in all_employees.items():
                for emp in employees:
                    emp['_snapshot_company'] = company
                    f.write(json.dumps(emp) + '\n')
        
        # Also save summary
        summary = {
            'timestamp': timestamp,
            'companies': list(all_employees.keys()),
            'total_employees': sum(len(emps) for emps in all_employees.values()),
            'by_company': {
                company: len(emps) for company, emps in all_employees.items()
            }
        }
        
        summary_file = self.snapshots_dir / f"master_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n[MASTER SNAPSHOT SAVED]")
        print(f"  Data: {master_file.name}")
        print(f"  Summary: {summary_file.name}")
        
        return master_file

def main():
    """Main function to fetch all employees"""
    
    fetcher = SeniorEmployeeFetcher()
    
    print("\n" + "="*60)
    print("SENIOR AI/ML EMPLOYEE TRACKER - INITIAL FETCH")
    print("="*60)
    print(f"\nTarget companies: {', '.join(TARGET_COMPANIES)}")
    print(f"This will fetch senior AI/ML employees from each company")
    
    # Ask for credits per company
    credits = input("\nCredits per company (default 30): ").strip()
    credits_per_company = int(credits) if credits else 30
    
    estimated_total = credits_per_company * len(TARGET_COMPANIES)
    print(f"\nEstimated max credits: {estimated_total}")
    
    confirm = input("Proceed? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled")
        return
    
    # Fetch all employees
    all_employees = fetcher.fetch_all_companies(credits_per_company)
    
    # Save master snapshot
    fetcher.save_master_snapshot(all_employees)
    
    print("\n" + "="*60)
    print("INITIAL FETCH COMPLETE")
    print("Next step: Run monthly_tracker.py to detect departures")
    print("="*60)

if __name__ == "__main__":
    main()