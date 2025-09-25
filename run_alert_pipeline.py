"""
Main Alert Pipeline Integration
Demonstrates how to use the Three-Level Alert System with real data
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

# Import all necessary modules
from src.data_collection.pdl_client import get_pdl_client
from src.utils.query_updated import build_simple_sql_query, get_optimal_query_sequence
from src.alerts.three_level_alert_system import ThreeLevelAlertSystem


class AlertPipeline:
    """
    Complete pipeline for alert generation
    """
    
    def __init__(self):
        """Initialize the alert pipeline"""
        load_dotenv()
        
        # Check API key
        if not os.getenv('API_KEY'):
            raise ValueError("No API_KEY found in .env file!")
        
        self.client = get_pdl_client()
        self.alert_system = ThreeLevelAlertSystem()
        
        # Statistics tracking
        self.stats = {
            'api_credits_used': 0,
            'employees_fetched': 0,
            'alerts_generated': {
                'LEVEL_3': 0,
                'LEVEL_2': 0,
                'LEVEL_1': 0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def fetch_recent_departures(self, days_back: int = 30, max_credits: int = 10):
        """
        Fetch employees who recently left big tech companies
        
        Args:
            days_back: How many days back to search
            max_credits: Maximum API credits to use
        """
        print(f"\n[FETCHING] RECENT DEPARTURES (Last {days_back} days)")
        print("="*60)
        
        # Build optimized query for recent departures
        companies = self.alert_system.big_tech_companies[:10]  # Top 10 companies
        
        # Use the high_potential query type for best results
        query = build_simple_sql_query(
            companies=companies,
            query_type='high_potential'
        )
        
        print(f"Target companies: {', '.join(companies[:5])}...")
        print(f"Max credits: {max_credits}")
        
        # Fetch from PDL
        params = {
            'query': query,
            'size': max_credits,  # 1 credit per record
            'pretty': True
        }
        
        try:
            response = self.client.person.search(**params)
            
            if response.status_code == 200:
                data = response.json()
                employees = data.get('data', [])
                
                self.stats['api_credits_used'] = len(employees)
                self.stats['employees_fetched'] = len(employees)
                
                print(f"[OK] Fetched {len(employees)} employees using {len(employees)} credits")
                return employees
            else:
                print(f"❌ API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []
    
    def process_and_generate_alerts(self, employees: list):
        """
        Process employees and generate alerts
        
        Args:
            employees: List of employee records from PDL
        """
        print(f"\n[PROCESSING] {len(employees)} EMPLOYEES")
        print("="*60)
        
        # Process employees to extract structured data
        from src.data_processing.employee_processor import (
            extract_location, get_current_company, get_previous_companies,
            get_last_role, get_last_big_tech_departure, extract_education
        )
        from config.companies import AI_FOCUSED_BIG_TECH
        
        processed_employees = []
        for emp in employees:
            processed = {
                'pdl_id': emp.get('id'),
                'full_name': emp.get('full_name'),
                'first_name': emp.get('first_name'),
                'last_name': emp.get('last_name'),
                'location': extract_location(emp),
                'current_company': get_current_company(emp),
                'previous_companies': get_previous_companies(emp),
                'last_known_role': get_last_role(emp),
                'last_big_tech_departure': get_last_big_tech_departure(emp, AI_FOCUSED_BIG_TECH),
                'linkedin_url': emp.get('linkedin_url'),
                'skills': emp.get('skills', []),
                'education': extract_education(emp),
                'experience': emp.get('experience', []),
                
                # Include raw fields needed for alert detection
                'job_company_name': emp.get('job_company_name'),
                'job_title': emp.get('job_title'),
                'job_company_size': emp.get('job_company_size'),
                'job_last_changed': emp.get('job_last_changed'),
                'job_last_updated': emp.get('job_last_updated'),
                'job_title_role': emp.get('job_title_role'),
                'job_title_sub_role': emp.get('job_title_sub_role'),
                'summary': emp.get('summary'),
                'headline': emp.get('headline')
            }
            processed_employees.append(processed)
        
        print(f"[OK] Processed {len(processed_employees)} employees")
        
        # Generate alerts
        print(f"\n[GENERATING] ALERTS")
        print("="*60)
        
        results = self.alert_system.analyze_employees(processed_employees)
        
        # Update statistics
        for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
            self.stats['alerts_generated'][level] = results['stats'][f'{level.lower()}_count']
        
        return results
    
    def display_alerts(self, results: dict):
        """
        Display alerts in a formatted way
        
        Args:
            results: Alert results from the alert system
        """
        print(f"\n[SUMMARY] ALERT SUMMARY")
        print("="*60)
        print(f"Total Analyzed: {results['stats']['total_analyzed']}")
        print(f"Eligible for Alerts: {results['stats']['eligible_for_alerts']}")
        print(f"Average Founder Score: {results['stats']['avg_founder_score']}")
        print(f"Average Stealth Score: {results['stats']['avg_stealth_score']}")
        
        # Level 3 Alerts (HIGHEST PRIORITY)
        if results['LEVEL_3']:
            print(f"\n[LEVEL 3] JOINED QUALIFIED STARTUP ({len(results['LEVEL_3'])})")
            print("-"*60)
            for alert in results['LEVEL_3'][:5]:  # Top 5
                print(f"\n  * {alert['full_name']}")
                print(f"   Current: {alert.get('startup_info', {}).get('startup_name', 'Unknown')}")
                print(f"   Previous: {alert.get('departure_info', {}).get('company', 'Unknown')}")
                print(f"   Founder Score: {alert['founder_score']:.1f} | Stealth Score: {alert['stealth_score']:.0f}")
                print(f"   Action: IMMEDIATE CONTACT - Already at funded startup")
        
        # Level 2 Alerts (HIGH PRIORITY)
        if results['LEVEL_2']:
            print(f"\n[LEVEL 2] BUILDING SIGNALS ({len(results['LEVEL_2'])})")
            print("-"*60)
            for alert in results['LEVEL_2'][:5]:  # Top 5
                print(f"\n  * {alert['full_name']}")
                if alert.get('building_phrases'):
                    print(f"   Phrases: {', '.join(alert['building_phrases'][:2])}")
                print(f"   Previous: {alert.get('departure_info', {}).get('company', 'Unknown')}")
                print(f"   Founder Score: {alert['founder_score']:.1f} | Stealth Score: {alert['stealth_score']:.0f}")
                print(f"   Action: HIGH PRIORITY - Likely founding startup")
        
        # Level 1 Alerts (MONITORING)
        if results['LEVEL_1']:
            print(f"\n[LEVEL 1] RECENTLY LEFT ({len(results['LEVEL_1'])})")
            print("-"*60)
            for alert in results['LEVEL_1'][:3]:  # Top 3
                print(f"\n  * {alert['full_name']}")
                print(f"   Left: {alert.get('departure_info', {}).get('company', 'Unknown')} ({alert.get('departure_info', {}).get('days_ago', 'Unknown')} days ago)")
                print(f"   Founder Score: {alert['founder_score']:.1f}")
                print(f"   Action: MONITOR - Track for status changes")
    
    def save_results(self, results: dict):
        """
        Save alert results to files
        
        Args:
            results: Alert results to save
        """
        # Create output directory
        output_dir = os.path.join('data', 'alerts')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save full results
        full_path = os.path.join(output_dir, f'alerts_full_{timestamp}.json')
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save high priority alerts only (Level 2 and 3)
        high_priority = {
            'LEVEL_3': results['LEVEL_3'],
            'LEVEL_2': results['LEVEL_2'],
            'stats': results['stats'],
            'timestamp': results['timestamp']
        }
        
        priority_path = os.path.join(output_dir, f'alerts_high_priority_{timestamp}.json')
        with open(priority_path, 'w', encoding='utf-8') as f:
            json.dump(high_priority, f, indent=2, ensure_ascii=False)
        
        # Create CSV for easy viewing
        csv_path = os.path.join(output_dir, f'alerts_summary_{timestamp}.csv')
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('Level,Name,Previous Company,Current Company,Building Phrases,Founder Score,Stealth Score,Priority\n')
            
            for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
                for alert in results[level]:
                    if alert is None:
                        continue
                    name = alert.get('full_name', '')
                    prev = alert.get('departure_info', {}).get('company', '') if alert.get('departure_info') else ''
                    startup_info = alert.get('startup_info', {})
                    current = startup_info.get('startup_name', '') if startup_info else alert.get('job_company_name', '')
                    phrases = '|'.join(alert.get('building_phrases', []))
                    founder_score = alert.get('founder_score', 0)
                    stealth_score = alert.get('stealth_score', 0)
                    priority = alert.get('priority_score', 0)
                    
                    f.write(f'{level},{name},{prev},{current},"{phrases}",{founder_score:.1f},{stealth_score:.0f},{priority:.1f}\n')
        
        print(f"\n[SAVED] RESULTS")
        print(f"  • Full results: {full_path}")
        print(f"  • High priority: {priority_path}")
        print(f"  • Summary CSV: {csv_path}")
        
        return full_path
    
    def run(self, days_back: int = 30, max_credits: int = 10, 
            use_cache: bool = False, cache_file: str = None):
        """
        Run the complete alert pipeline
        
        Args:
            days_back: How many days back to search for departures
            max_credits: Maximum API credits to use
            use_cache: Whether to use cached data instead of API
            cache_file: Path to cached employee data
        """
        print("\n" + "="*80)
        print("[RUNNING] THREE-LEVEL ALERT PIPELINE")
        print("="*80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Days back: {days_back}")
        print(f"Max credits: {max_credits}")
        print(f"Use cache: {use_cache}")
        
        # Step 1: Fetch or load employees
        if use_cache and cache_file and os.path.exists(cache_file):
            print(f"\n[LOADING] Cached data from: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                employees = []
                for line in f:
                    if line.strip():
                        employees.append(json.loads(line))
            print(f"[OK] Loaded {len(employees)} employees from cache")
        else:
            employees = self.fetch_recent_departures(days_back, max_credits)
            
            # Save raw data for future use
            if employees:
                cache_dir = os.path.join('data', 'raw', 'alert_cache')
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl')
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    for emp in employees:
                        f.write(json.dumps(emp) + '\n')
                
                print(f"[SAVED] Cached raw data to: {cache_file}")
        
        if not employees:
            print("[ERROR] No employees to process")
            return None
        
        # Step 2: Process and generate alerts
        results = self.process_and_generate_alerts(employees)
        
        # Step 3: Display alerts
        self.display_alerts(results)
        
        # Step 4: Save results
        output_path = self.save_results(results)
        
        # Step 5: Show final statistics
        print(f"\n[STATS] PIPELINE STATISTICS")
        print("="*60)
        print(f"API Credits Used: {self.stats['api_credits_used']}")
        print(f"Employees Fetched: {self.stats['employees_fetched']}")
        print(f"Total Alerts Generated: {sum(self.stats['alerts_generated'].values())}")
        print(f"  • Level 3 (Immediate): {self.stats['alerts_generated']['LEVEL_3']}")
        print(f"  • Level 2 (High Priority): {self.stats['alerts_generated']['LEVEL_2']}")
        print(f"  • Level 1 (Monitoring): {self.stats['alerts_generated']['LEVEL_1']}")
        
        print("\n[SUCCESS] ALERT PIPELINE COMPLETED SUCCESSFULLY!")
        
        return results


def main():
    """Main function to run the alert pipeline"""
    
    # Initialize pipeline
    pipeline = AlertPipeline()
    
    # Configuration
    DAYS_BACK = 90  # Look for departures in last 90 days
    MAX_CREDITS = 20  # Use up to 20 API credits
    USE_CACHE = True  # Set to True to use cached data
    
    # Optional: Specify cache file if you have one
    CACHE_FILE = 'data/raw/updated_test/openai_high_potential_10credits_raw.jsonl'  # Your existing cache
    
    # Run the pipeline
    results = pipeline.run(
        days_back=DAYS_BACK,
        max_credits=MAX_CREDITS,
        use_cache=USE_CACHE,
        cache_file=CACHE_FILE
    )
    
    # Optional: Send notifications for high priority alerts
    if results:
        high_priority_count = len(results['LEVEL_3']) + len(results['LEVEL_2'])
        if high_priority_count > 0:
            print(f"\n[ALERT] {high_priority_count} HIGH PRIORITY ALERTS require immediate attention!")
            
            # Here you could integrate with email, Slack, etc.
            # Example:
            # send_slack_notification(results['LEVEL_3'], results['LEVEL_2'])
            # send_email_alerts(results['LEVEL_3'], results['LEVEL_2'])


if __name__ == "__main__":
    main()