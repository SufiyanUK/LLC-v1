"""
FULL AI FOUNDER DETECTION PIPELINE
This script runs the complete pipeline from data collection to monitoring setup
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

# Import all necessary modules
from src.data_collection.pdl_client import get_pdl_client
from src.data_collection.company_search import fetch_state_wise_data
from src.data_collection.employee_search import get_employees_by_company
from src.data_processing.company_qualifier import process_potential_tech_startups
from src.data_processing.employee_processor import process_all_employees
from src.data_processing.founder_qualifier import process_potential_founders
from src.matching.employment_matcher import EmploymentMatcher, save_matches_to_jsonl
from src.monitoring.integrated_founder_search import IntegratedFounderSearch
from src.monitoring.employment_monitor import EmploymentMonitor
from src.monitoring.alert_system import AlertSystem

# Import configurations
from config.companies import AI_FOCUSED_BIG_TECH, ONLY_AI_TECH, TRADITIONAL_BIG_TECH
from config.job_roles import AI_ML_ROLES

class FounderDetectionPipeline:
    """
    Complete pipeline for AI founder detection
    """
    
    def __init__(self, config=None):
        """Initialize pipeline with configuration"""
        load_dotenv()
        
        # Check API key
        if not os.getenv('API_KEY'):
            raise ValueError("No API_KEY found in .env file! Please add: API_KEY=your_pdl_api_key")
        
        self.client = get_pdl_client()
        
        # Default configuration
        self.config = config or {
            # API Limits
            'max_companies_per_state': 500,
            'max_employees_per_company': 500,
            'api_batch_size': 100,
            
            # Target states
            'states': ['california', 'new york', 'texas', 'washington', 'delaware'],
            
            # Target companies (choose which groups to search)
            'search_ai_focused': True,      # Google, Meta, Microsoft, etc.
            'search_only_ai': True,          # OpenAI, Anthropic, DeepMind
            'search_traditional': False,     # Oracle, IBM, Adobe (set True if needed)
            
            # Scoring thresholds
            'min_startup_score': 3.0,
            'min_founder_score': 4.0,
            'min_match_confidence': 50.0,
            
            # Monitoring
            'enable_monitoring': True,
            'enable_alerts': True
        }
        
        self.stats = {
            'companies_collected': 0,
            'employees_collected': 0,
            'qualified_startups': 0,
            'potential_founders': 0,
            'matches_found': 0,
            'api_calls_made': 0,
            'estimated_cost': 0.0
        }
    
    def run_full_pipeline(self, mode='full'):
        """
        Run the complete pipeline
        
        Modes:
        - 'full': Run everything (expensive, ~$10-50 in API costs)
        - 'test': Limited test run (~$1 in API costs)
        - 'process_only': Skip data collection, just process existing data (free)
        """
        
        print("="*70)
        print("🚀 AI FOUNDER DETECTION PIPELINE")
        print("="*70)
        print(f"Mode: {mode.upper()}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*70 + "\n")
        
        # Step 1: Data Collection
        if mode in ['full', 'test']:
            self.collect_data(mode)
        elif mode == 'process_only':
            print("📊 Skipping data collection - using existing data")
        
        # Step 2: Data Processing
        print("\n" + "="*70)
        print("📊 PHASE 2: DATA PROCESSING")
        print("="*70)
        
        self.process_data()
        
        # Step 3: Matching
        print("\n" + "="*70)
        print("🔗 PHASE 3: FOUNDER-STARTUP MATCHING")
        print("="*70)
        
        self.run_matching()
        
        # Step 4: Monitoring Setup
        if self.config['enable_monitoring']:
            print("\n" + "="*70)
            print("📡 PHASE 4: MONITORING SETUP")
            print("="*70)
            
            self.setup_monitoring()
        
        # Step 5: Summary
        self.print_summary()
        
        return self.stats
    
    def collect_data(self, mode):
        """Collect company and employee data"""
        
        print("\n" + "="*70)
        print("📥 PHASE 1: DATA COLLECTION")
        print("="*70)
        
        # Determine limits based on mode
        if mode == 'test':
            company_limit = 10  # per state
            employee_limit = 10  # per company
            states_to_search = ['california']  # Just one state for testing
            companies_to_search = ['openai', 'google', 'meta']  # Just 3 companies
        else:
            company_limit = self.config['max_companies_per_state']
            employee_limit = self.config['max_employees_per_company']
            states_to_search = self.config['states']
            companies_to_search = self.get_target_companies()
        
        # Step 1A: Collect Companies by State
        print(f"\n📍 Collecting startups from {len(states_to_search)} states...")
        print(f"   States: {', '.join(states_to_search)}")
        print(f"   Max per state: {company_limit}")
        
        if input("\nProceed with company collection? (y/n): ").lower() == 'y':
            for state in states_to_search:
                print(f"\n   Fetching {state}...")
                try:
                    fetch_state_wise_data(
                        [state], 
                        max_number=company_limit, 
                        page_size=min(100, company_limit),
                        pause=0.5
                    )
                    self.stats['companies_collected'] += company_limit
                    self.stats['api_calls_made'] += (company_limit // 100) + 1
                except Exception as e:
                    print(f"   ❌ Error fetching {state}: {e}")
        
        # Step 1B: Collect Employees from Target Companies
        print(f"\n👥 Collecting employees from {len(companies_to_search)} companies...")
        print(f"   Companies: {', '.join(companies_to_search[:5])}{'...' if len(companies_to_search) > 5 else ''}")
        print(f"   Max per company: {employee_limit}")
        
        if input("\nProceed with employee collection? (y/n): ").lower() == 'y':
            try:
                all_employees = get_employees_by_company(
                    companies_to_search, 
                    per_company_limit=employee_limit
                )
                self.stats['employees_collected'] = len(all_employees)
                self.stats['api_calls_made'] += len(companies_to_search) * ((employee_limit // 100) + 1)
                print(f"\n   ✅ Collected {len(all_employees)} total employees")
            except Exception as e:
                print(f"   ❌ Error collecting employees: {e}")
        
        # Estimate cost
        self.stats['estimated_cost'] = self.stats['api_calls_made'] * 0.01
        print(f"\n💰 Estimated API cost so far: ${self.stats['estimated_cost']:.2f}")
    
    def process_data(self):
        """Process collected data to identify qualified startups and founders"""
        
        # Process companies to find qualified startups
        print("\n🏢 Processing companies to identify tech startups...")
        try:
            qualified_startups = process_potential_tech_startups()
            self.stats['qualified_startups'] = len(qualified_startups)
            print(f"   ✅ Identified {len(qualified_startups)} qualified tech startups")
        except Exception as e:
            print(f"   ❌ Error processing companies: {e}")
            qualified_startups = []
        
        # Process employees
        print("\n👤 Processing employees...")
        try:
            # First process raw employee data
            print("   Step 1: Processing employment histories...")
            process_all_employees()
            
            # Then qualify potential founders
            print("   Step 2: Identifying potential founders...")
            potential_founders = process_potential_founders()
            self.stats['potential_founders'] = len(potential_founders)
            print(f"   ✅ Identified {len(potential_founders)} potential founders")
        except Exception as e:
            print(f"   ❌ Error processing employees: {e}")
            potential_founders = []
        
        return qualified_startups, potential_founders
    
    def run_matching(self):
        """Match potential founders with startups"""
        
        print("\n🔍 Matching founders with startups...")
        
        # Load processed data
        try:
            with open('data/processed/potential_founders.json', 'r') as f:
                founders = json.load(f)
            with open('data/processed/qualified_startups.json', 'r') as f:
                startups = json.load(f)
            
            if not founders or not startups:
                print("   ⚠️ No data to match")
                return
            
            # Run matching
            matcher = EmploymentMatcher(
                min_company_similarity=0.7,
                high_confidence_threshold=70,
                manual_review_threshold=50
            )
            
            matches = matcher.find_employment_matches(founders, startups)
            self.stats['matches_found'] = len(matches)
            
            # Save matches
            if matches:
                # All matches
                save_matches_to_jsonl(matches, 'data/results/employment_matches.jsonl')
                
                # High confidence matches
                high_conf = [m for m in matches if m.confidence_score >= 70]
                if high_conf:
                    save_matches_to_jsonl(high_conf, 'data/results/high_confidence_employment_matches.jsonl')
                    print(f"   🌟 Found {len(high_conf)} HIGH CONFIDENCE matches!")
                
                # Manual review matches
                manual = [m for m in matches if 50 <= m.confidence_score < 70]
                if manual:
                    save_matches_to_jsonl(manual, 'data/results/manual_review_employment_matches.jsonl')
                    print(f"   📋 Found {len(manual)} matches for manual review")
                
                print(f"   ✅ Total matches found: {len(matches)}")
            else:
                print("   ❌ No matches found")
                
        except FileNotFoundError as e:
            print(f"   ❌ Required files not found. Run data processing first.")
        except Exception as e:
            print(f"   ❌ Error during matching: {e}")
    
    def setup_monitoring(self):
        """Setup ongoing monitoring for high-value targets"""
        
        print("\n📡 Setting up monitoring...")
        
        try:
            # Initialize monitoring systems
            monitor = EmploymentMonitor()
            integrated_search = IntegratedFounderSearch()
            
            # Load potential founders
            with open('data/processed/potential_founders.json', 'r') as f:
                founders = json.load(f)
            
            # Get top targets for monitoring
            top_founders = sorted(founders, key=lambda x: x.get('founder_score', 0), reverse=True)[:100]
            
            print(f"   Setting up monitoring for top {len(top_founders)} targets")
            
            # Set up monitoring schedules
            for founder in top_founders:
                score = founder.get('founder_score', 0)
                
                # Determine tier
                if score >= 7:
                    tier = 'vip'
                elif score >= 5:
                    tier = 'watch'
                else:
                    tier = 'general'
                
                # Save to monitoring
                monitor.save_snapshot(founder)
                monitor.update_monitoring_schedule(
                    founder, 
                    tier, 
                    score, 
                    founder.get('qualification_reasons', [])
                )
            
            # Get monitoring stats
            stats = monitor.get_monitoring_stats()
            
            print(f"\n   📊 Monitoring Distribution:")
            print(f"      VIP (Daily): {stats['tier_distribution'].get('vip', 0)} people")
            print(f"      Watch (Weekly): {stats['tier_distribution'].get('watch', 0)} people")
            print(f"      General (Monthly): {stats['tier_distribution'].get('general', 0)} people")
            print(f"      Estimated daily cost: ${stats['estimated_daily_cost']:.2f}")
            
            if self.config['enable_alerts']:
                print(f"\n   🔔 Alert system enabled")
                print(f"      Email alerts: {os.getenv('ALERT_EMAIL_TO', 'Not configured')}")
                print(f"      Webhook: {'Configured' if os.getenv('WEBHOOK_URL') else 'Not configured'}")
                
        except Exception as e:
            print(f"   ❌ Error setting up monitoring: {e}")
    
    def get_target_companies(self):
        """Get list of target companies based on configuration"""
        companies = []
        
        if self.config['search_ai_focused']:
            companies.extend(AI_FOCUSED_BIG_TECH)
        
        if self.config['search_only_ai']:
            companies.extend(ONLY_AI_TECH)
        
        if self.config['search_traditional']:
            companies.extend(TRADITIONAL_BIG_TECH)
        
        # Remove duplicates
        return list(set(companies))
    
    def print_summary(self):
        """Print final summary"""
        
        print("\n" + "="*70)
        print("📈 PIPELINE SUMMARY")
        print("="*70)
        
        print(f"\n📊 Data Collected:")
        print(f"   Companies searched: {self.stats['companies_collected']}")
        print(f"   Employees collected: {self.stats['employees_collected']}")
        print(f"   API calls made: {self.stats['api_calls_made']}")
        print(f"   Estimated cost: ${self.stats['estimated_cost']:.2f}")
        
        print(f"\n✅ Results:")
        print(f"   Qualified startups: {self.stats['qualified_startups']}")
        print(f"   Potential founders: {self.stats['potential_founders']}")
        print(f"   Matches found: {self.stats['matches_found']}")
        
        print(f"\n📁 Output Files:")
        print(f"   Raw data: data/raw/")
        print(f"   Processed: data/processed/")
        print(f"   Results: data/results/")
        print(f"   Monitoring DB: data/monitoring/employment_history.db")
        
        # Save summary to file
        summary_file = f"pipeline_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'config': self.config
            }, f, indent=2)
        
        print(f"\n💾 Summary saved to: {summary_file}")
        print("="*70)

def main():
    """Main execution function"""
    
    print("\n" + "="*70)
    print("🚀 AI FOUNDER DETECTION SYSTEM")
    print("="*70)
    print("\nThis pipeline will:")
    print("1. Collect company data from 5 states")
    print("2. Collect employee data from AI/ML companies")
    print("3. Identify qualified tech startups")
    print("4. Identify potential founders")
    print("5. Match founders with startups")
    print("6. Set up ongoing monitoring")
    print("="*70)
    
    print("\nSelect mode:")
    print("1. TEST MODE - Limited data (~$1 in API costs)")
    print("2. FULL MODE - Complete pipeline (~$10-50 in API costs)")
    print("3. PROCESS ONLY - Process existing data (FREE)")
    print("4. EXIT")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        mode = 'test'
    elif choice == '2':
        mode = 'full'
        print("\n⚠️ WARNING: This will use significant API credits!")
        if input("Are you sure? (y/n): ").lower() != 'y':
            print("Cancelled.")
            return
    elif choice == '3':
        mode = 'process_only'
    else:
        print("Exiting...")
        return
    
    # Initialize and run pipeline
    pipeline = FounderDetectionPipeline()
    
    try:
        stats = pipeline.run_full_pipeline(mode=mode)
        print("\n✅ Pipeline completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()