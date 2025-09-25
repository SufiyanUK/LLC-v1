"""
Simple Test Script for Monitoring System
Uses PDL SQL queries for testing
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

from src.data_collection.pdl_client import get_pdl_client
from src.monitoring.stealth_detector import StealthFounderDetector
from src.monitoring.employment_monitor import EmploymentMonitor

def test_with_sql_queries():
    """
    Test using SQL queries which PDL supports
    """
    
    print("=" * 60)
    print("MONITORING SYSTEM TEST - SQL QUERIES")
    print("=" * 60)
    print("Budget: 20 Person API calls + 20 Company API calls")
    print("=" * 60 + "\n")
    
    # Initialize components
    load_dotenv()
    if not os.getenv('API_KEY'):
        print("❌ No API_KEY found in .env file!")
        print("Please add: API_KEY=your_pdl_api_key")
        return
    
    client = get_pdl_client()
    stealth_detector = StealthFounderDetector()
    employment_monitor = EmploymentMonitor()
    
    # Track results
    results = {
        'employees_found': 0,
        'companies_found': 0,
        'stealth_signals': [],
        'vip_tier': [],
        'watch_tier': [],
        'general_tier': []
    }
    
    # ============================================
    # TEST 1: Person Search with SQL
    # ============================================
    print("TEST 1: Searching for potential stealth founders")
    print("-" * 40)
    
    # SQL query for people who might be founders
    person_sql_queries = [
        {
            'name': 'Founders and Co-founders',
            'sql': """
                SELECT * FROM person 
                WHERE job_title ILIKE '%founder%' 
                OR job_title ILIKE '%co-founder%'
                OR job_company_name ILIKE '%stealth%'
                LIMIT 10
            """
        },
        {
            'name': 'Building Something',
            'sql': """
                SELECT * FROM person
                WHERE job_title ILIKE '%building%'
                OR job_title ILIKE '%working on%'
                OR job_company_size = '1-10'
                LIMIT 10
            """
        }
    ]
    
    for query_info in person_sql_queries:
        print(f"\n🔍 {query_info['name']}")
        
        try:
            params = {
                'sql': query_info['sql'],
                'size': 10
            }
            
            response = client.person.search(**params).json()
            
            if response.get('status') == 200:
                employees = response.get('data', [])
                results['employees_found'] += len(employees)
                print(f"   ✅ Found {len(employees)} people")
                
                # Analyze each employee
                for emp in employees[:5]:
                    # Detect stealth signals
                    score, signals, tier = stealth_detector.detect_stealth_signals(emp)
                    
                    if score > 0:
                        print(f"\n   👤 {emp.get('full_name', 'Unknown')}")
                        print(f"      Company: {emp.get('job_company_name', 'None')}")
                        print(f"      Title: {emp.get('job_title', 'None')}")
                        print(f"      Score: {score}/100")
                        print(f"      Tier: {tier}")
                        
                        # Track by tier
                        if tier == 'vip':
                            results['vip_tier'].append(emp.get('full_name'))
                        elif tier == 'watch':
                            results['watch_tier'].append(emp.get('full_name'))
                        else:
                            results['general_tier'].append(emp.get('full_name'))
                        
                        if score >= 50:
                            results['stealth_signals'].append({
                                'name': emp.get('full_name'),
                                'score': score,
                                'signals': signals[:2]
                            })
                            print(f"      🚀 HIGH STEALTH PROBABILITY!")
                        
                        # Save to monitoring database
                        employment_monitor.save_snapshot(emp)
                        employment_monitor.update_monitoring_schedule(emp, tier, score, signals)
            else:
                print(f"   ❌ Error: {response.get('error', {}).get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:100]}")
    
    # ============================================
    # TEST 2: Company Search with SQL
    # ============================================
    print("\n" + "=" * 60)
    print("TEST 2: Searching for stealth startups")
    print("-" * 40)
    
    company_sql_queries = [
        {
            'name': 'Stealth Companies',
            'sql': """
                SELECT * FROM company
                WHERE name ILIKE '%stealth%'
                AND size = '1-10'
                LIMIT 10
            """
        },
        {
            'name': 'Recent Small Startups',
            'sql': """
                SELECT * FROM company
                WHERE founded >= 2022
                AND employee_count <= 10
                AND industry = 'computer software'
                LIMIT 10
            """
        }
    ]
    
    for query_info in company_sql_queries:
        print(f"\n🔍 {query_info['name']}")
        
        try:
            params = {
                'sql': query_info['sql'],
                'size': 10
            }
            
            response = client.company.search(**params).json()
            
            if response.get('status') == 200:
                companies = response.get('data', [])
                results['companies_found'] += len(companies)
                print(f"   ✅ Found {len(companies)} companies")
                
                for company in companies[:5]:
                    print(f"\n   🏢 {company.get('name', 'Unknown')}")
                    print(f"      Founded: {company.get('founded', 'N/A')}")
                    print(f"      Size: {company.get('size', 'N/A')}")
                    print(f"      Industry: {company.get('industry', 'N/A')}")
                    
                    # Check for stealth indicators
                    company_name = (company.get('name', '') or '').lower()
                    if 'stealth' in company_name or company.get('size') == '1-10':
                        print(f"      🚀 POTENTIAL STEALTH STARTUP!")
            else:
                print(f"   ❌ Error: {response.get('error', {}).get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:100]}")
    
    # ============================================
    # RESULTS SUMMARY
    # ============================================
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 Data Collected:")
    print(f"   Employees Found: {results['employees_found']}")
    print(f"   Companies Found: {results['companies_found']}")
    print(f"   Stealth Signals Detected: {len(results['stealth_signals'])}")
    
    print(f"\n📈 Monitoring Tiers:")
    print(f"   VIP (Daily): {len(results['vip_tier'])} people")
    print(f"   Watch (Weekly): {len(results['watch_tier'])} people")
    print(f"   General (Monthly): {len(results['general_tier'])} people")
    
    if results['stealth_signals']:
        print(f"\n🚀 Top Stealth Signals:")
        for signal in results['stealth_signals'][:3]:
            print(f"   {signal['name']} (Score: {signal['score']})")
            if signal['signals']:
                print(f"      - {signal['signals'][0]}")
    
    # Get monitoring stats
    stats = employment_monitor.get_monitoring_stats()
    print(f"\n💰 Cost Estimate:")
    print(f"   Daily monitoring cost: ${stats['estimated_daily_cost']:.2f}")
    print(f"   Monthly cost: ${stats['estimated_daily_cost'] * 30:.2f}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'data/monitoring/test_simple_{timestamp}.json'
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ TEST COMPLETE!")
    
    return results

def test_without_api():
    """
    Test with mock data (no API calls)
    """
    print("\n" + "=" * 60)
    print("MOCK TEST - NO API CALLS")
    print("=" * 60 + "\n")
    
    detector = StealthFounderDetector()
    monitor = EmploymentMonitor()
    
    # Mock data
    test_people = [
        {
            'id': 'test1',
            'full_name': 'John Stealth',
            'job_company_name': 'Stealth Startup',
            'job_title': 'Founder & CEO',
            'job_company_size': '1-10'
        },
        {
            'id': 'test2',
            'full_name': 'Jane Builder',
            'job_company_name': 'Building Something Cool Inc',
            'job_title': 'Working on something new',
            'job_company_size': '1-10'
        },
        {
            'id': 'test3',
            'full_name': 'Bob Regular',
            'job_company_name': 'Microsoft',
            'job_title': 'Software Engineer',
            'job_company_size': '10001+'
        }
    ]
    
    print("Testing stealth detection:\n")
    
    for person in test_people:
        score, signals, tier = detector.detect_stealth_signals(person)
        
        print(f"👤 {person['full_name']}")
        print(f"   Company: {person['job_company_name']}")
        print(f"   Title: {person['job_title']}")
        print(f"   Stealth Score: {score}/100")
        print(f"   Tier: {tier}")
        
        if signals:
            print(f"   Signals:")
            for signal in signals:
                print(f"      - {signal}")
        
        if score >= 50:
            print(f"   🚀 HIGH STEALTH PROBABILITY!")
        
        print()
    
    print("=" * 60)
    print("Mock test complete!")

def main():
    """Main execution"""
    
    print("\nSelect test mode:")
    print("1. Mock Test (No API credits)")
    print("2. Simple SQL Test (Uses ~20 API credits)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        test_without_api()
    elif choice == '2':
        load_dotenv()
        if not os.getenv('API_KEY'):
            print("\n❌ No API_KEY found in .env file!")
            print("Please create .env file with:")
            print("API_KEY=your_pdl_api_key_here")
            return
        
        confirm = input("\n⚠️ This will use ~20 API credits. Continue? (y/n): ")
        if confirm.lower() == 'y':
            test_with_sql_queries()
        else:
            print("Test cancelled.")
    else:
        print("Exiting...")

if __name__ == "__main__":
    main()