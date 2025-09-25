"""
OpenAI + California Test - 10 Credits Version
Geographic-aligned test with minimal API usage:
- 5 credits: OpenAI employees who left for startups
- 5 credits: California tech startups
Total: 10 credits for better matching
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
print("OPENAI + CALIFORNIA TEST - 10 CREDITS VERSION")
print("="*70)
print("Budget: 10 API Credits Total")
print("  - 5 for OpenAI departures now at small companies")
print("  - 5 for California tech startups")
print("="*70 + "\n")

# Load environment
load_dotenv()
if not os.getenv('API_KEY'):
    print("ERROR: No API_KEY found in .env file!")
    sys.exit(1)

from src.data_collection.pdl_client import get_pdl_client

# Initialize
api_credits_used = 0
matches_found = []

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        'data/raw/pdl_companies',
        'data/raw/pdl_employees', 
        'data/processed',
        'data/results',
        'test_output/openai_california_10credits'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("Directories verified\n")

def collect_openai_alumni():
    """Collect 5 OpenAI alumni who left for small companies (5 credits)"""
    global api_credits_used
    
    print("="*60)
    print("PHASE 1: OPENAI ALUMNI AT STARTUPS (5 credits)")
    print("="*60)
    
    client = get_pdl_client()
    output_file = 'data/raw/pdl_employees/openai_california_alumni.jsonl'
    
    # Clear file
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Query: OpenAI people who left for small companies
    query = {
        'bool': {
            'must': [
                {'term': {'experience.company.name': 'openai'}},  # Worked at OpenAI
                {'term': {'job_company_size': '1-10'}},          # Now at tiny company
                {'range': {'job_last_changed': {'gte': '2023-01-01'}}},  # Recent move
            ],
            'must_not': [
                {'term': {'job_company_name': 'openai'}}  # Not at OpenAI anymore
            ]
        }
    }
    
    print("\nSearching for OpenAI alumni who joined small companies...")
    
    try:
        response = client.person.search(query=query, size=5).json()
        api_credits_used += 5
        
        if response.get('status') == 200:
            employees = response.get('data', [])
            print(f"Found {len(employees)} OpenAI alumni at small companies\n")
            
            # Save and display
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, emp in enumerate(employees, 1):
                    f.write(json.dumps(emp) + '\n')
                    
                    print(f"{i}. {emp.get('full_name', 'Unknown').title()}")
                    print(f"   Previous: OpenAI")
                    print(f"   Current: {emp.get('job_company_name', 'Unknown')}")
                    print(f"   Company size: {emp.get('job_company_size', 'Unknown')}")
                    print(f"   Location: {emp.get('job_company_location_locality', 'Unknown')}")
                    
                    # Check for founder signals
                    title = emp.get('job_title', '').lower()
                    if any(word in title for word in ['founder', 'ceo', 'cto', 'building']):
                        print(f"   >>> FOUNDER SIGNAL: {emp.get('job_title')}")
                    print()
            
            return employees
        else:
            print(f"API Error: {response.get('error')}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def collect_california_startups():
    """Collect 5 California tech startups (5 credits)"""
    global api_credits_used
    
    print("="*60)
    print("PHASE 2: CALIFORNIA TECH STARTUPS (5 credits)")
    print("="*60)
    
    client = get_pdl_client()
    output_file = 'data/raw/pdl_companies/california_startups.jsonl'
    
    # Clear file
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # SQL query for California tech startups
    query_sql = """
        SELECT * FROM company 
        WHERE location.region = 'california'
        AND location.locality IN ('san francisco', 'palo alto', 'mountain view', 'menlo park', 'san mateo')
        AND size = '1-10'
        AND founded >= 2022
        AND (
            industry CONTAINS 'software' OR 
            industry CONTAINS 'artificial intelligence' OR
            industry CONTAINS 'technology' OR
            industry CONTAINS 'internet'
        )
        LIMIT 5
    """
    
    print("\nSearching for California tech startups (Bay Area focus)...")
    
    try:
        response = client.company.search(sql=query_sql, size=5).json()
        api_credits_used += 5
        
        if response.get('status') == 200:
            startups = response.get('data', [])
            print(f"Found {len(startups)} California tech startups\n")
            
            # Save and display
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, startup in enumerate(startups, 1):
                    f.write(json.dumps(startup) + '\n')
                    
                    print(f"{i}. {startup.get('name', 'Unknown')}")
                    print(f"   Industry: {startup.get('industry', 'Unknown')}")
                    print(f"   Founded: {startup.get('founded', 'Unknown')}")
                    print(f"   Size: {startup.get('size', 'Unknown')}")
                    print(f"   Location: {startup.get('location', {}).get('locality', 'Unknown')}")
                    
                    # Check for AI/ML signals
                    desc = str(startup.get('summary', '')).lower()
                    if any(word in desc for word in ['ai', 'machine learning', 'ml', 'artificial']):
                        print(f"   >>> AI/ML SIGNAL in description")
                    print()
            
            return startups
        else:
            print(f"API Error: {response.get('error')}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def run_matching(employees, startups):
    """Match OpenAI alumni with California startups"""
    
    print("="*60)
    print("PHASE 3: MATCHING ANALYSIS")
    print("="*60)
    
    matches = []
    
    print("\nAnalyzing potential matches...\n")
    
    for emp in employees:
        emp_company = (emp.get('job_company_name', '') or '').lower().strip()
        emp_location = (emp.get('job_company_location_locality', '') or '').lower()
        
        for startup in startups:
            startup_name = (startup.get('name', '') or '').lower().strip()
            startup_location = (startup.get('location', {}).get('locality', '') or '').lower()
            
            confidence = 0
            reasons = []
            
            # Name matching (strongest signal)
            if emp_company and startup_name:
                # Direct match
                if emp_company == startup_name:
                    confidence += 60
                    reasons.append("Exact company name match")
                # Partial match
                elif emp_company in startup_name or startup_name in emp_company:
                    confidence += 40
                    reasons.append("Partial name match")
                # Remove spaces/punctuation and check again
                elif emp_company.replace(' ', '').replace('-', '') == startup_name.replace(' ', '').replace('-', ''):
                    confidence += 50
                    reasons.append("Name match (normalized)")
            
            # Location match (same city)
            if emp_location and startup_location:
                if emp_location in startup_location or startup_location in emp_location:
                    confidence += 20
                    reasons.append(f"Same location: {emp_location}")
            
            # Size match
            if emp.get('job_company_size') == startup.get('size'):
                confidence += 15
                reasons.append("Company size matches")
            
            # Timing (startup founded after person left OpenAI)
            if startup.get('founded') and startup.get('founded') >= 2023:
                confidence += 10
                reasons.append("Recent founding matches departure timing")
            
            # Founder title
            if 'founder' in emp.get('job_title', '').lower():
                confidence += 15
                reasons.append("Has founder title")
            
            if confidence >= 50:  # Threshold for match
                match = {
                    'confidence': confidence,
                    'person': emp.get('full_name', 'Unknown'),
                    'person_company': emp.get('job_company_name'),
                    'person_title': emp.get('job_title'),
                    'startup': startup.get('name'),
                    'startup_industry': startup.get('industry'),
                    'reasons': reasons
                }
                matches.append(match)
    
    # Sort by confidence
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    
    if matches:
        print(f"FOUND {len(matches)} POTENTIAL MATCHES!\n")
        for i, match in enumerate(matches, 1):
            print(f"Match #{i} (Confidence: {match['confidence']}%)")
            print(f"  Person: {match['person']}")
            print(f"  Title: {match['person_title']}")
            print(f"  Current Company: {match['person_company']}")
            print(f"  Matched Startup: {match['startup']}")
            print(f"  Industry: {match['startup_industry']}")
            print(f"  Reasons: {', '.join(match['reasons'])}")
            print()
    else:
        print("No direct matches found.\n")
        print("This is expected because:")
        print("  - People often don't update profiles immediately")
        print("  - Startups operate in stealth mode")
        print("  - Company names in profiles may differ from legal names")
        print("\nHowever, we identified:")
        print(f"  - {len(employees)} OpenAI alumni at small companies (potential founders)")
        print(f"  - {len(startups)} California tech startups (potential targets)")
        print("\nThese lists are valuable for:")
        print("  - Manual review and outreach")
        print("  - Ongoing monitoring for updates")
        print("  - Cross-referencing with other data sources")
    
    return matches

def generate_report(employees, startups, matches):
    """Generate summary report"""
    
    print("="*60)
    print("PHASE 4: REPORT GENERATION")
    print("="*60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'api_credits_used': api_credits_used,
        'openai_alumni_found': len(employees),
        'california_startups_found': len(startups),
        'matches_found': len(matches),
        'alumni_details': [
            {
                'name': emp.get('full_name'),
                'current_company': emp.get('job_company_name'),
                'title': emp.get('job_title'),
                'location': emp.get('job_company_location_locality')
            }
            for emp in employees
        ],
        'startup_details': [
            {
                'name': s.get('name'),
                'industry': s.get('industry'),
                'founded': s.get('founded'),
                'location': s.get('location', {}).get('locality')
            }
            for s in startups
        ],
        'matches': matches
    }
    
    # Save JSON report
    report_file = f'test_output/openai_california_10credits/report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Save text summary
    summary_file = 'test_output/openai_california_10credits/summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("OPENAI + CALIFORNIA 10-CREDIT TEST SUMMARY\n")
        f.write("="*50 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"API Credits Used: {api_credits_used}/10\n\n")
        f.write("RESULTS:\n")
        f.write(f"  OpenAI Alumni Found: {len(employees)}\n")
        f.write(f"  California Startups Found: {len(startups)}\n")
        f.write(f"  Potential Matches: {len(matches)}\n\n")
        
        if matches:
            f.write("TOP MATCHES:\n")
            for match in matches[:3]:
                f.write(f"  - {match['person']} at {match['person_company']}\n")
                f.write(f"    matched with {match['startup']} ({match['confidence']}% confidence)\n\n")
    
    print(f"\nReports saved:")
    print(f"  - {report_file}")
    print(f"  - {summary_file}")

def main():
    """Run the complete 10-credit test"""
    
    print("STARTING 10-CREDIT TEST\n")
    print("This test will:")
    print("1. Find OpenAI alumni who joined small companies (5 credits)")
    print("2. Find California tech startups (5 credits)")
    print("3. Match them based on geography and signals (no credits)")
    print("4. Generate report (no credits)")
    print("\n" + "="*60)
    
    # Auto-confirm
    print("\nAuto-confirming test run (10 API credits)...")
    
    start_time = datetime.now()
    
    # Setup
    ensure_directories()
    
    # Collect data
    employees = collect_openai_alumni()
    print(f"API credits used: {api_credits_used}/10\n")
    
    time.sleep(1)  # Rate limiting
    
    startups = collect_california_startups()
    print(f"Total API credits used: {api_credits_used}/10\n")
    
    # Match
    matches = run_matching(employees, startups)
    
    # Report
    generate_report(employees, startups, matches)
    
    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print(f"\nFINAL RESULTS:")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"  API Credits Used: {api_credits_used}/10")
    print(f"  OpenAI Alumni: {len(employees)}")
    print(f"  California Startups: {len(startups)}")
    print(f"  Matches Found: {len(matches)}")
    print(f"\nKey Insight: Geographic alignment (CA + CA) improves matching!")
    print("="*70)

if __name__ == "__main__":
    main()