"""
Enhanced Employee Search with Monitoring Integration - UPDATED VERSION
Fetches employees and integrates with tiered monitoring system
IMPROVEMENTS:
- Added seniority level filters
- Enhanced stealth signals with company size and founded date
- Added technical expertise filter
- Improved departure timing with profile updates
- Added new query focus types
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

from src.data_collection.pdl_client import get_pdl_client
from src.monitoring.stealth_detector import StealthFounderDetector
from src.monitoring.employment_monitor import EmploymentMonitor

CLIENT = get_pdl_client()

# Target companies to monitor
TARGET_COMPANIES = {
    'big_tech': [
        'google', 'meta', 'facebook', 'apple', 'microsoft', 
        'amazon', 'netflix'
    ],
    'ai_companies': [
        'openai', 'anthropic', 'deepmind', 'inflection ai',
        'cohere', 'hugging face', 'stability ai'
    ],
    'hot_startups': [
        'stripe', 'databricks', 'canva', 'figma', 'notion',
        'airtable', 'vercel', 'supabase'
    ]
}

def build_enhanced_query(companies: List[str], focus: str = 'recent_departures') -> str:
    """
    Build enhanced PDL query based on monitoring needs
    
    Args:
        companies: List of company names
        focus: Type of search ('recent_departures', 'stealth_signals', 'senior_departures', 
                               'technical_founders', 'very_recent_departures')
    """
    
    company_clause = ' OR '.join([f'past_company:"{company}"' for company in companies])
    
    # Calculate date ranges
    last_30_days = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    last_90_days = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    last_180_days = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    last_365_days = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    queries = {
        'recent_departures': f"""
            ({company_clause}) AND 
            job_last_changed:[{last_180_days} TO *] AND
            (NOT job_company_name:({' OR '.join([f'"{c}"' for c in companies])}))
        """,
        
        # UPDATED: Enhanced stealth signals with company size and founding date
        'stealth_signals': f"""
            ({company_clause}) AND
            (job_company_name:"stealth" OR 
             job_company_name:"building" OR
             job_company_name:"new venture" OR
             job_company_name:"consulting" OR
             job_company_name:"advisor" OR
             job_company_name:"labs" OR
             job_company_name:"research" OR
             job_title:"founder" OR
             job_title:"co-founder" OR
             job_title:"cofounder" OR
             job_title:"cto" OR
             job_title:"ceo" OR
             job_title:"chief" OR
             job_title:"founding engineer" OR
             job_title:"technical co-founder" OR
             job_title:"building" OR
             job_title:"working on") AND
            (job_company_size:"1-10" OR job_company_size:"11-50") AND
            job_company_founded:[2022 TO *]
        """,
        
        # UPDATED: Added more seniority levels
        'senior_departures': f"""
            ({company_clause}) AND
            (job_title_levels:("senior" OR "staff" OR "principal" OR 
                               "director" OR "vp" OR "head" OR "chief")) AND
            job_last_changed:[{last_365_days} TO *]
        """,
        
        # NEW: Technical founders with specific AI/ML skills
        'technical_founders': f"""
            ({company_clause}) AND
            (skills:("machine learning" OR "deep learning" OR "llm" OR 
                    "large language models" OR "pytorch" OR "tensorflow" OR
                    "generative ai" OR "computer vision" OR "nlp")) AND
            (job_title_levels:("senior" OR "staff" OR "principal" OR "lead")) AND
            job_last_changed:[{last_180_days} TO *] AND
            (job_company_size:"1-10" OR job_company_size:"11-50" OR 
             job_company_name:"stealth" OR job_company_name:"building")
        """,
        
        # NEW: Very recent departures with profile updates
        'very_recent_departures': f"""
            ({company_clause}) AND
            job_last_changed:[{last_30_days} TO *] AND
            job_last_updated:[{last_30_days} TO *] AND
            job_start_date:[2024 TO *] AND
            (NOT job_company_name:({' OR '.join([f'"{c}"' for c in companies])}))
        """,
        
        # NEW: Potential co-founder groups (people who left same company recently)
        'cofounder_patterns': f"""
            ({company_clause}) AND
            job_last_changed:[{last_90_days} TO *] AND
            (job_company_size:"1-10") AND
            (job_title:"co-founder" OR job_title:"founding" OR 
             job_company_name:"stealth" OR job_company_name:"new venture")
        """
    }
    
    return queries.get(focus, queries['recent_departures'])

def fetch_employees_with_monitoring(
    companies: List[str],
    total_limit: int = 5000,
    batch_size: int = 500,
    focus: str = 'recent_departures',
    min_seniority: bool = True  # NEW: Filter for senior roles only
) -> Dict:
    """
    Fetch employees and categorize them for monitoring
    
    Returns dict with employees categorized by monitoring tier
    """
    
    print(f"Fetching {focus} from {len(companies)} companies...")
    
    # Initialize detectors
    stealth_detector = StealthFounderDetector()
    employment_monitor = EmploymentMonitor()
    
    all_employees = []
    query = build_enhanced_query(companies, focus)
    
    # Add seniority filter if requested
    if min_seniority and focus not in ['senior_departures', 'technical_founders']:
        query += ' AND (job_title_levels:("senior" OR "lead" OR "principal" OR "staff" OR "manager" OR "director" OR "vp" OR "head"))'
    
    params = {
        'query': query,
        'size': min(batch_size, total_limit),
        'from': 0,
        'pretty': True
    }
    
    total_fetched = 0
    api_calls = 0
    
    while total_fetched < total_limit:
        try:
            response = CLIENT.person.search(**params)
            api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                batch_employees = data.get('data', [])
                
                if not batch_employees:
                    print(f"No more results after {total_fetched} employees")
                    break
                
                all_employees.extend(batch_employees)
                total_fetched += len(batch_employees)
                
                print(f"  Fetched {len(batch_employees)} employees (Total: {total_fetched})")
                
                # Check if more results available
                total_available = data.get('total', 0)
                if total_fetched >= total_available:
                    break
                
                # Update pagination
                params['from'] = total_fetched
                params['size'] = min(batch_size, total_limit - total_fetched)
                
                # Rate limiting
                time.sleep(0.5)
                
            else:
                print(f"API Error: {response.status_code}")
                break
                
        except Exception as e:
            print(f"Error fetching employees: {e}")
            break
    
    print(f"Total API calls: {api_calls}")
    print(f"Total employees fetched: {len(all_employees)}")
    
    # Analyze for stealth signals
    monitoring_results = stealth_detector.analyze_bulk_employees(all_employees)
    
    # Add employment monitoring setup
    for tier in ['vip', 'watch', 'general']:
        tier_employees = monitoring_results.get(tier, [])
        for employee in tier_employees:
            schedule = stealth_detector.get_monitoring_priority(employee)
            employment_monitor.add_employee(employee, schedule)
    
    return monitoring_results

def run_multi_focus_search(
    companies: List[str],
    budget_per_focus: int = 1000
) -> Dict:
    """
    Run multiple focused searches for comprehensive coverage
    """
    
    # Define search priorities
    search_focuses = [
        'very_recent_departures',  # Highest priority
        'stealth_signals',          # Direct founder signals  
        'technical_founders',       # Technical expertise
        'cofounder_patterns',       # Team formation
        'senior_departures'         # General senior movement
    ]
    
    all_results = {
        'vip': [],
        'watch': [],
        'general': [],
        'stats': {
            'total_analyzed': 0,
            'by_focus': {}
        }
    }
    
    for focus in search_focuses:
        print(f"\n{'='*60}")
        print(f"Running {focus} search...")
        print(f"{'='*60}")
        
        results = fetch_employees_with_monitoring(
            companies=companies,
            total_limit=budget_per_focus,
            focus=focus,
            min_seniority=True
        )
        
        # Merge results
        for tier in ['vip', 'watch', 'general']:
            all_results[tier].extend(results.get(tier, []))
        
        # Track stats
        focus_total = sum(len(results.get(tier, [])) for tier in ['vip', 'watch', 'general'])
        all_results['stats']['by_focus'][focus] = focus_total
        all_results['stats']['total_analyzed'] += focus_total
        
        # Deduplicate by PDL ID
        for tier in ['vip', 'watch', 'general']:
            seen_ids = set()
            unique_employees = []
            for emp in all_results[tier]:
                emp_id = emp.get('pdl_id')
                if emp_id and emp_id not in seen_ids:
                    seen_ids.add(emp_id)
                    unique_employees.append(emp)
            all_results[tier] = unique_employees
    
    return all_results

def save_monitoring_results(results: Dict, output_dir: str = 'data/monitoring'):
    """
    Save categorized monitoring results
    """
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save by tier
    for tier in ['vip', 'watch', 'general']:
        tier_file = os.path.join(output_dir, f'{tier}_tier_{timestamp}.jsonl')
        with open(tier_file, 'w', encoding='utf-8') as f:
            for employee in results.get(tier, []):
                f.write(json.dumps(employee) + '\n')
        
        print(f"Saved {len(results.get(tier, []))} {tier} employees to {tier_file}")
    
    # Save statistics
    stats_file = os.path.join(output_dir, f'search_stats_{timestamp}.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(results.get('stats', {}), f, indent=2)
    
    print(f"Saved statistics to {stats_file}")

if __name__ == "__main__":
    # Test with targeted search
    test_companies = ['openai', 'anthropic', 'google', 'meta']
    
    # Run comprehensive multi-focus search
    results = run_multi_focus_search(
        companies=test_companies,
        budget_per_focus=500  # Adjust based on API credits
    )
    
    # Save results
    save_monitoring_results(results)
    
    # Print summary
    print("\n" + "="*60)
    print("SEARCH SUMMARY")
    print("="*60)
    print(f"Total unique profiles analyzed: {results['stats']['total_analyzed']}")
    print(f"VIP tier (daily monitoring): {len(results['vip'])}")
    print(f"Watch tier (weekly monitoring): {len(results['watch'])}")
    print(f"General tier (monthly monitoring): {len(results['general'])}")
    
    print("\nBy search focus:")
    for focus, count in results['stats']['by_focus'].items():
        print(f"  {focus}: {count} profiles")