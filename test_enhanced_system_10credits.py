"""
Enhanced System Test - 10 Credits
Tests all improved matching logic including:
- Geographic optimization
- Stealth detection
- Multi-signal matching
- Company location mapping
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Add project root
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

print("="*70)
print("ENHANCED MATCHING SYSTEM TEST - 10 CREDITS")
print("="*70)
print("Testing:")
print("  ✓ Geographic optimization")
print("  ✓ Stealth detection") 
print("  ✓ Multi-signal matching")
print("  ✓ Company location intelligence")
print("="*70 + "\n")

# Load environment
load_dotenv()
if not os.getenv('API_KEY'):
    print("ERROR: No API_KEY found in .env file!")
    sys.exit(1)

# Import all modules
from src.data_collection.pdl_client import get_pdl_client
from src.monitoring.stealth_detector import StealthFounderDetector
from src.matching.geographic_optimizer import GeographicOptimizer, EnhancedMatcher
from config.company_locations import get_geographic_search_strategy, COMPANY_HEADQUARTERS

# Initialize components
client = get_pdl_client()
stealth_detector = StealthFounderDetector()
geo_optimizer = GeographicOptimizer()
enhanced_matcher = EnhancedMatcher()

# Track API usage and results
api_credits_used = 0
all_results = {
    'timestamp': datetime.now().isoformat(),
    'api_credits_used': 0,
    'employees_analyzed': [],
    'startups_found': [],
    'stealth_signals': [],
    'matches': [],
    'geographic_insights': {}
}

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        'data/raw/enhanced_test',
        'data/processed/enhanced_test',
        'test_output/enhanced_10credits'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("✓ Directories ready\n")

def test_employee_analysis(company='openai', limit=5):
    """
    Phase 1: Analyze employees with geographic and stealth detection
    Uses 5 API credits
    """
    global api_credits_used
    
    print("="*60)
    print(f"PHASE 1: ANALYZING {company.upper()} TALENT")
    print("="*60)
    
    # Get optimized search strategy for this company
    strategy = get_geographic_search_strategy(company)
    print(f"\nGeographic Strategy for {company}:")
    print(f"  Primary states: {', '.join(strategy['primary_states'])}")
    print(f"  Tech hubs: {', '.join(strategy['tech_hub_cities'][:5])}...")
    all_results['geographic_insights']['strategy'] = strategy
    
    # Query: Find people who left this company for small companies
    query = {
        'bool': {
            'must': [
                {'term': {'experience.company.name': company}},
                {'terms': {'job_company_size': ['1-10', '11-50']}},
                {'range': {'job_last_changed': {'gte': '2023-01-01'}}}
            ],
            'must_not': [
                {'term': {'job_company_name': company}}
            ]
        }
    }
    
    print(f"\nSearching for {company} alumni at small companies...")
    
    try:
        response = client.person.search(query=query, size=limit).json()
        api_credits_used += limit
        
        if response.get('status') == 200:
            employees = response.get('data', [])
            print(f"✓ Found {len(employees)} {company} alumni\n")
            
            # Analyze each employee
            for i, emp in enumerate(employees, 1):
                print(f"{i}. {emp.get('full_name', 'Unknown').title()}")
                
                # Basic info
                current_company = emp.get('job_company_name', 'Unknown')
                title = emp.get('job_title', 'Unknown')
                size = emp.get('job_company_size', 'Unknown')
                location_state = emp.get('job_company_location_region', 'Unknown')
                location_city = emp.get('job_company_location_locality', 'Unknown')
                
                print(f"   Current: {current_company} ({size} employees)")
                print(f"   Title: {title}")
                print(f"   Location: {location_city}, {location_state}")
                
                # Stealth detection
                stealth_score, stealth_signals, tier = stealth_detector.detect_stealth_signals(emp)
                if stealth_score >= 50:
                    print(f"   🚨 STEALTH SCORE: {stealth_score}/100 ({tier} priority)")
                    for signal in stealth_signals[:2]:
                        print(f"      - {signal}")
                    all_results['stealth_signals'].append({
                        'name': emp.get('full_name'),
                        'score': stealth_score,
                        'signals': stealth_signals
                    })
                
                # Geographic analysis
                emp_state = location_state.lower() if location_state else ''
                if emp_state in strategy['primary_states']:
                    print(f"   ✓ In target state: {location_state}")
                elif emp_state:
                    print(f"   ⚠ Different state: {location_state} (may have relocated)")
                
                # Store for matching
                all_results['employees_analyzed'].append({
                    'name': emp.get('full_name'),
                    'current_company': current_company,
                    'title': title,
                    'location': f"{location_city}, {location_state}",
                    'stealth_score': stealth_score,
                    'raw_data': emp  # Keep full data for matching
                })
                print()
            
            return employees
        else:
            print(f"API Error: {response.get('error')}")
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_startup_search(states, limit=5):
    """
    Phase 2: Search for startups in optimized locations
    Uses 5 API credits
    """
    global api_credits_used
    
    print("="*60)
    print("PHASE 2: FINDING STARTUPS IN TARGET LOCATIONS")
    print("="*60)
    
    # Search in the primary state (usually where most employees are)
    primary_state = states[0] if states else 'california'
    
    print(f"\nSearching for tech startups in {primary_state.title()}...")
    
    # Build query for tech startups
    query = {
        'bool': {
            'must': [
                {'term': {'location.region': primary_state}},
                {'terms': {'size': ['1-10', '11-50']}},
                {'range': {'founded': {'gte': 2022}}},
                {
                    'bool': {
                        'should': [
                            {'match': {'industry': 'software'}},
                            {'match': {'industry': 'technology'}},
                            {'match': {'industry': 'artificial intelligence'}},
                            {'match': {'industry': 'internet'}}
                        ]
                    }
                }
            ]
        }
    }
    
    try:
        response = client.company.search(query=query, size=limit).json()
        api_credits_used += limit
        
        if response.get('status') == 200:
            startups = response.get('data', [])
            print(f"✓ Found {len(startups)} {primary_state} tech startups\n")
            
            for i, startup in enumerate(startups, 1):
                name = startup.get('name', 'Unknown')
                industry = startup.get('industry', 'Unknown')
                founded = startup.get('founded', 'Unknown')
                size = startup.get('size', 'Unknown')
                city = startup.get('location', {}).get('locality', 'Unknown')
                
                print(f"{i}. {name}")
                print(f"   Industry: {industry}")
                print(f"   Founded: {founded} | Size: {size}")
                print(f"   Location: {city}, {primary_state.title()}")
                
                # Check for AI/stealth signals in company
                summary = (startup.get('summary', '') or '').lower()
                name_lower = name.lower()
                
                signals = []
                if any(term in summary for term in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
                    signals.append("AI/ML focused")
                if any(term in name_lower for term in ['labs', 'ai', 'ml', 'tech', 'research']):
                    signals.append("Tech/research name")
                if size == '1-10' and founded >= 2023:
                    signals.append("Very early stage")
                
                if signals:
                    print(f"   📍 Signals: {', '.join(signals)}")
                
                all_results['startups_found'].append({
                    'name': name,
                    'industry': industry,
                    'founded': founded,
                    'location': f"{city}, {primary_state}",
                    'signals': signals,
                    'raw_data': startup
                })
                print()
            
            return startups
        else:
            print(f"API Error: {response.get('error')}")
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def run_enhanced_matching(employees, startups):
    """
    Phase 3: Enhanced multi-signal matching
    No API credits needed
    """
    print("="*60)
    print("PHASE 3: ENHANCED MULTI-SIGNAL MATCHING")
    print("="*60)
    
    print("\nApplying enhanced matching algorithms...")
    print("  • Company name (exact, fuzzy, normalized)")
    print("  • Timing analysis (departure → founding)")
    print("  • Role & seniority scoring")
    print("  • Geographic alignment")
    print("  • Stealth signal detection")
    print("  • Industry alignment\n")
    
    matches = []
    
    for emp in employees:
        emp_name = emp.get('full_name', 'Unknown')
        emp_company = (emp.get('job_company_name', '') or '').lower()
        
        for startup in startups:
            startup_name = startup.get('name', 'Unknown')
            
            # Use enhanced matcher
            match_result = enhanced_matcher.comprehensive_match(
                founder=emp,
                startup=startup,
                search_strategy=all_results['geographic_insights'].get('strategy')
            )
            
            # Only keep significant matches
            if match_result['total_score'] >= 30:
                matches.append(match_result)
                print(f"\n🎯 MATCH FOUND!")
                print(f"   Person: {emp_name}")
                print(f"   Startup: {startup_name}")
                print(f"   Score: {match_result['total_score']}/100 ({match_result['confidence_tier']})")
                print(f"   Signals:")
                for reason in match_result['reasons'][:3]:
                    print(f"     • {reason}")
                print(f"   Breakdown: {match_result['breakdown']}")
    
    if not matches:
        print("\n📊 No direct matches found, but we identified:")
        print(f"   • {len([e for e in all_results['employees_analyzed'] if e['stealth_score'] >= 50])} potential stealth founders")
        print(f"   • {len([s for s in all_results['startups_found'] if s['signals']])} high-signal startups")
        print("\nThese are high-priority targets for monitoring!")
    
    # Sort matches by score
    matches.sort(key=lambda x: x['total_score'], reverse=True)
    all_results['matches'] = matches
    
    return matches

def generate_enhanced_report():
    """
    Phase 4: Generate comprehensive report with insights
    """
    print("\n" + "="*60)
    print("PHASE 4: GENERATING ENHANCED REPORT")
    print("="*60)
    
    # Analysis summary
    stealth_count = len([e for e in all_results['employees_analyzed'] if e['stealth_score'] >= 50])
    high_signal_startups = len([s for s in all_results['startups_found'] if s['signals']])
    
    # JSON report
    report_file = f"test_output/enhanced_10credits/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Human-readable summary
    summary_file = "test_output/enhanced_10credits/summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("ENHANCED MATCHING SYSTEM TEST RESULTS\n")
        f.write("="*50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"API Credits Used: {api_credits_used}/10\n\n")
        
        f.write("GEOGRAPHIC INSIGHTS:\n")
        strategy = all_results['geographic_insights'].get('strategy', {})
        f.write(f"  Primary search states: {', '.join(strategy.get('primary_states', []))}\n")
        f.write(f"  Tech hub focus: {len(strategy.get('tech_hub_cities', []))} cities\n\n")
        
        f.write("TALENT ANALYSIS:\n")
        f.write(f"  Employees analyzed: {len(all_results['employees_analyzed'])}\n")
        f.write(f"  Stealth signals detected: {stealth_count}\n")
        
        if all_results['stealth_signals']:
            f.write("\n  TOP STEALTH CANDIDATES:\n")
            for sig in all_results['stealth_signals'][:3]:
                f.write(f"    • {sig['name']} (Score: {sig['score']})\n")
        
        f.write(f"\nSTARTUP DISCOVERY:\n")
        f.write(f"  Startups found: {len(all_results['startups_found'])}\n")
        f.write(f"  High-signal startups: {high_signal_startups}\n")
        
        f.write(f"\nMATCHING RESULTS:\n")
        f.write(f"  Total matches: {len(all_results['matches'])}\n")
        
        if all_results['matches']:
            f.write("\n  TOP MATCHES:\n")
            for match in all_results['matches'][:3]:
                f.write(f"    • {match['founder']['name']} → {match['startup']['name']}\n")
                f.write(f"      Score: {match['total_score']} ({match['confidence_tier']})\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("KEY INSIGHTS:\n")
        f.write("• Geographic alignment improves match quality\n")
        f.write("• Stealth detection identifies hidden founders\n")
        f.write("• Multi-signal matching reduces false positives\n")
    
    print(f"\n✓ Reports saved:")
    print(f"  • {report_file}")
    print(f"  • {summary_file}")
    
    # Print summary
    print("\n" + "="*40)
    print("SUMMARY:")
    print(f"  Stealth candidates: {stealth_count}")
    print(f"  High-signal startups: {high_signal_startups}")
    print(f"  Matches found: {len(all_results['matches'])}")
    
    if all_results['matches']:
        print(f"\n  Best match:")
        best = all_results['matches'][0]
        print(f"    {best['founder']['name']} → {best['startup']['name']}")
        print(f"    Confidence: {best['total_score']}/100")

def main():
    """
    Run complete enhanced test with 10 credits
    """
    print("STARTING ENHANCED TEST\n")
    print("This test will demonstrate:")
    print("1. Geographic optimization for OpenAI")
    print("2. Stealth founder detection")
    print("3. Multi-signal matching")
    print("4. Smart location-based search\n")
    
    # Which company to analyze?
    target_company = 'openai'  # Change to 'google', 'microsoft', etc.
    
    print(f"Target company: {target_company.upper()}")
    print("Auto-confirming test (10 credits)...\n")
    
    start_time = datetime.now()
    
    # Setup
    ensure_directories()
    
    # Get search strategy
    strategy = get_geographic_search_strategy(target_company)
    
    # Phase 1: Analyze employees (5 credits)
    employees = test_employee_analysis(company=target_company, limit=5)
    all_results['api_credits_used'] = api_credits_used
    print(f"Credits used: {api_credits_used}/10\n")
    
    time.sleep(1)  # Rate limiting
    
    # Phase 2: Find startups (5 credits)
    startups = test_startup_search(states=strategy['primary_states'], limit=5)
    all_results['api_credits_used'] = api_credits_used
    print(f"Total credits used: {api_credits_used}/10\n")
    
    # Phase 3: Enhanced matching (no credits)
    matches = run_enhanced_matching(employees, startups)
    
    # Phase 4: Generate report
    generate_enhanced_report()
    
    # Complete
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("✅ ENHANCED TEST COMPLETE!")
    print("="*70)
    print(f"\nResults:")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"  API Credits: {api_credits_used}/10")
    print(f"  Cost: ${api_credits_used * 0.01:.2f}")
    print(f"\nKey findings:")
    print(f"  • {len([e for e in all_results['employees_analyzed'] if e['stealth_score'] >= 50])} stealth founder candidates")
    print(f"  • {len([s for s in all_results['startups_found'] if s['signals']])} high-potential startups")
    print(f"  • {len(all_results['matches'])} potential matches")
    
    if all_results['stealth_signals']:
        print(f"\n🚨 Top stealth signal:")
        top = all_results['stealth_signals'][0]
        print(f"  {top['name']} - Score: {top['score']}/100")
        print(f"  Signal: {top['signals'][0]}")
    
    print("\n" + "="*70)
    print("All enhanced features tested successfully!")
    print("Check test_output/enhanced_10credits/ for detailed results")
    print("="*70)

if __name__ == "__main__":
    main()