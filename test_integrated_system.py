"""
Test Script for Integrated Founder Search System
Uses company and role configurations for targeted monitoring
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from src.monitoring.integrated_founder_search import IntegratedFounderSearch
from src.monitoring.stealth_detector import StealthFounderDetector
from src.monitoring.employment_monitor import EmploymentMonitor
from config.companies import AI_FOCUSED_BIG_TECH, ONLY_AI_TECH
from config.job_roles import AI_ML_ROLES, AI_ML_SUBROLES

def test_integrated_search(use_api: bool = False, limit: int = 10):
    """
    Test the integrated search system
    
    Args:
        use_api: If True, uses real API calls (costs credits)
        limit: Number of results per query
    """
    
    print("=" * 70)
    print("INTEGRATED AI FOUNDER DETECTION SYSTEM TEST")
    print("=" * 70)
    print(f"Mode: {'LIVE API' if use_api else 'MOCK DATA'}")
    print(f"Target Companies: {', '.join(AI_FOCUSED_BIG_TECH[:5])}")
    print(f"Target Roles: {', '.join(AI_ML_ROLES)}")
    print("=" * 70 + "\n")
    
    if use_api:
        # Initialize real system
        searcher = IntegratedFounderSearch()
        
        print("🔍 PHASE 1: Searching for AI Company Alumni")
        print("-" * 50)
        
        # Search with limited queries to save credits
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
        
        # Execute a focused search
        sql_query = f"""
            SELECT * FROM person
            WHERE (experience.company.name = 'openai' 
                   OR experience.company.name = 'google'
                   OR experience.company.name = 'meta')
            AND (job_title ILIKE '%founder%' 
                 OR job_company_name ILIKE '%stealth%'
                 OR job_company_size = '1-10')
            LIMIT {limit}
        """
        
        try:
            print(f"Executing search for AI company founders...")
            params = {'sql': sql_query, 'size': limit}
            response = searcher.client.person.search(**params).json()
            
            if response.get('status') == 200:
                employees = response.get('data', [])
                print(f"✅ Found {len(employees)} potential founders\n")
                
                for emp in employees:
                    # Calculate priority score
                    priority_score, breakdown = searcher.calculate_founder_priority_score(emp)
                    tier = searcher.determine_monitoring_tier(emp, priority_score, breakdown)
                    
                    emp_data = {
                        'name': emp.get('full_name'),
                        'company': emp.get('job_company_name'),
                        'title': emp.get('job_title'),
                        'score': priority_score,
                        'tier': tier,
                        'breakdown': breakdown
                    }
                    
                    results[tier].append(emp_data)
                    results['stats']['total_searched'] += 1
                    
                    # Print details for high-score individuals
                    if priority_score >= 50:
                        print(f"🎯 HIGH PRIORITY: {emp_data['name']}")
                        print(f"   Company: {emp_data['company']}")
                        print(f"   Title: {emp_data['title']}")
                        print(f"   Score: {priority_score:.1f}")
                        print(f"   Tier: {tier.upper()}")
                        
                        if breakdown.get('best_company'):
                            print(f"   Background: {breakdown['best_company'][0]}")
                        
                        print()
        
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")
        
        # Search for AI startups
        print("\n🔍 PHASE 2: Searching for AI Startups")
        print("-" * 50)
        
        startup_query = """
            SELECT * FROM company
            WHERE (name ILIKE '%AI%' OR name ILIKE '%.ai'
                   OR industry ILIKE '%artificial intelligence%')
            AND founded >= 2022
            AND size = '1-10'
            LIMIT 10
        """
        
        try:
            params = {'sql': startup_query, 'size': 10}
            response = searcher.client.company.search(**params).json()
            
            if response.get('status') == 200:
                companies = response.get('data', [])
                print(f"✅ Found {len(companies)} AI startups\n")
                
                for company in companies[:5]:
                    print(f"🏢 {company.get('name')}")
                    print(f"   Founded: {company.get('founded')}")
                    print(f"   Industry: {company.get('industry')}")
                    print(f"   Size: {company.get('size')}")
                    print()
        
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")
    
    else:
        # Use mock data for testing
        print("Using mock data for testing...\n")
        
        mock_employees = [
            {
                'id': 'test1',
                'full_name': 'Sarah Chen',
                'job_company_name': 'Stealth AI Startup',
                'job_title': 'Co-Founder & CTO',
                'job_company_size': '1-10',
                'job_title_role': 'engineering',
                'job_title_sub_role': 'data_science',
                'job_last_changed': '2024-01-15',
                'experience': [
                    {
                        'company': {'name': 'OpenAI'},
                        'end_date': '2024-01-01',
                        'is_primary': False
                    }
                ]
            },
            {
                'id': 'test2',
                'full_name': 'Michael Rodriguez',
                'job_company_name': 'Building Something Cool',
                'job_title': 'Founder',
                'job_company_size': '1-10',
                'job_title_role': 'research',
                'job_last_changed': '2024-02-01',
                'experience': [
                    {
                        'company': {'name': 'Google DeepMind'},
                        'end_date': '2024-01-20',
                        'is_primary': False
                    }
                ]
            },
            {
                'id': 'test3',
                'full_name': 'Emily Johnson',
                'job_company_name': 'Meta',
                'job_title': 'Senior ML Engineer',
                'job_company_size': '10001+',
                'job_title_role': 'engineering',
                'job_title_sub_role': 'machine_learning',
                'experience': [
                    {
                        'company': {'name': 'Meta'},
                        'is_primary': True
                    }
                ]
            }
        ]
        
        searcher = IntegratedFounderSearch()
        detector = StealthFounderDetector()
        
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
        
        print("🔍 ANALYZING MOCK EMPLOYEES")
        print("-" * 50 + "\n")
        
        for emp in mock_employees:
            # Calculate scores
            priority_score, breakdown = searcher.calculate_founder_priority_score(emp)
            stealth_score, signals, tier = detector.detect_stealth_signals(emp)
            tier = searcher.determine_monitoring_tier(emp, priority_score, breakdown)
            
            print(f"👤 {emp['full_name']}")
            print(f"   Current: {emp['job_title']} at {emp['job_company_name']}")
            print(f"   Priority Score: {priority_score:.1f}/100")
            print(f"   Stealth Score: {stealth_score}/100")
            print(f"   Monitoring Tier: {tier.upper()}")
            
            # Show breakdown
            print(f"   Score Breakdown:")
            print(f"      Company: {breakdown['company_score']:.1f} pts", end="")
            if breakdown.get('best_company'):
                print(f" (from {breakdown['best_company'][0]})")
            else:
                print()
            print(f"      Role: {breakdown['role_score']:.1f} pts ({breakdown.get('role_type', 'other')})")
            print(f"      Stealth: {breakdown['stealth_score']:.1f} pts")
            print(f"      Timing: {breakdown['timing_score']:.1f} pts")
            
            if signals:
                print(f"   Signals Detected:")
                for signal in signals[:3]:
                    print(f"      - {signal}")
            
            # Categorize
            results[tier].append({
                'name': emp['full_name'],
                'score': priority_score,
                'company': emp['job_company_name']
            })
            results['stats']['total_searched'] += 1
            
            if priority_score >= 50:
                print(f"   🎯 HIGH PRIORITY TARGET!")
            
            print()
    
    # Print summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\n📊 Statistics:")
    print(f"   Total Analyzed: {results['stats']['total_searched']}")
    print(f"   VIP Tier: {len(results['vip'])} people")
    print(f"   Watch Tier: {len(results['watch'])} people")
    print(f"   General Tier: {len(results['general'])} people")
    
    print(f"\n🎯 Monitoring Distribution:")
    for tier_name, tier_list in [('VIP', results['vip']), ('Watch', results['watch']), ('General', results['general'])]:
        if tier_list:
            print(f"\n   {tier_name} Tier ({['Daily', 'Weekly', 'Monthly'][['VIP', 'Watch', 'General'].index(tier_name)]} monitoring):")
            for person in tier_list[:3]:
                print(f"      - {person['name']} (Score: {person['score']:.1f})")
    
    # Cost estimates
    daily_cost = (
        len(results['vip']) * 0.01 +           # Daily checks
        len(results['watch']) * 0.01 / 7 +     # Weekly checks
        len(results['general']) * 0.01 / 30    # Monthly checks
    )
    
    print(f"\n💰 Cost Estimates:")
    print(f"   Daily monitoring cost: ${daily_cost:.2f}")
    print(f"   Monthly cost: ${daily_cost * 30:.2f}")
    print(f"   Annual cost: ${daily_cost * 365:.2f}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'data/monitoring/integrated_test_{timestamp}.json'
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Test complete!")
    
    return results

def main():
    """Main test execution"""
    
    load_dotenv()
    
    print("\nIntegrated Founder Search System Test")
    print("=====================================")
    print("\nThis system searches for:")
    print("1. Employees from AI companies (OpenAI, Google, Meta, etc.)")
    print("2. With AI/ML roles (Research, Data Science, ML Engineering)")
    print("3. Who show founder signals (stealth companies, 'building', etc.)")
    print("\nSelect test mode:")
    print("1. Mock Data Test (No API credits)")
    print("2. Live API Test (Uses ~20 credits)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        test_integrated_search(use_api=False)
    elif choice == '2':
        if not os.getenv('API_KEY'):
            print("\n❌ No API_KEY found in .env file!")
            print("Please add: API_KEY=your_pdl_api_key")
            return
        
        confirm = input("\n⚠️ This will use ~20 API credits. Continue? (y/n): ")
        if confirm.lower() == 'y':
            test_integrated_search(use_api=True, limit=10)
        else:
            print("Test cancelled.")
    else:
        print("Exiting...")

if __name__ == "__main__":
    main()