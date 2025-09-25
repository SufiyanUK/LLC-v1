"""
OpenAI + California Test - Geographic Match Fix
Searches for OpenAI employees and California startups (same geography)
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

load_dotenv()

from src.data_collection.pdl_client import get_pdl_client

def test_geographic_matching():
    """
    Test with proper geographic alignment:
    - OpenAI employees (mostly in California)
    - California startups (same location)
    """
    
    client = get_pdl_client()
    
    print("="*60)
    print("OPENAI + CALIFORNIA GEOGRAPHIC MATCH TEST")
    print("="*60)
    
    # Query 1: OpenAI employees who left for small companies
    print("\n1. Fetching OpenAI alumni at small companies...")
    
    employee_query = {
        'bool': {
            'must': [
                {'term': {'experience.company.name': 'openai'}},  # Worked at OpenAI
                {'term': {'job_company_size': '1-10'}},          # Now at small company
                {'range': {'job_last_changed': {'gte': '2023-01-01'}}}  # Recent change
            ],
            'must_not': [
                {'term': {'job_company_name': 'openai'}}  # No longer at OpenAI
            ]
        }
    }
    
    try:
        response = client.person.search(query=employee_query, size=5).json()
        
        if response.get('status') == 200:
            employees = response.get('data', [])
            print(f"Found {len(employees)} OpenAI alumni at small companies")
            
            for emp in employees:
                print(f"\n  - {emp.get('full_name')}")
                print(f"    Previously: OpenAI")
                print(f"    Now at: {emp.get('job_company_name')} (size: {emp.get('job_company_size')})")
                print(f"    Location: {emp.get('job_company_location_locality', 'Unknown')}")
                
                # Store the current company name for matching
                emp['potential_startup_name'] = emp.get('job_company_name', '').lower()
    except Exception as e:
        print(f"Error: {e}")
        employees = []
    
    # Query 2: California startups (where OpenAI people actually are)
    print("\n2. Fetching California tech startups...")
    
    startup_query = """
        SELECT * FROM company 
        WHERE location.region = 'california'
        AND location.locality IN ('san francisco', 'palo alto', 'mountain view', 'san mateo')
        AND size = '1-10'
        AND founded >= 2022
        AND (industry CONTAINS 'software' OR industry CONTAINS 'technology' OR industry CONTAINS 'artificial intelligence')
        LIMIT 10
    """
    
    try:
        response = client.company.search(sql=startup_query, size=10).json()
        
        if response.get('status') == 200:
            startups = response.get('data', [])
            print(f"Found {len(startups)} California tech startups")
            
            for startup in startups:
                print(f"\n  - {startup.get('name')}")
                print(f"    Industry: {startup.get('industry')}")
                print(f"    Location: {startup.get('location', {}).get('locality', 'Unknown')}")
                print(f"    Founded: {startup.get('founded')}")
    except Exception as e:
        print(f"Error: {e}")
        startups = []
    
    # Query 3: Check for Delaware incorporation but California operation
    print("\n3. Checking dual-location pattern (Delaware inc, California ops)...")
    
    hybrid_query = """
        SELECT * FROM company 
        WHERE location.name CONTAINS 'delaware'
        AND (headquarters_location.region = 'california' 
             OR website CONTAINS '.ai' 
             OR website CONTAINS 'labs')
        AND size = '1-10'
        AND founded >= 2023
        LIMIT 5
    """
    
    try:
        response = client.company.search(sql=hybrid_query, size=5).json()
        
        if response.get('status') == 200:
            hybrid_cos = response.get('data', [])
            print(f"Found {len(hybrid_cos)} Delaware-incorporated, California-operating startups")
            
            for co in hybrid_cos:
                print(f"\n  - {co.get('name')}")
                print(f"    Incorporated: {co.get('location', {}).get('name', 'Unknown')}")
                print(f"    Operating: Likely California (based on pattern)")
    except Exception as e:
        print(f"Note: Hybrid query not supported - {e}")
    
    # Attempt matching
    print("\n" + "="*60)
    print("MATCHING ANALYSIS")
    print("="*60)
    
    if employees and startups:
        print("\nLooking for matches...")
        
        matches_found = 0
        for emp in employees:
            emp_company = emp.get('job_company_name', '').lower()
            
            for startup in startups:
                startup_name = startup.get('name', '').lower()
                
                # Simple name matching
                if emp_company and startup_name:
                    if (emp_company in startup_name or 
                        startup_name in emp_company or
                        emp_company.replace(' ', '') == startup_name.replace(' ', '')):
                        
                        print(f"\nPOTENTIAL MATCH FOUND!")
                        print(f"  Person: {emp.get('full_name')}")
                        print(f"  Company: {startup.get('name')}")
                        print(f"  Match basis: Name similarity")
                        matches_found += 1
        
        if matches_found == 0:
            print("\nNo direct matches found, but this is normal because:")
            print("  1. People don't always update their LinkedIn immediately")
            print("  2. Startups often operate in stealth mode")
            print("  3. Company names in profiles might not match legal names")
            
            print("\nSuggested improvements:")
            print("  - Track 'stealth startup' or 'building something new' signals")
            print("  - Monitor for 3-6 months as profiles get updated")
            print("  - Cross-reference with funding announcements")
    
    print("\n" + "="*60)
    print("GEOGRAPHIC INSIGHTS")
    print("="*60)
    print("\n1. Most OpenAI employees who leave stay in Bay Area")
    print("2. They start companies in California, not Delaware")
    print("3. Delaware is just for incorporation (legal/tax benefits)")
    print("4. Better matching requires same-geography searches")
    
    return employees, startups

if __name__ == "__main__":
    test_geographic_matching()