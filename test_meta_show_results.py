"""
Test and SHOW the actual results from the Meta query
See what PDL actually returns with the combined query
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

def test_and_show_results():
    """
    Run the query that returned 2 records and SHOW them in detail
    """
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("[ERROR] No API_KEY found in .env file")
        return
    
    print("\n" + "="*60)
    print("FETCHING AND ANALYZING META QUERY RESULTS")
    print("="*60)
    
    url = "https://api.peopledatalabs.com/v5/person/search"
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    
    departure_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    print(f"\nSearching for Meta departures after: {departure_date}")
    
    # The query that returned 2 records
    query = {
        "size": 3,  # Get 3 to see a bit more
        "query": {
            "bool": {
                "must": [
                    {"term": {"experience.company.name": "meta"}},
                    {"range": {"experience.end_date": {"gte": departure_date}}},
                    {"bool": {"must_not": {"term": {"job_company_name": "meta"}}}}
                ]
            }
        }
    }
    
    print("\n[QUERY BEING SENT]")
    print(json.dumps(query, indent=2))
    
    response = requests.post(url, headers=headers, json=query)
    
    if response.status_code == 200:
        data = response.json()
        records = data.get('data', [])
        total = data.get('total', 0)
        
        print(f"\n[RESULTS] Got {len(records)} records (Total available: {total})")
        print("="*60)
        
        # Analyze each record in detail
        actual_meta_departures = []
        false_positives = []
        
        for i, person in enumerate(records, 1):
            print(f"\n[PERSON {i}]")
            print("-"*40)
            
            # Basic info
            name = person.get('full_name', 'Unknown')
            pdl_id = person.get('id', 'No ID')
            current_company = person.get('job_company_name', 'Unknown')
            current_title = person.get('job_title', 'Unknown')
            job_last_changed = person.get('job_last_changed', 'Unknown')
            
            print(f"Name: {name}")
            print(f"PDL ID: {pdl_id}")
            print(f"Current Company: {current_company}")
            print(f"Current Title: {current_title}")
            print(f"Job Last Changed: {job_last_changed}")
            
            # Check their experience array
            print(f"\n[EXPERIENCE HISTORY]")
            experiences = person.get('experience', [])
            
            meta_experience_found = False
            meta_departure_date = None
            
            for j, exp in enumerate(experiences[:5], 1):  # Show first 5 experiences
                if isinstance(exp, dict):
                    company_info = exp.get('company', {})
                    company_name = company_info.get('name', 'Unknown') if isinstance(company_info, dict) else 'Unknown'
                    title = exp.get('title', {})
                    title_name = title.get('name', 'Unknown') if isinstance(title, dict) else 'Unknown'
                    start_date = exp.get('start_date', 'Unknown')
                    end_date = exp.get('end_date', None)
                    
                    print(f"\n  Experience {j}:")
                    print(f"    Company: {company_name}")
                    print(f"    Title: {title_name}")
                    print(f"    Period: {start_date} to {end_date if end_date else 'Present'}")
                    
                    # Check if this is Meta
                    if company_name and ('meta' in company_name.lower() or 'facebook' in company_name.lower()):
                        meta_experience_found = True
                        if end_date:
                            meta_departure_date = end_date
                            print(f"    >>> META/FACEBOOK DEPARTURE: {end_date} <<<")
                            
                            # Check if it's recent
                            try:
                                if len(end_date) >= 7:
                                    year = int(end_date[:4])
                                    month = int(end_date[5:7])
                                    cutoff = datetime.now() - timedelta(days=90)
                                    
                                    if datetime(year, month, 1) >= cutoff:
                                        print(f"    >>> RECENT DEPARTURE (within 90 days) <<<")
                                    else:
                                        print(f"    >>> OLD DEPARTURE (more than 90 days ago) <<<")
                            except:
                                pass
                        else:
                            print(f"    >>> STILL AT META (no end_date) <<<")
            
            # Summary for this person
            print(f"\n[ANALYSIS]")
            if meta_experience_found and meta_departure_date:
                print(f"✓ VALID: Left Meta on {meta_departure_date}, now at {current_company}")
                actual_meta_departures.append({
                    'name': name,
                    'left_meta': meta_departure_date,
                    'current_company': current_company,
                    'current_title': current_title
                })
            elif meta_experience_found and not meta_departure_date:
                print(f"✗ FALSE POSITIVE: Still at Meta (no end_date)")
                false_positives.append(name)
            else:
                print(f"✗ FALSE POSITIVE: No Meta experience found in history")
                false_positives.append(name)
                
            print("="*60)
        
        # Final summary
        print(f"\n[FINAL SUMMARY]")
        print(f"Total records fetched: {len(records)}")
        print(f"Actual Meta departures: {len(actual_meta_departures)}")
        print(f"False positives: {len(false_positives)}")
        
        if actual_meta_departures:
            print(f"\n[VERIFIED META DEPARTURES]")
            for dep in actual_meta_departures:
                print(f"- {dep['name']}: Left {dep['left_meta']}, now at {dep['current_company']}")
        
        if false_positives:
            print(f"\n[FALSE POSITIVES]")
            for name in false_positives:
                print(f"- {name}")
        
        # Save results for inspection
        output_file = f"meta_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)
        print(f"\n[SAVED] Full results saved to: {output_file}")
        
    else:
        print(f"\n[ERROR] Query failed: {response.status_code}")
        print(response.json())
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("\nThis will use 3 PDL credits to show detailed results")
    confirm = input("Continue? (y/n): ")
    if confirm.lower() == 'y':
        test_and_show_results()
    else:
        print("Cancelled")