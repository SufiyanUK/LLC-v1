"""
Test REST API for Meta Departures
This demonstrates why we need local filtering - PDL can't filter array elements properly
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

def test_meta_departures():
    """
    Test fetching Meta employees who LEFT in last 90 days
    Using REST API with local filtering
    """
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("[ERROR] No API_KEY found in .env file")
        return
    
    print("\n" + "="*60)
    print("TESTING META DEPARTURES - REST API WITH LOCAL FILTERING")
    print("="*60)
    
    # Calculate date for 90 days ago
    departure_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    print(f"\nLooking for people who LEFT Meta after: {departure_date}")
    
    # PDL REST API endpoint
    url = "https://api.peopledatalabs.com/v5/person/search"
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # ATTEMPT 1: Try the SQL query as you specified
    print("\n[ATTEMPT 1] Using SQL query with experience.end_date")
    print("-"*40)
    
    sql_query = f"""
    SELECT * FROM person
    WHERE experience.company.name = 'meta'
    AND experience.end_date >= '{departure_date}'
    AND job_company_name != 'meta'
    AND (
        job_title_role IN ('engineering', 'research', 'product', 'design')
        OR job_title_levels IN ('senior', 'lead', 'principal', 'staff', 'director', 'vp')
    )
    """
    
    print("SQL Query:")
    print(sql_query)
    
    params = {
        'sql': sql_query.strip(),
        'size': 2  # Using 5 credits
    }
    
    response = requests.post(url, headers=headers, json=params)
    
    if response.status_code == 200:
        data = response.json()
        records = data.get('data', [])
        total = data.get('total', 0)
        
        print(f"\nResults: {len(records)} records fetched")
        print(f"Total available: {total}")
        
        # Analyze what we got
        print("\n[ANALYSIS OF RESULTS]")
        for i, person in enumerate(records[:3], 1):
            print(f"\n{i}. {person.get('full_name', 'Unknown')}")
            print(f"   Current: {person.get('job_title')} @ {person.get('job_company_name')}")
            
            # Check their Meta experience
            found_meta = False
            for exp in person.get('experience', []):
                if isinstance(exp, dict):
                    company = exp.get('company', {})
                    if isinstance(company, dict) and 'meta' in (company.get('name', '') or '').lower():
                        end_date = exp.get('end_date')
                        print(f"   Meta experience: ended {end_date or 'STILL THERE'}")
                        found_meta = True
                        break
            
            if not found_meta:
                print("   Meta experience: NOT FOUND IN EXPERIENCE ARRAY")
    else:
        print(f"\nError: {response.status_code}")
        error_msg = response.json().get('error', {}).get('message', 'Unknown')
        print(f"Message: {error_msg}")
    
    print("\n" + "="*60)
    
    # ATTEMPT 2: Broader query with local filtering
    print("\n[ATTEMPT 2] Broader query + local filtering")
    print("-"*40)
    print("This is what fetch_employees_rest_proper.py does")
    
    # Use a broader query that we know works
    broader_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
    
    sql_query2 = f"""
    SELECT * FROM person 
    WHERE experience.company.name = 'meta'
    AND job_last_changed >= '{broader_date}'
    AND job_company_name != 'meta'
    AND (
        job_title_role IN ('engineering', 'research', 'product', 'design')
        OR job_title_levels IN ('senior', 'lead', 'principal', 'staff', 'director', 'vp')
    )
    """
    
    print("\nBroader SQL Query (will filter locally):")
    print(sql_query2)
    
    params2 = {
        'sql': sql_query2.strip(),
        'size': 20  # Fetch more to filter
    }
    
    response2 = requests.post(url, headers=headers, json=params2)
    
    if response2.status_code == 200:
        data2 = response2.json()
        candidates = data2.get('data', [])
        
        print(f"\nPhase 1: Fetched {len(candidates)} candidates")
        
        # Phase 2: Local filtering for actual Meta departures
        actual_departures = []
        
        for person in candidates:
            # Check if they actually LEFT Meta recently
            for exp in person.get('experience', []):
                if isinstance(exp, dict):
                    company = exp.get('company', {})
                    if isinstance(company, dict) and 'meta' in (company.get('name', '') or '').lower():
                        end_date_str = exp.get('end_date')
                        if end_date_str:
                            try:
                                # Parse the end date
                                if len(end_date_str) == 7:  # YYYY-MM
                                    end_date = datetime.strptime(end_date_str, '%Y-%m')
                                elif len(end_date_str) == 10:  # YYYY-MM-DD
                                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                                else:
                                    continue
                                
                                # Check if they left within 90 days
                                if end_date >= datetime.now() - timedelta(days=90):
                                    actual_departures.append({
                                        'name': person.get('full_name'),
                                        'left_meta': end_date_str,
                                        'now_at': person.get('job_company_name'),
                                        'current_role': person.get('job_title')
                                    })
                                    break
                            except:
                                continue
        
        print(f"\nPhase 2: Found {len(actual_departures)} ACTUAL Meta departures")
        
        if actual_departures:
            print("\n[VERIFIED META DEPARTURES]")
            for i, dep in enumerate(actual_departures[:2], 1):
                print(f"\n{i}. {dep['name']}")
                print(f"   Left Meta: {dep['left_meta']}")
                print(f"   Now at: {dep['now_at']}")
                print(f"   Role: {dep['current_role']}")
        else:
            print("\nNo verified departures found in the candidates")
            print("This shows why we need to fetch MORE candidates and filter locally")
    
    else:
        print(f"\nError in broader query: {response2.status_code}")
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("- PDL SQL cannot properly filter nested array elements")
    print("- We must fetch broader results and filter locally")
    print("- This is why fetch_employees_rest_proper.py uses 2 phases")
    print("="*60)

if __name__ == "__main__":
    print("\nThis test will use up to 25 PDL credits (5 + 20)")
    confirm = input("Continue? (y/n): ")
    if confirm.lower() == 'y':
        test_meta_departures()
    else:
        print("Test cancelled")