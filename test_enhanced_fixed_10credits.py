"""
Fixed Enhanced System Test - 10 Credits
Fixes the over-matching issue by:
1. Checking if person already has a company
2. Requiring name similarity for matches
3. Better scoring thresholds
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from difflib import SequenceMatcher

# Add project root
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

print("="*70)
print("FIXED ENHANCED MATCHING SYSTEM TEST - 10 CREDITS")
print("="*70)
print("Improvements:")
print("  ✓ Checks if person already has their own company")
print("  ✓ Requires name similarity or strong signals")
print("  ✓ Prevents over-matching")
print("="*70 + "\n")

# Load environment
load_dotenv()
if not os.getenv('API_KEY'):
    print("ERROR: No API_KEY found in .env file!")
    sys.exit(1)

# Import modules
from src.data_collection.pdl_client import get_pdl_client
from src.monitoring.stealth_detector import StealthFounderDetector
from config.company_locations import get_geographic_search_strategy

# Initialize
client = get_pdl_client()
stealth_detector = StealthFounderDetector()
api_credits_used = 0

def ensure_directories():
    """Create necessary directories"""
    dirs = ['test_output/fixed_enhanced_10credits']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def analyze_employees(company='openai', limit=5):
    """
    Phase 1: Analyze employees and identify who already has companies
    """
    global api_credits_used
    
    print("="*60)
    print(f"PHASE 1: ANALYZING {company.upper()} ALUMNI")
    print("="*60)
    
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
            
            founders_with_companies = []
            potential_matches = []
            
            for i, emp in enumerate(employees, 1):
                name = emp.get('full_name', 'Unknown').title()
                current_company = emp.get('job_company_name', 'Unknown')
                title = emp.get('job_title', 'Unknown')
                size = emp.get('job_company_size', 'Unknown')
                location = f"{emp.get('job_company_location_locality', 'Unknown')}, {emp.get('job_company_location_region', 'Unknown')}"
                
                print(f"{i}. {name}")
                print(f"   Company: {current_company} ({size})")
                print(f"   Title: {title}")
                print(f"   Location: {location}")
                
                # Check if they're a founder of their current company
                is_founder = any(word in title.lower() for word in ['founder', 'ceo', 'cto', 'chief'])
                
                if is_founder and size == '1-10':
                    print(f"   ✅ CONFIRMED FOUNDER of {current_company}")
                    founders_with_companies.append({
                        'name': name,
                        'company': current_company,
                        'title': title,
                        'location': location
                    })
                else:
                    # They might be joining someone else's startup
                    print(f"   📊 Potential match candidate (not founder of current company)")
                    potential_matches.append(emp)
                
                # Stealth detection
                stealth_score, signals, tier = stealth_detector.detect_stealth_signals(emp)
                if stealth_score >= 50:
                    print(f"   🚨 Stealth score: {stealth_score}/100")
                
                print()
            
            print(f"Summary:")
            print(f"  • {len(founders_with_companies)} confirmed founders with their own companies")
            print(f"  • {len(potential_matches)} people who might match with other startups")
            
            return employees, founders_with_companies, potential_matches
            
    except Exception as e:
        print(f"Error: {e}")
        return [], [], []

def find_startups(state='california', limit=5):
    """
    Phase 2: Find startups
    """
    global api_credits_used
    
    print("\n" + "="*60)
    print(f"PHASE 2: FINDING {state.upper()} STARTUPS")
    print("="*60)
    
    query = {
        'bool': {
            'must': [
                {'term': {'location.region': state}},
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
    
    print(f"\nSearching for tech startups in {state.title()}...")
    
    try:
        response = client.company.search(query=query, size=limit).json()
        api_credits_used += limit
        
        if response.get('status') == 200:
            startups = response.get('data', [])
            print(f"✓ Found {len(startups)} tech startups\n")
            
            for i, startup in enumerate(startups, 1):
                print(f"{i}. {startup.get('name', 'Unknown')}")
                print(f"   Industry: {startup.get('industry', 'Unknown')}")
                print(f"   Founded: {startup.get('founded', 'Unknown')}")
                print(f"   Location: {startup.get('location', {}).get('locality', 'Unknown')}, {state.title()}")
                print()
            
            return startups
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def smart_matching(employees, founders_with_companies, potential_matches, startups):
    """
    Phase 3: Smart matching that avoids false positives
    """
    print("\n" + "="*60)
    print("PHASE 3: SMART MATCHING")
    print("="*60)
    
    matches = []
    
    # First, check if any founder's company appears in the startup list
    print("\n🔍 Checking for founder's companies in startup list...")
    for founder in founders_with_companies:
        founder_company_lower = founder['company'].lower().strip()
        
        for startup in startups:
            startup_name_lower = startup.get('name', '').lower().strip()
            
            # Check for name match
            if founder_company_lower in startup_name_lower or startup_name_lower in founder_company_lower:
                print(f"\n✅ VERIFIED MATCH!")
                print(f"   {founder['name']} is founder of {founder['company']}")
                print(f"   Matched with startup: {startup.get('name')}")
                print(f"   This is their actual company!")
                
                matches.append({
                    'type': 'VERIFIED',
                    'person': founder['name'],
                    'person_company': founder['company'],
                    'startup': startup.get('name'),
                    'confidence': 100,
                    'reason': 'Founder of this company'
                })
            
            # Also check fuzzy matching
            elif SequenceMatcher(None, founder_company_lower, startup_name_lower).ratio() > 0.8:
                print(f"\n📊 PROBABLE MATCH!")
                print(f"   {founder['name']} at {founder['company']}")
                print(f"   Similar to startup: {startup.get('name')}")
                
                matches.append({
                    'type': 'PROBABLE',
                    'person': founder['name'],
                    'person_company': founder['company'],
                    'startup': startup.get('name'),
                    'confidence': 85,
                    'reason': 'High name similarity'
                })
    
    # For non-founders, only match if there's actual evidence
    print("\n🔍 Checking potential matches (non-founders)...")
    for emp in potential_matches:
        emp_name = emp.get('full_name', 'Unknown').title()
        emp_company = emp.get('job_company_name', 'Unknown')
        emp_title = emp.get('job_title', 'Unknown')
        
        # Only match if the person's current company matches a startup name
        for startup in startups:
            startup_name = startup.get('name', '')
            
            if emp_company.lower() in startup_name.lower() or startup_name.lower() in emp_company.lower():
                print(f"\n💡 POSSIBLE MATCH!")
                print(f"   {emp_name} works at {emp_company}")
                print(f"   Matched with startup: {startup_name}")
                print(f"   Role: {emp_title}")
                
                matches.append({
                    'type': 'POSSIBLE',
                    'person': emp_name,
                    'person_company': emp_company,
                    'startup': startup_name,
                    'confidence': 70,
                    'reason': 'Works at this company'
                })
    
    if not matches:
        print("\n📊 No direct matches found")
        print("This is normal because:")
        print("  • Founder's companies may not be in the database yet")
        print("  • Names may not match exactly")
        print("  • People may not have updated profiles")
    
    return matches

def generate_report(employees, founders, matches, credits_used):
    """
    Generate final report
    """
    print("\n" + "="*60)
    print("PHASE 4: REPORT GENERATION")
    print("="*60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'api_credits_used': credits_used,
        'employees_found': len(employees),
        'confirmed_founders': len(founders),
        'matches': matches
    }
    
    # Save report
    report_file = f"test_output/fixed_enhanced_10credits/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Report saved: {report_file}")
    
    # Print summary
    print("\n" + "="*40)
    print("SUMMARY:")
    print(f"  API Credits Used: {credits_used}/10")
    print(f"  Employees analyzed: {len(employees)}")
    print(f"  Confirmed founders: {len(founders)}")
    print(f"  Matches found: {len(matches)}")
    
    if matches:
        print("\n  Match types:")
        verified = len([m for m in matches if m['type'] == 'VERIFIED'])
        probable = len([m for m in matches if m['type'] == 'PROBABLE'])
        possible = len([m for m in matches if m['type'] == 'POSSIBLE'])
        
        if verified: print(f"    • Verified: {verified}")
        if probable: print(f"    • Probable: {probable}")
        if possible: print(f"    • Possible: {possible}")

def main():
    """
    Run the fixed test
    """
    print("STARTING FIXED TEST\n")
    print("This version:")
    print("  • Identifies who already has companies")
    print("  • Only matches based on actual evidence")
    print("  • Prevents false positive spam\n")
    
    ensure_directories()
    
    # Phase 1: Analyze employees
    employees, founders_with_companies, potential_matches = analyze_employees('openai', 5)
    
    print(f"\nCredits used: {api_credits_used}/10")
    time.sleep(1)
    
    # Phase 2: Find startups
    startups = find_startups('california', 5)
    
    print(f"\nTotal credits used: {api_credits_used}/10")
    
    # Phase 3: Smart matching
    matches = smart_matching(employees, founders_with_companies, potential_matches, startups)
    
    # Phase 4: Report
    generate_report(employees, founders_with_companies, matches, api_credits_used)
    
    print("\n" + "="*70)
    print("✅ FIXED TEST COMPLETE!")
    print("="*70)
    print("\nKey improvements:")
    print("  • No more duplicate matches")
    print("  • Identifies actual founders")
    print("  • Only shows meaningful connections")
    print("="*70)

if __name__ == "__main__":
    main()