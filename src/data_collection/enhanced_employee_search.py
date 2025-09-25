"""
Enhanced Employee Search with Monitoring Integration
Fetches employees and integrates with tiered monitoring system
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
        focus: Type of search ('recent_departures', 'stealth_signals', 'all')
    """
    
    company_clause = ' OR '.join([f'past_company:"{company}"' for company in companies])
    
    queries = {
        'recent_departures': f"""
            ({company_clause}) AND 
            job_last_changed:[{(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')} TO *] AND
            (NOT job_company_name:({' OR '.join([f'"{c}"' for c in companies])}))
        """,
        
        'stealth_signals': f"""
            ({company_clause}) AND
            (job_company_name:"stealth" OR 
             job_company_name:"building" OR
             job_company_name:"new venture" OR
             job_company_name:"consulting" OR
             job_company_name:"advisor" OR
             job_title:"founder" OR
             job_title:"co-founder" OR
             job_title:"building" OR
             job_title:"working on")
        """,
        
        'senior_departures': f"""
            ({company_clause}) AND
            (job_title_levels:("director" OR "vp" OR "head" OR "chief" OR "principal" OR "staff")) AND
            job_last_changed:[{(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')} TO *]
        """
    }
    
    return queries.get(focus, queries['recent_departures'])

def fetch_employees_with_monitoring(
    companies: List[str],
    total_limit: int = 5000,
    batch_size: int = 500,
    focus: str = 'recent_departures'
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
    
    # Fetch employees in batches
    offset = 0
    while len(all_employees) < total_limit:
        params = {
            'query': query,
            'size': min(batch_size, total_limit - len(all_employees)),
            'from': offset,
            'pretty': True
        }
        
        try:
            response = CLIENT.person.search(**params).json()
            
            if response.get('status') != 200:
                print(f"Error: {response}")
                break
            
            batch = response.get('data', [])
            if not batch:
                print("No more results")
                break
            
            all_employees.extend(batch)
            offset += len(batch)
            
            print(f"Fetched {len(all_employees)} employees so far...")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error fetching batch: {e}")
            break
    
    print(f"Total employees fetched: {len(all_employees)}")
    
    # Analyze and categorize employees
    categorized = stealth_detector.analyze_bulk_employees(all_employees)
    
    # Save to monitoring system
    monitoring_results = {
        'vip': [],
        'watch': [],
        'general': [],
        'stats': {
            'total_fetched': len(all_employees),
            'with_stealth_signals': 0,
            'recent_departures': 0,
            'senior_level': 0
        }
    }
    
    for tier in ['vip', 'watch', 'general']:
        for emp in categorized.get(tier, []):
            # Get original employee data
            original = next((e for e in all_employees if e.get('id') == emp['pdl_id']), None)
            
            if original:
                # Save snapshot for monitoring
                employment_monitor.save_snapshot(original)
                
                # Set up monitoring schedule
                employment_monitor.update_monitoring_schedule(
                    original,
                    tier=emp['tier'],
                    stealth_score=emp['stealth_score'],
                    signals=emp['signals']
                )
                
                # Add to results
                monitoring_results[tier].append({
                    'pdl_id': emp['pdl_id'],
                    'full_name': emp['full_name'],
                    'company': emp['job_company_name'],
                    'title': emp['job_title'],
                    'stealth_score': emp['stealth_score'],
                    'signals': emp['signals']
                })
                
                if emp['stealth_score'] >= 50:
                    monitoring_results['stats']['with_stealth_signals'] += 1
    
    # Calculate additional stats
    for emp in all_employees:
        # Recent departure
        job_changed = emp.get('job_last_changed')
        if job_changed:
            try:
                change_date = datetime.strptime(job_changed, '%Y-%m-%d')
                if (datetime.now() - change_date).days < 180:
                    monitoring_results['stats']['recent_departures'] += 1
            except:
                pass
        
        # Senior level
        levels = emp.get('job_title_levels', [])
        if any(level in ['director', 'vp', 'head', 'chief'] for level in levels):
            monitoring_results['stats']['senior_level'] += 1
    
    return monitoring_results

def save_monitoring_results(results: Dict, output_dir: str = "data/monitoring"):
    """Save monitoring results to files"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save categorized employees
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save VIP list
    vip_file = os.path.join(output_dir, f'vip_employees_{timestamp}.json')
    with open(vip_file, 'w') as f:
        json.dump(results['vip'], f, indent=2)
    print(f"Saved {len(results['vip'])} VIP employees to {vip_file}")
    
    # Save watch list
    watch_file = os.path.join(output_dir, f'watch_employees_{timestamp}.json')
    with open(watch_file, 'w') as f:
        json.dump(results['watch'], f, indent=2)
    print(f"Saved {len(results['watch'])} watch-list employees to {watch_file}")
    
    # Save general list
    general_file = os.path.join(output_dir, f'general_employees_{timestamp}.json')
    with open(general_file, 'w') as f:
        json.dump(results['general'], f, indent=2)
    print(f"Saved {len(results['general'])} general employees to {general_file}")
    
    # Save stats
    stats_file = os.path.join(output_dir, f'monitoring_stats_{timestamp}.json')
    with open(stats_file, 'w') as f:
        json.dump(results['stats'], f, indent=2)
    print(f"Saved statistics to {stats_file}")

def main():
    """Main execution"""
    
    print("=== Enhanced Employee Search with Monitoring ===")
    
    # Choose companies to monitor
    companies = TARGET_COMPANIES['big_tech'] + TARGET_COMPANIES['ai_companies']
    
    # Fetch and categorize employees
    print("\n1. Fetching recent departures...")
    departures = fetch_employees_with_monitoring(
        companies=companies[:5],  # Start with first 5 companies
        total_limit=2000,
        focus='recent_departures'
    )
    
    print("\n2. Fetching stealth signals...")
    stealth = fetch_employees_with_monitoring(
        companies=companies[:5],
        total_limit=1000,
        focus='stealth_signals'
    )
    
    # Combine results
    combined_results = {
        'vip': departures['vip'] + stealth['vip'],
        'watch': departures['watch'] + stealth['watch'],
        'general': departures['general'] + stealth['general'],
        'stats': {
            'total_fetched': departures['stats']['total_fetched'] + stealth['stats']['total_fetched'],
            'with_stealth_signals': departures['stats']['with_stealth_signals'] + stealth['stats']['with_stealth_signals'],
            'recent_departures': departures['stats']['recent_departures'],
            'senior_level': departures['stats']['senior_level'] + stealth['stats'].get('senior_level', 0)
        }
    }
    
    # Save results
    print("\n3. Saving monitoring results...")
    save_monitoring_results(combined_results)
    
    # Print summary
    print("\n=== MONITORING SETUP COMPLETE ===")
    print(f"Total employees analyzed: {combined_results['stats']['total_fetched']}")
    print(f"VIP tier (daily checks): {len(combined_results['vip'])}")
    print(f"Watch tier (weekly checks): {len(combined_results['watch'])}")
    print(f"General tier (monthly checks): {len(combined_results['general'])}")
    print(f"With stealth signals: {combined_results['stats']['with_stealth_signals']}")
    print(f"Recent departures: {combined_results['stats']['recent_departures']}")
    print(f"Senior level: {combined_results['stats']['senior_level']}")
    
    # Calculate costs
    daily_cost = (
        len(combined_results['vip']) * 0.01 +
        len(combined_results['watch']) * 0.01 / 7 +
        len(combined_results['general']) * 0.01 / 30
    )
    print(f"\nEstimated daily monitoring cost: ${daily_cost:.2f}")
    print(f"Estimated monthly monitoring cost: ${daily_cost * 30:.2f}")

if __name__ == "__main__":
    main()