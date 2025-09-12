"""
Search for employees who departed from a specific company
Uses REST API with local filtering for accurate results
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.target_companies import SENIOR_ROLES, SENIOR_LEVELS, AI_ML_KEYWORDS, AI_ML_SKILLS
from dotenv import load_dotenv

class DepartureSearcher:
    """Search for recent departures from any company"""
    
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
    
    async def search_company_departures(
        self, 
        company_name: str, 
        days_back: int = 90,
        max_results: int = 100,
        include_all_tech: bool = False
    ) -> List[Dict]:
        """
        Search for employees who left a company within specified days
        
        Args:
            company_name: Company to search departures from
            days_back: How many days back to search
            max_results: Maximum results to return
            include_all_tech: Include all tech roles, not just AI/ML
            
        Returns:
            List of departed employees with details
        """
        
        print(f"\n[SEARCHING] Departures from {company_name}")
        print(f"  Days back: {days_back}")
        print(f"  Max results: {max_results}")
        print(f"  Include all tech: {include_all_tech}")
        
        # Phase 1: Fetch candidates who worked at company and changed jobs
        candidates = await self._fetch_candidates(company_name, days_back, max_results * 3)
        
        if not candidates:
            print("  No candidates found")
            return []
        
        print(f"  Phase 1: Found {len(candidates)} candidates")
        
        # Phase 2: Filter for actual departures
        departures = self._filter_actual_departures(
            candidates, 
            company_name, 
            days_back,
            include_all_tech
        )
        
        print(f"  Phase 2: Verified {len(departures)} actual departures")
        
        # Limit to max_results
        departures = departures[:max_results]
        
        # Enrich departure data
        enriched = self._enrich_departure_data(departures, company_name)
        
        return enriched
    
    async def _fetch_candidates(self, company_name: str, days_back: int, fetch_size: int) -> List[Dict]:
        """Fetch candidate employees who might have left"""
        
        # Calculate date range
        cutoff_date = (datetime.now() - timedelta(days=days_back + 30)).strftime('%Y-%m-%d')
        
        # Build SQL query - broader to catch more candidates
        sql_query = f"""
        SELECT * FROM person 
        WHERE experience.company.name = '{company_name.lower()}'
        AND job_last_changed >= '{cutoff_date}'
        AND job_company_name != '{company_name.lower()}'
        """
        
        # Add role filters for senior positions
        roles_sql = " OR ".join([f"job_title_role = '{role}'" for role in SENIOR_ROLES])
        levels_sql = " OR ".join([f"job_title_levels = '{level}'" for level in SENIOR_LEVELS])
        
        sql_query += f" AND ({roles_sql} OR {levels_sql})"
        
        params = {
            'sql': sql_query.strip(),
            'size': min(fetch_size, 500)  # Cap at 500
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                print(f"  API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  Exception: {str(e)}")
            return []
    
    def _filter_actual_departures(
        self, 
        candidates: List[Dict], 
        company_name: str, 
        days_back: int,
        include_all_tech: bool
    ) -> List[Dict]:
        """Filter candidates for actual departures within timeframe"""
        
        departures = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        company_lower = company_name.lower()
        
        for person in candidates:
            # Check experience array for actual departure
            for exp in person.get('experience', []):
                if not isinstance(exp, dict):
                    continue
                    
                company_data = exp.get('company', {})
                if not isinstance(company_data, dict):
                    continue
                    
                exp_company = (company_data.get('name', '') or '').lower()
                
                # Check if this is the target company
                if company_lower in exp_company:
                    end_date_str = exp.get('end_date')
                    
                    if end_date_str:
                        try:
                            # Parse end date
                            if len(end_date_str) == 7:  # YYYY-MM
                                end_date = datetime.strptime(end_date_str, '%Y-%m')
                            elif len(end_date_str) == 10:  # YYYY-MM-DD
                                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                            else:
                                continue
                            
                            # Check if they left within our window
                            if end_date >= cutoff_date:
                                # Check if AI/ML relevant or include all tech
                                if include_all_tech or self._is_ai_ml_relevant(person):
                                    person['_departure_date'] = end_date_str
                                    person['_departure_company'] = company_name
                                    person['_days_since_departure'] = (datetime.now() - end_date).days
                                    departures.append(person)
                                    break
                                    
                        except:
                            continue
        
        return departures
    
    def _is_ai_ml_relevant(self, person: Dict) -> bool:
        """Check if person is AI/ML relevant"""
        
        # Check job title
        job_title = (person.get('job_title', '') or '').lower()
        job_summary = (person.get('job_summary', '') or '').lower()
        
        # Check for AI/ML keywords
        for keyword in AI_ML_KEYWORDS:
            if keyword in job_title or keyword in job_summary:
                return True
        
        # Check skills
        skills = person.get('skills', []) or []
        if skills:
            skills_lower = [s.lower() for s in skills if s]
            for skill in AI_ML_SKILLS:
                if skill in skills_lower:
                    return True
        
        return False
    
    def _enrich_departure_data(self, departures: List[Dict], company_name: str) -> List[Dict]:
        """Enrich departure data with additional information"""
        
        enriched = []
        
        for person in departures:
            enriched_person = {
                'pdl_id': person.get('id') or person.get('pdl_id'),
                'name': person.get('full_name', 'Unknown'),
                'old_company': company_name,
                'old_title': self._get_title_at_company(person, company_name),
                'new_company': person.get('job_company_name', 'Unknown'),
                'new_title': person.get('job_title', 'Unknown'),
                'departure_date': person.get('_departure_date'),
                'days_since_departure': person.get('_days_since_departure'),
                'linkedin_url': person.get('linkedin_url'),
                'location': person.get('location_name'),
                'skills': person.get('skills', [])[:10],  # Top 10 skills
                'is_ai_ml': self._is_ai_ml_relevant(person),
                'seniority_level': self._get_seniority_level(person)
            }
            
            enriched.append(enriched_person)
        
        # Sort by departure date (most recent first)
        enriched.sort(key=lambda x: x['days_since_departure'])
        
        return enriched
    
    def _get_title_at_company(self, person: Dict, company_name: str) -> str:
        """Get the person's title at the specified company"""
        
        company_lower = company_name.lower()
        
        for exp in person.get('experience', []):
            if isinstance(exp, dict):
                company_data = exp.get('company', {})
                if isinstance(company_data, dict):
                    if company_lower in (company_data.get('name', '') or '').lower():
                        title_data = exp.get('title', {})
                        if isinstance(title_data, dict):
                            return title_data.get('name', 'Unknown')
                        return exp.get('title', 'Unknown') if isinstance(exp.get('title'), str) else 'Unknown'
        
        return 'Unknown'
    
    def _get_seniority_level(self, person: Dict) -> str:
        """Determine seniority level from job title"""
        
        job_title = (person.get('job_title', '') or '').lower()
        
        if any(level in job_title for level in ['chief', 'cto', 'ceo', 'cfo']):
            return 'C-Level'
        elif any(level in job_title for level in ['vp', 'vice president', 'head']):
            return 'VP/Head'
        elif any(level in job_title for level in ['director']):
            return 'Director'
        elif any(level in job_title for level in ['principal', 'staff']):
            return 'Principal/Staff'
        elif any(level in job_title for level in ['senior', 'lead']):
            return 'Senior/Lead'
        else:
            return 'Other'