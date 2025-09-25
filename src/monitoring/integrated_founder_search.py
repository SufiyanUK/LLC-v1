"""
Integrated Founder Search System
Uses company and job role configurations for targeted searching
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

from config.companies import AI_FOCUSED_BIG_TECH, ONLY_AI_TECH, TRADITIONAL_BIG_TECH
from config.job_roles import (
    AI_ML_ROLES, AI_ML_SUBROLES, 
    AI_ML_SUPPORTING_ROLES, AI_ML_SUPPORTING_SUBROLES,
    EXCLUDE_SUBROLES
)
from src.data_collection.pdl_client import get_pdl_client
from src.monitoring.stealth_detector import StealthFounderDetector
from src.monitoring.employment_monitor import EmploymentMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedFounderSearch:
    """
    Integrated search system using company and role configurations
    """
    
    def __init__(self):
        self.client = get_pdl_client()
        self.stealth_detector = StealthFounderDetector()
        self.employment_monitor = EmploymentMonitor()
        
        # Priority scoring weights
        self.company_weights = {
            'only_ai': 30,      # OpenAI, Anthropic, DeepMind
            'ai_focused': 20,   # Google, Meta, Microsoft
            'traditional': 10   # Adobe, Oracle, IBM
        }
        
        self.role_weights = {
            'ai_ml_core': 25,       # Research, engineering
            'ai_ml_subrole': 20,    # Data science, ML engineering
            'supporting': 10,       # Product, BD
            'other': 5
        }
    
    def get_company_priority(self, company_name: str) -> Tuple[int, str]:
        """
        Get priority weight for a company
        Returns (weight, category)
        """
        company_lower = company_name.lower()
        
        if any(comp in company_lower for comp in ONLY_AI_TECH):
            return self.company_weights['only_ai'], 'only_ai'
        elif any(comp in company_lower for comp in AI_FOCUSED_BIG_TECH):
            return self.company_weights['ai_focused'], 'ai_focused'
        elif any(comp in company_lower for comp in TRADITIONAL_BIG_TECH):
            return self.company_weights['traditional'], 'traditional'
        else:
            return 0, 'other'
    
    def get_role_priority(self, job_title_role: str, job_title_sub_role: str) -> Tuple[int, str]:
        """
        Get priority weight for a role
        Returns (weight, category)
        """
        role_lower = (job_title_role or '').lower()
        subrole_lower = (job_title_sub_role or '').lower()
        
        # Check exclusions first
        if any(exclude in subrole_lower for exclude in EXCLUDE_SUBROLES):
            return 0, 'excluded'
        
        # Check AI/ML core roles
        if role_lower in AI_ML_ROLES:
            return self.role_weights['ai_ml_core'], 'ai_ml_core'
        
        # Check AI/ML subroles
        if subrole_lower in AI_ML_SUBROLES:
            return self.role_weights['ai_ml_subrole'], 'ai_ml_subrole'
        
        # Check supporting roles
        if role_lower in AI_ML_SUPPORTING_ROLES or subrole_lower in AI_ML_SUPPORTING_SUBROLES:
            return self.role_weights['supporting'], 'supporting'
        
        return self.role_weights['other'], 'other'
    
    def build_employee_search_queries(self) -> Dict[str, str]:
        """
        Build SQL queries for finding potential founders from target companies
        """
        
        # Convert lists to SQL-friendly format
        ai_companies_sql = "'" + "', '".join(AI_FOCUSED_BIG_TECH) + "'"
        only_ai_sql = "'" + "', '".join(ONLY_AI_TECH) + "'"
        ai_roles_sql = "'" + "', '".join(AI_ML_ROLES) + "'"
        ai_subroles_sql = "'" + "', '".join(AI_ML_SUBROLES) + "'"
        
        queries = {
            # Priority 1: Recent departures from pure AI companies
            'ai_company_departures': f"""
                SELECT * FROM person
                WHERE experience.company.name IN ({only_ai_sql})
                AND job_last_changed >= '{(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')}'
                AND (job_company_size = '1-10' 
                     OR job_company_name ILIKE '%stealth%'
                     OR job_company_name IS NULL
                     OR job_title ILIKE '%founder%')
                LIMIT 100
            """,
            
            # Priority 2: AI/ML roles who became founders
            'ai_role_founders': f"""
                SELECT * FROM person
                WHERE (job_title_role IN ({ai_roles_sql}) 
                       OR job_title_sub_role IN ({ai_subroles_sql}))
                AND (job_title ILIKE '%founder%' 
                     OR job_title ILIKE '%co-founder%'
                     OR job_title ILIKE '%building%'
                     OR job_company_name ILIKE '%stealth%')
                AND job_company_size IN ('1-10', '11-50')
                LIMIT 100
            """,
            
            # Priority 3: Recent big tech departures with small company moves
            'big_tech_to_startup': f"""
                SELECT * FROM person
                WHERE experience.company.name IN ({ai_companies_sql})
                AND job_company_size = '1-10'
                AND job_last_changed >= '{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')}'
                AND (job_title_role IN ({ai_roles_sql}) 
                     OR job_title_sub_role IN ({ai_subroles_sql}))
                LIMIT 100
            """,
            
            # Priority 4: Stealth mode indicators
            'stealth_signals': f"""
                SELECT * FROM person
                WHERE experience.company.name IN ({ai_companies_sql}, {only_ai_sql})
                AND (job_company_name ILIKE '%building something%'
                     OR job_company_name ILIKE '%stealth%'
                     OR job_company_name ILIKE '%new venture%'
                     OR job_title ILIKE '%working on%')
                LIMIT 100
            """
        }
        
        return queries
    
    def build_startup_search_queries(self) -> Dict[str, str]:
        """
        Build SQL queries for finding AI/ML startups
        """
        
        queries = {
            # AI/ML focused startups
            'ai_ml_startups': """
                SELECT * FROM company
                WHERE (industry ILIKE '%artificial intelligence%'
                       OR industry ILIKE '%machine learning%'
                       OR industry = 'computer software'
                       OR name ILIKE '%AI%'
                       OR name ILIKE '%.ai'
                       OR summary ILIKE '%artificial intelligence%'
                       OR summary ILIKE '%machine learning%'
                       OR summary ILIKE '%deep learning%')
                AND founded >= 2022
                AND employee_count <= 50
                AND size IN ('1-10', '11-50')
                LIMIT 100
            """,
            
            # Stealth AI companies
            'stealth_ai_companies': """
                SELECT * FROM company
                WHERE (name ILIKE '%stealth%'
                       OR name ILIKE '%labs%'
                       OR name ILIKE '%research%')
                AND size = '1-10'
                AND founded >= 2023
                AND (industry = 'computer software'
                     OR industry ILIKE '%technology%')
                LIMIT 50
            """,
            
            # Companies in key AI hubs
            'ai_hub_startups': """
                SELECT * FROM company
                WHERE location.locality IN ('san francisco', 'palo alto', 
                                           'mountain view', 'menlo park',
                                           'seattle', 'redmond',
                                           'new york', 'boston')
                AND industry IN ('computer software', 'internet', 
                                'information technology and services')
                AND founded >= 2022
                AND employee_count BETWEEN 1 AND 20
                LIMIT 100
            """
        }
        
        return queries
    
    def calculate_founder_priority_score(self, employee: Dict) -> Tuple[float, Dict]:
        """
        Calculate priority score for an employee based on company and role
        Returns (score, breakdown)
        """
        score = 0
        breakdown = {
            'company_score': 0,
            'role_score': 0,
            'stealth_score': 0,
            'timing_score': 0,
            'total': 0
        }
        
        # 1. Company score - check all past companies
        max_company_score = 0
        best_company = None
        experiences = employee.get('experience', [])
        
        for exp in experiences:
            if isinstance(exp, dict):
                company_name = exp.get('company', {}).get('name', '') if isinstance(exp.get('company'), dict) else ''
                company_score, company_type = self.get_company_priority(company_name)
                if company_score > max_company_score:
                    max_company_score = company_score
                    best_company = (company_name, company_type)
        
        breakdown['company_score'] = max_company_score
        score += max_company_score
        
        # 2. Role score
        role_score, role_type = self.get_role_priority(
            employee.get('job_title_role', ''),
            employee.get('job_title_sub_role', '')
        )
        breakdown['role_score'] = role_score
        score += role_score
        
        # 3. Stealth signals
        stealth_score, signals, tier = self.stealth_detector.detect_stealth_signals(employee)
        breakdown['stealth_score'] = stealth_score / 2  # Scale to 0-50
        score += stealth_score / 2
        
        # 4. Timing score - recent departure
        job_changed = employee.get('job_last_changed')
        if job_changed:
            try:
                change_date = datetime.strptime(job_changed, '%Y-%m-%d')
                days_since = (datetime.now() - change_date).days
                
                if days_since <= 30:
                    breakdown['timing_score'] = 20
                elif days_since <= 90:
                    breakdown['timing_score'] = 15
                elif days_since <= 180:
                    breakdown['timing_score'] = 10
                elif days_since <= 365:
                    breakdown['timing_score'] = 5
                
                score += breakdown['timing_score']
            except:
                pass
        
        breakdown['total'] = score
        breakdown['best_company'] = best_company
        breakdown['role_type'] = role_type
        
        return score, breakdown
    
    def determine_monitoring_tier(self, employee: Dict, priority_score: float, breakdown: Dict) -> str:
        """
        Determine monitoring tier based on company, role, and score
        """
        
        # VIP Tier - Daily monitoring
        if priority_score >= 80:
            return 'vip'
        
        # Special case: ONLY_AI_TECH companies with AI roles
        if breakdown.get('best_company'):
            company_name, company_type = breakdown['best_company']
            if company_type == 'only_ai' and breakdown['role_score'] >= 20:
                return 'vip'
        
        # Watch Tier - Weekly monitoring
        if priority_score >= 50:
            return 'watch'
        
        # AI-focused companies with relevant roles
        if breakdown['company_score'] >= 20 and breakdown['role_score'] >= 15:
            return 'watch'
        
        # General Tier - Monthly monitoring
        return 'general'
    
    def search_and_categorize_employees(self, limit_per_query: int = 50) -> Dict:
        """
        Execute searches and categorize employees
        """
        logger.info("Starting integrated founder search...")
        
        results = {
            'vip': [],
            'watch': [],
            'general': [],
            'stats': {
                'total_searched': 0,
                'from_only_ai': 0,
                'from_ai_focused': 0,
                'with_ai_roles': 0,
                'stealth_signals': 0
            }
        }
        
        # Execute each search query
        queries = self.build_employee_search_queries()
        
        for query_name, sql_query in queries.items():
            logger.info(f"Executing query: {query_name}")
            
            try:
                params = {
                    'sql': sql_query,
                    'size': limit_per_query
                }
                
                response = self.client.person.search(**params).json()
                
                if response.get('status') == 200:
                    employees = response.get('data', [])
                    logger.info(f"  Found {len(employees)} employees")
                    
                    for emp in employees:
                        # Calculate priority score
                        priority_score, breakdown = self.calculate_founder_priority_score(emp)
                        
                        # Determine tier
                        tier = self.determine_monitoring_tier(emp, priority_score, breakdown)
                        
                        # Store employee with metadata
                        emp_data = {
                            'pdl_id': emp.get('id'),
                            'full_name': emp.get('full_name'),
                            'job_company_name': emp.get('job_company_name'),
                            'job_title': emp.get('job_title'),
                            'priority_score': priority_score,
                            'breakdown': breakdown,
                            'tier': tier
                        }
                        
                        # Add to appropriate tier
                        results[tier].append(emp_data)
                        
                        # Update stats
                        results['stats']['total_searched'] += 1
                        
                        if breakdown.get('best_company'):
                            _, company_type = breakdown['best_company']
                            if company_type == 'only_ai':
                                results['stats']['from_only_ai'] += 1
                            elif company_type == 'ai_focused':
                                results['stats']['from_ai_focused'] += 1
                        
                        if breakdown['role_score'] >= 20:
                            results['stats']['with_ai_roles'] += 1
                        
                        if breakdown['stealth_score'] >= 25:
                            results['stats']['stealth_signals'] += 1
                        
                        # Save to monitoring database
                        self.employment_monitor.save_snapshot(emp)
                        self.employment_monitor.update_monitoring_schedule(
                            emp, tier, priority_score, 
                            [f"Priority: {priority_score:.1f}", 
                             f"Company: {breakdown.get('best_company', ['Unknown'])[0] if breakdown.get('best_company') else 'Unknown'}",
                             f"Role: {breakdown.get('role_type', 'other')}"]
                        )
                else:
                    logger.error(f"  Query failed: {response.get('error')}")
                    
            except Exception as e:
                logger.error(f"  Exception in {query_name}: {str(e)[:100]}")
        
        return results
    
    def search_ai_startups(self, limit_per_query: int = 50) -> List[Dict]:
        """
        Search for AI/ML startups
        """
        logger.info("Searching for AI/ML startups...")
        
        all_startups = []
        queries = self.build_startup_search_queries()
        
        for query_name, sql_query in queries.items():
            logger.info(f"Executing query: {query_name}")
            
            try:
                params = {
                    'sql': sql_query,
                    'size': limit_per_query
                }
                
                response = self.client.company.search(**params).json()
                
                if response.get('status') == 200:
                    companies = response.get('data', [])
                    logger.info(f"  Found {len(companies)} companies")
                    
                    for company in companies:
                        # Add metadata
                        company['query_source'] = query_name
                        company['is_ai_startup'] = self._is_ai_startup(company)
                        all_startups.append(company)
                else:
                    logger.error(f"  Query failed: {response.get('error')}")
                    
            except Exception as e:
                logger.error(f"  Exception in {query_name}: {str(e)[:100]}")
        
        return all_startups
    
    def _is_ai_startup(self, company: Dict) -> bool:
        """
        Check if company is likely an AI/ML startup
        """
        indicators = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'computer vision', 'nlp', 'natural language',
            'data science', 'predictive', 'algorithm'
        ]
        
        company_text = ' '.join([
            company.get('name', ''),
            company.get('industry', ''),
            company.get('summary', '')
        ]).lower()
        
        return any(indicator in company_text for indicator in indicators)
    
    def generate_report(self, results: Dict) -> str:
        """
        Generate summary report of findings
        """
        report = f"""
=== INTEGRATED FOUNDER SEARCH REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 SEARCH STATISTICS
Total Employees Analyzed: {results['stats']['total_searched']}
From Pure AI Companies (OpenAI, Anthropic, etc.): {results['stats']['from_only_ai']}
From AI-Focused Big Tech: {results['stats']['from_ai_focused']}
With AI/ML Roles: {results['stats']['with_ai_roles']}
Showing Stealth Signals: {results['stats']['stealth_signals']}

📈 MONITORING DISTRIBUTION
VIP Tier (Daily Monitoring): {len(results['vip'])} employees
  - Highest priority targets
  - From OpenAI/Anthropic or showing strong founder signals
  
Watch Tier (Weekly Monitoring): {len(results['watch'])} employees
  - Medium priority targets
  - From Google/Meta with AI roles
  
General Tier (Monthly Monitoring): {len(results['general'])} employees
  - Lower priority but still relevant

💰 ESTIMATED COSTS
Daily Monitoring Cost: ${(len(results['vip']) * 0.01 + len(results['watch']) * 0.01/7 + len(results['general']) * 0.01/30):.2f}
Monthly Cost: ${(len(results['vip']) * 0.01 + len(results['watch']) * 0.01/7 + len(results['general']) * 0.01/30) * 30:.2f}

🎯 TOP VIP TARGETS
"""
        
        # Add top VIP targets
        for emp in results['vip'][:10]:
            report += f"\n{emp['full_name']} (Score: {emp['priority_score']:.1f})"
            report += f"\n  Company: {emp['job_company_name']}"
            report += f"\n  Title: {emp['job_title']}"
            if emp['breakdown'].get('best_company'):
                report += f"\n  From: {emp['breakdown']['best_company'][0]}"
            report += "\n"
        
        return report


def main():
    """Main execution"""
    searcher = IntegratedFounderSearch()
    
    print("=" * 60)
    print("INTEGRATED FOUNDER SEARCH SYSTEM")
    print("=" * 60)
    
    # Search and categorize employees
    print("\nSearching for potential founders...")
    results = searcher.search_and_categorize_employees(limit_per_query=20)
    
    # Search for startups
    print("\nSearching for AI/ML startups...")
    startups = searcher.search_ai_startups(limit_per_query=20)
    
    # Generate report
    report = searcher.generate_report(results)
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'data/monitoring/integrated_search_{timestamp}.json'
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'employees': results,
            'startups': [{'name': s.get('name'), 'founded': s.get('founded'), 
                         'size': s.get('size')} for s in startups[:20]],
            'timestamp': timestamp
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Search complete!")


if __name__ == "__main__":
    main()