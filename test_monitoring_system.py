"""
Test Script for Monitoring System
Uses limited API credits (50 person, 50 company) for testing
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
from src.monitoring.alert_system import AlertSystem

def test_with_limited_credits():
    """
    Test the monitoring system with limited API credits
    50 person searches + 50 company searches
    """
    
    print("=" * 60)
    print("MONITORING SYSTEM TEST - LIMITED CREDITS")
    print("=" * 60)
    print("Budget: 50 Person API calls + 50 Company API calls")
    print("=" * 60 + "\n")
    
    # Initialize components
    load_dotenv()
    client = get_pdl_client()
    stealth_detector = StealthFounderDetector()
    employment_monitor = EmploymentMonitor()
    alert_system = AlertSystem()
    
    # Track API usage
    api_usage = {
        'person_calls': 0,
        'company_calls': 0,
        'person_limit': 10,
        'company_limit': 10
    }
    
    results = {
        'employees_fetched': [],
        'companies_fetched': [],
        'stealth_signals_found': [],
        'monitoring_tiers': {'vip': [], 'watch': [], 'general': []},
        'alerts_generated': []
    }
    
    # ============================================
    # PHASE 1: Test Person Search (30 credits)
    # ============================================
    print("PHASE 1: Testing Person Search API")
    print("-" * 40)
    
    # Search for recent departures from key companies using PDL structured queries
    test_queries = [
        {
            'name': 'Recent OpenAI Departures',
            'query': {
                'bool': {
                    'must': [
                        {'term': {'experience.company.name': 'openai'}},
                        {'range': {'job_last_changed': {'gte': '2023-01-01'}}}
                    ]
                }
            },
            'limit': 10
        },
        {
            'name': 'Google/Meta Founders',
            'query': {
                'bool': {
                    'must': [
                        {
                            'bool': {
                                'should': [
                                    {'term': {'experience.company.name': 'google'}},
                                    {'term': {'experience.company.name': 'meta'}}
                                ]
                            }
                        },
                        {
                            'bool': {
                                'should': [
                                    {'term': {'job_title': 'founder'}},
                                    {'term': {'job_title': 'co-founder'}},
                                    {'term': {'job_company_name': 'stealth'}}
                                ]
                            }
                        }
                    ]
                }
            },
            'limit': 10
        },
        {
            'name': 'Building Something Signals',
            'query': {
                'bool': {
                    'must': [
                        {
                            'bool': {
                                'should': [
                                    {'term': {'experience.company.name': 'microsoft'}},
                                    {'term': {'experience.company.name': 'apple'}}
                                ]
                            }
                        },
                        {
                            'bool': {
                                'should': [
                                    {'match': {'job_title': 'building'}},
                                    {'match': {'job_title': 'working on'}},
                                    {'term': {'job_company_size': '1-10'}}
                                ]
                            }
                        }
                    ]
                }
            },
            'limit': 10
        }
    ]
    
    for test in test_queries:
        if api_usage['person_calls'] >= api_usage['person_limit']:
            print(f"⚠️ Reached person API limit ({api_usage['person_limit']} calls)")
            break
        
        print(f"\n🔍 Test: {test['name']}")
        print(f"   Query: Structured query for {test['name']}")
        
        try:
            params = {
                'query': test['query'],
                'size': min(test['limit'], api_usage['person_limit'] - api_usage['person_calls']),
                'pretty': True
            }
            
            response = client.person.search(**params).json()
            api_usage['person_calls'] += 1
            
            if response.get('status') == 200:
                employees = response.get('data', [])
                print(f"   ✅ Found {len(employees)} employees")
                
                # Analyze each employee
                for emp in employees[:5]:  # Analyze first 5
                    # Detect stealth signals
                    score, signals, tier = stealth_detector.detect_stealth_signals(emp)
                    
                    emp_summary = {
                        'name': emp.get('full_name', 'Unknown'),
                        'company': emp.get('job_company_name', 'None'),
                        'title': emp.get('job_title', 'None'),
                        'stealth_score': score,
                        'tier': tier,
                        'signals': signals[:3] if signals else []
                    }
                    
                    results['employees_fetched'].append(emp_summary)
                    results['monitoring_tiers'][tier].append(emp_summary['name'])
                    
                    if score >= 50:
                        results['stealth_signals_found'].append(emp_summary)
                        print(f"   🚀 STEALTH SIGNAL: {emp_summary['name']} (Score: {score})")
                        
                        # Generate test alert
                        if 'stealth' in emp.get('job_company_name', '').lower():
                            alert = {
                                'type': 'stealth_company',
                                'data': {
                                    'name': emp_summary['name'],
                                    'new_company': emp_summary['company'],
                                    'confidence': score/100,
                                    'signals': signals
                                }
                            }
                            results['alerts_generated'].append(alert)
                    
                    # Save to monitoring database
                    employment_monitor.save_snapshot(emp)
                    employment_monitor.update_monitoring_schedule(emp, tier, score, signals)
                    
            else:
                print(f"   ❌ API Error: {response.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
    
    print(f"\n📊 Person API Usage: {api_usage['person_calls']}/{api_usage['person_limit']}")
    
    # ============================================
    # PHASE 2: Test Company Search (20 credits)
    # ============================================
    print("\n" + "=" * 60)
    print("PHASE 2: Testing Company Search API")
    print("-" * 40)
    
    test_company_queries = [
        {
            'name': 'Recent SF Startups',
            'query': {
                'bool': {
                    'must': [
                        {'range': {'founded': {'gte': 2023}}},
                        {'term': {'location.locality': 'san francisco'}},
                        {'term': {'size': '1-10'}}
                    ]
                }
            },
            'limit': 10
        },
        {
            'name': 'Stealth Companies',
            'query': {
                'bool': {
                    'must': [
                        {'term': {'size': '1-10'}},
                        {'range': {'founded': {'gte': 2022}}},
                        {
                            'bool': {
                                'should': [
                                    {'match': {'name': 'stealth'}},
                                    {'term': {'industry': 'computer software'}}
                                ]
                            }
                        }
                    ]
                }
            },
            'limit': 10
        }
    ]
    
    for test in test_company_queries:
        if api_usage['company_calls'] >= api_usage['company_limit']:
            print(f"⚠️ Reached company API limit ({api_usage['company_limit']} calls)")
            break
        
        print(f"\n🔍 Test: {test['name']}")
        print(f"   Query: Structured query for {test['name']}")
        
        try:
            params = {
                'query': test['query'],
                'size': min(test['limit'], api_usage['company_limit'] - api_usage['company_calls']),
                'pretty': True
            }
            
            response = client.company.search(**params).json()
            api_usage['company_calls'] += 1
            
            if response.get('status') == 200:
                companies = response.get('data', [])
                print(f"   ✅ Found {len(companies)} companies")
                
                for company in companies[:5]:
                    # Safe location extraction with proper None handling
                    location_data = company.get('location')
                    locality = None
                    if location_data and isinstance(location_data, dict):
                        locality = location_data.get('locality')
                    
                    company_summary = {
                        'name': company.get('name', 'Unknown'),
                        'founded': company.get('founded'),
                        'size': company.get('size'),
                        'industry': company.get('industry'),
                        'location': locality
                    }
                    results['companies_fetched'].append(company_summary)
                    
                    # Check for stealth indicators
                    if 'stealth' in company.get('name', '').lower():
                        print(f"   🚀 STEALTH COMPANY: {company_summary['name']}")
            else:
                print(f"   ❌ API Error: {response.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
    
    print(f"\n📊 Company API Usage: {api_usage['company_calls']}/{api_usage['company_limit']}")
    
    # ============================================
    # PHASE 3: Test Monitoring & Alerts
    # ============================================
    print("\n" + "=" * 60)
    print("PHASE 3: Testing Monitoring System")
    print("-" * 40)
    
    # Get monitoring stats
    stats = employment_monitor.get_monitoring_stats()
    
    print(f"\n📈 Monitoring Distribution:")
    print(f"   VIP Tier (Daily): {stats['tier_distribution'].get('vip', 0)} people")
    print(f"   Watch Tier (Weekly): {stats['tier_distribution'].get('watch', 0)} people")
    print(f"   General Tier (Monthly): {stats['tier_distribution'].get('general', 0)} people")
    print(f"   Estimated Daily Cost: ${stats['estimated_daily_cost']:.2f}")
    
    # Test alert system (without actually sending)
    if results['alerts_generated']:
        print(f"\n🔔 Testing Alert System:")
        print(f"   Generated {len(results['alerts_generated'])} alerts")
        
        for alert in results['alerts_generated'][:3]:
            print(f"   - {alert['type']}: {alert['data']['name']}")
        
        # Test alert formatting (don't actually send)
        test_alert = results['alerts_generated'][0]
        print(f"\n   Sample Alert Content:")
        print(f"   Type: {test_alert['type']}")
        print(f"   Person: {test_alert['data']['name']}")
        print(f"   Details: {test_alert['data'].get('new_company', 'N/A')}")
    
    # ============================================
    # PHASE 4: Generate Test Report
    # ============================================
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"\n✅ API Usage Summary:")
    print(f"   Person API: {api_usage['person_calls']}/{api_usage['person_limit']} credits used")
    print(f"   Company API: {api_usage['company_calls']}/{api_usage['company_limit']} credits used")
    print(f"   Total Cost: ${(api_usage['person_calls'] + api_usage['company_calls']) * 0.01:.2f}")
    
    print(f"\n📊 Data Collected:")
    print(f"   Employees Analyzed: {len(results['employees_fetched'])}")
    print(f"   Companies Found: {len(results['companies_fetched'])}")
    print(f"   Stealth Signals: {len(results['stealth_signals_found'])}")
    
    if results['stealth_signals_found']:
        print(f"\n🚀 Top Stealth Signals Found:")
        for person in sorted(results['stealth_signals_found'], key=lambda x: x['stealth_score'], reverse=True)[:5]:
            print(f"   {person['name']} (Score: {person['stealth_score']})")
            print(f"      Company: {person['company']}")
            print(f"      Title: {person['title']}")
            if person['signals']:
                print(f"      Signal: {person['signals'][0]}")
    
    # Save test results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'data/monitoring/test_results_{timestamp}.json'
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {results_file}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    
    return results

def quick_test_stealth_detection():
    """
    Quick test without using API credits - uses mock data
    """
    print("\n" + "=" * 60)
    print("QUICK TEST - STEALTH DETECTION (No API Credits)")
    print("=" * 60 + "\n")
    
    # Mock employee data for testing
    test_employees = [
        {
            'id': 'test1',
            'full_name': 'John Doe',
            'job_company_name': 'Stealth Startup',
            'job_title': 'Founder',
            'job_company_size': '1-10',
            'job_last_changed': '2024-01-15',
            'experience': [
                {
                    'company': {'name': 'OpenAI'},
                    'end_date': '2024-01-01',
                    'is_primary': False
                },
                {
                    'company': {'name': 'Stealth Startup'},
                    'is_primary': True
                }
            ]
        },
        {
            'id': 'test2',
            'full_name': 'Jane Smith',
            'job_company_name': 'Building Something Cool Inc',
            'job_title': 'Working on something new',
            'job_company_size': '1-10',
            'job_last_changed': '2024-02-01'
        },
        {
            'id': 'test3',
            'full_name': 'Bob Johnson',
            'job_company_name': '',
            'job_title': '',
            'job_last_changed': '2024-01-20',
            'experience': [
                {
                    'company': {'name': 'Google'},
                    'end_date': '2024-01-20',
                    'is_primary': False
                }
            ]
        }
    ]
    
    detector = StealthFounderDetector()
    monitor = EmploymentMonitor()
    
    print("Testing stealth detection on mock data:\n")
    
    for emp in test_employees:
        score, signals, tier = detector.detect_stealth_signals(emp)
        
        print(f"👤 {emp['full_name']}")
        print(f"   Company: {emp.get('job_company_name', 'None')}")
        print(f"   Title: {emp.get('job_title', 'None')}")
        print(f"   Stealth Score: {score}/100")
        print(f"   Monitoring Tier: {tier.upper()}")
        
        if signals:
            print(f"   Signals Detected:")
            for signal in signals:
                print(f"      - {signal}")
        
        if score >= 50:
            print(f"   🚀 HIGH STEALTH PROBABILITY!")
        
        print()
    
    print("=" * 60)
    print("Quick test complete! No API credits used.")
    print("=" * 60)

def main():
    """Main test execution"""
    
    print("\nSelect test mode:")
    print("1. Quick Test (No API credits - uses mock data)")
    print("2. Limited Test (Uses 50 person + 50 company API credits)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        quick_test_stealth_detection()
    elif choice == '2':
        # Check for API key
        load_dotenv()
        if not os.getenv('API_KEY'):
            print("\n❌ Error: No API_KEY found in .env file")
            print("Please create a .env file with your PDL API key:")
            print("API_KEY=your_pdl_api_key_here")
            return
        
        confirm = input("\n⚠️ This will use up to 50 person + 50 company API credits. Continue? (y/n): ")
        if confirm.lower() == 'y':
            test_with_limited_credits()
        else:
            print("Test cancelled.")
    else:
        print("Exiting...")

if __name__ == "__main__":
    main()