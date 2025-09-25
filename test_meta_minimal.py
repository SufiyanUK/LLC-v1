"""
Minimal Test - Meta Departures with 4-5 credits only
Shows the REST API approach with local filtering
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

def find_meta_departures_minimal():
    """
    Find Meta employees who LEFT in last 90 days
    Using only 4-5 credits
    """
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("[ERROR] No API_KEY found in .env file")
        return
    
    print("\n" + "="*60)
    print("MINIMAL TEST: FINDING META DEPARTURES (4-5 CREDITS)")
    print("="*60)
    
    url = "https://api.peopledatalabs.com/v5/person/search"
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    
    # Calculate dates
    departure_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    broader_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
    
    print(f"\nTarget: People who LEFT Meta after {departure_date}")
    print(f"Credits to use: 5 maximum")
    
    # Strategy: Fetch recent job changers from Meta, then filter locally
    sql = f"""
    SELECT * FROM person 
    WHERE experience.company.name = 'meta'
    AND job_last_changed >= '{broader_date}'
    AND job_company_name != 'meta'
    AND (
        job_title_role IN ('engineering', 'research', 'product', 'design', 'management')
        OR job_title_levels IN ('senior', 'lead', 'principal', 'staff', 'director', 'vp')
    )
    """
    
    print("\n[FETCHING] Using broader query to get candidates...")
    
    params = {
        'sql': sql.strip(),
        'size': 5  # ONLY 5 CREDITS
    }
    
    response = requests.post(url, headers=headers, json=params)
    
    if response.status_code == 200:
        data = response.json()
        candidates = data.get('data', [])
        total_available = data.get('total', 0)
        
        print(f"[RESULTS] Got {len(candidates)} candidates (Total available: {total_available})")
        print(f"[CREDITS] Used exactly {len(candidates)} credits")
        
        # Now filter for ACTUAL Meta departures
        print("\n[FILTERING] Checking who actually LEFT Meta recently...")
        print("-"*40)
        
        verified_departures = []
        
        for person in candidates:
            name = person.get('full_name', 'Unknown')
            current_company = person.get('job_company_name', 'Unknown')
            
            print(f"\nChecking: {name} (now at {current_company})")
            
            # Look through their experience
            meta_experience = None
            for exp in person.get('experience', []):
                if isinstance(exp, dict):
                    company = exp.get('company', {})
                    if isinstance(company, dict):
                        company_name = (company.get('name', '') or '').lower()
                        if 'meta' in company_name or 'facebook' in company_name:
                            meta_experience = exp
                            break
            
            if meta_experience:
                end_date_str = meta_experience.get('end_date')
                if end_date_str:
                    print(f"  -> Found Meta experience, ended: {end_date_str}")
                    
                    try:
                        # Check if they left within 90 days
                        if len(end_date_str) >= 7:
                            year = int(end_date_str[:4])
                            month = int(end_date_str[5:7])
                            
                            # Simple check: 2024-09 or later (assuming today is Dec 2024)
                            if year > 2024 or (year == 2024 and month >= 9):
                                verified_departures.append({
                                    'name': name,
                                    'left_date': end_date_str,
                                    'current_company': current_company,
                                    'current_role': person.get('job_title', 'Unknown'),
                                    'pdl_id': person.get('id')
                                })
                                print(f"  -> VERIFIED: Left Meta on {end_date_str}")
                            else:
                                print(f"  -> Too old: {end_date_str}")
                    except Exception as e:
                        print(f"  -> Date parse error: {e}")
                else:
                    print(f"  -> Still at Meta (no end_date)")
            else:
                print(f"  -> No Meta experience found")
        
        print("\n" + "="*60)
        print(f"SUMMARY:")
        print(f"  Candidates fetched: {len(candidates)}")
        print(f"  Verified Meta departures: {len(verified_departures)}")
        print(f"  Credits used: {len(candidates)}")
        
        if verified_departures:
            print(f"\n[VERIFIED DEPARTURES FROM META]")
            for i, dep in enumerate(verified_departures, 1):
                print(f"\n{i}. {dep['name']}")
                print(f"   Left Meta: {dep['left_date']}")
                print(f"   Now at: {dep['current_company']}")
                print(f"   Current role: {dep['current_role']}")
        else:
            print(f"\n[NO VERIFIED DEPARTURES]")
            print("None of the {len(candidates)} candidates actually left Meta recently")
            print("This shows we need to fetch MORE candidates to find actual departures")
        
        print("\n[RECOMMENDATION]")
        print("To find actual departures, we should:")
        print("1. Fetch more candidates (20-50) with broader criteria")
        print("2. Filter locally for actual Meta end_dates")
        print("3. This is what fetch_employees_rest_proper.py does")
        
    else:
        error = response.json()
        print(f"\n[ERROR] {response.status_code}")
        print(f"Message: {error.get('error', {}).get('message', 'Unknown')}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("\nThis test will use EXACTLY 5 PDL credits")
    print("It demonstrates why we need local filtering")
    confirm = input("\nProceed? (y/n): ")
    if confirm.lower() == 'y':
        find_meta_departures_minimal()
    else:
        print("Cancelled")