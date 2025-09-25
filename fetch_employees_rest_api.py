"""
PDL REST API Implementation for Employee Fetching
Uses direct REST API calls instead of the PDL Python client
This gives us more control over the query structure
"""

import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def fetch_company_departures_rest(
    company_name,
    max_credits=10,
    days_back=90,
    output_dir='data/raw/updated_test',
    verbose=True
):
    """
    Fetch employees using PDL REST API directly
    
    Args:
        company_name: Name of the company (e.g., 'anthropic', 'meta')
        max_credits: Maximum number of records to fetch (1 credit = 1 record)
        days_back: How many days back to search for departures
        output_dir: Directory to save results
        verbose: Print detailed progress
        
    Returns:
        Path to saved file
    """
    
    # Load API key
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        raise ValueError("No API_KEY found in .env file")
    
    if verbose:
        print(f"\n[REST API] Fetching {company_name} departures")
        print(f"  Max records: {max_credits}")
        print(f"  Days back: {days_back}")
        print("="*60)
    
    # Calculate date range
    departure_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # PDL REST API endpoint
    url = "https://api.peopledatalabs.com/v5/person/search"
    
    # Headers with API key
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Build SQL query - trying different approaches
    # Approach 1: Simple SQL with experience fields
    sql_query = f"""
    SELECT * FROM person 
    WHERE experience.company.name = '{company_name.lower()}'
    AND experience.end_date >= '{departure_date}'
    AND job_company_name != '{company_name.lower()}'
    """
    
    # Add role filters
    sql_query += """
    AND (
        job_title_role IN ('engineering', 'research', 'product', 'design', 'management')
        OR job_title_levels IN ('senior', 'lead', 'principal', 'staff', 'director', 'vp', 'head', 'chief')
    )
    """
    
    if verbose:
        print(f"\n[SQL QUERY]")
        print(sql_query)
        print("\n[EXECUTING] REST API call...")
    
    # Prepare request body
    params = {
        'sql': sql_query.strip(),
        'size': max_credits,
        'pretty': True
    }
    
    try:
        # Make REST API call
        response = requests.post(url, headers=headers, json=params)
        
        if verbose:
            print(f"[RESPONSE] Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract results
            total_count = data.get('total', 0)
            records = data.get('data', [])
            
            if verbose:
                print(f"[RESULTS] Total matching: {total_count}")
                print(f"[RESULTS] Fetched: {len(records)}")
                
                if total_count > max_credits:
                    print(f"[WARNING] {total_count - max_credits} more records available")
            
            # Save results
            if records:
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{company_name.lower()}_rest_api_{len(records)}records_{timestamp}.jsonl"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    for record in records:
                        f.write(json.dumps(record) + '\n')
                
                if verbose:
                    print(f"\n[SAVED] {filepath}")
                    print(f"  File size: {os.path.getsize(filepath) / 1024:.2f} KB")
                    
                    # Show sample of results
                    print(f"\n[SAMPLE] First 3 results:")
                    for i, emp in enumerate(records[:3], 1):
                        print(f"\n  {i}. {emp.get('full_name', 'Unknown')}")
                        print(f"     Current: {emp.get('job_title', 'Unknown')} @ {emp.get('job_company_name', 'Unknown')}")
                        print(f"     Job changed: {emp.get('job_last_changed', 'Unknown')}")
                        
                        # Try to find Meta/Anthropic in experience
                        experiences = emp.get('experience', [])
                        for exp in experiences:
                            if isinstance(exp, dict):
                                company = exp.get('company', {})
                                if isinstance(company, dict):
                                    comp_name = company.get('name', '').lower()
                                    if company_name.lower() in comp_name:
                                        print(f"     Left {company.get('name', '')}: {exp.get('end_date', 'Unknown')}")
                                        break
                
                return filepath
            else:
                print(f"\n[NO RESULTS] No employees found matching criteria")
                return None
                
        else:
            error_data = response.json()
            print(f"\n[ERROR] API returned {response.status_code}")
            print(f"  Message: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            # If query error, try alternative approach
            if response.status_code == 400:
                print("\n[RETRY] Trying alternative query approach...")
                return fetch_with_elasticsearch_query(
                    company_name, max_credits, days_back, 
                    output_dir, verbose, api_key
                )
            
            return None
            
    except Exception as e:
        print(f"\n[EXCEPTION] {str(e)}")
        return None


def fetch_with_elasticsearch_query(
    company_name, max_credits, days_back, 
    output_dir, verbose, api_key
):
    """
    Alternative approach using Elasticsearch query format
    """
    
    if verbose:
        print(f"\n[ELASTICSEARCH] Trying Elasticsearch query format")
    
    departure_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api.peopledatalabs.com/v5/person/search"
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Elasticsearch-style query
    es_query = {
        'query': {
            'bool': {
                'must': [
                    # Worked at the company
                    {
                        'term': {
                            'experience.company.name': company_name.lower()
                        }
                    },
                    # Left recently (using job_last_changed as fallback)
                    {
                        'range': {
                            'job_last_changed': {
                                'gte': departure_date
                            }
                        }
                    }
                ],
                'must_not': [
                    # Not currently at the company
                    {
                        'term': {
                            'job_company_name': company_name.lower()
                        }
                    }
                ],
                'should': [
                    # Prefer senior roles
                    {'term': {'job_title_levels': 'director'}},
                    {'term': {'job_title_levels': 'senior'}},
                    {'term': {'job_title_levels': 'principal'}},
                    {'term': {'job_title_levels': 'staff'}},
                    {'term': {'job_title_levels': 'lead'}},
                    {'term': {'job_title_levels': 'vp'}},
                    # Technical roles
                    {'term': {'job_title_role': 'engineering'}},
                    {'term': {'job_title_role': 'research'}},
                    {'term': {'job_title_role': 'product'}},
                    {'term': {'job_title_role': 'design'}}
                ],
                'minimum_should_match': 1
            }
        },
        'size': max_credits
    }
    
    if verbose:
        print(f"\n[ES QUERY]")
        print(json.dumps(es_query, indent=2))
    
    try:
        response = requests.post(url, headers=headers, json=es_query)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('data', [])
            
            if verbose:
                print(f"\n[ES RESULTS] Found {len(records)} records")
            
            if records:
                # Save results
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{company_name.lower()}_es_query_{len(records)}records_{timestamp}.jsonl"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    for record in records:
                        f.write(json.dumps(record) + '\n')
                
                if verbose:
                    print(f"[SAVED] {filepath}")
                
                return filepath
            
        else:
            print(f"\n[ES ERROR] {response.status_code}: {response.json()}")
            
    except Exception as e:
        print(f"\n[ES EXCEPTION] {str(e)}")
    
    return None


def test_multiple_approaches(company_name, max_credits=5, days_back=90):
    """
    Test different query approaches to find what works best
    """
    
    print("\n" + "="*60)
    print(f"TESTING MULTIPLE PDL QUERY APPROACHES FOR {company_name.upper()}")
    print("="*60)
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("[ERROR] No API_KEY found in .env file")
        return
    
    url = "https://api.peopledatalabs.com/v5/person/search"
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    departure_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Test 1: Simple SQL
    print("\n[TEST 1] Simple SQL Query")
    print("-"*40)
    sql1 = f"""
    SELECT * FROM person 
    WHERE experience.company.name = '{company_name.lower()}'
    AND job_last_changed >= '{departure_date}'
    AND job_company_name != '{company_name.lower()}'
    LIMIT {max_credits}
    """
    
    response = requests.post(url, headers=headers, json={'sql': sql1})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data.get('data', []))} records")
        print(f"Total available: {data.get('total', 0)}")
    else:
        print(f"Error: {response.json().get('error', {}).get('message', 'Unknown')}")
    
    time.sleep(1)  # Rate limiting
    
    # Test 2: SQL with experience.end_date
    print("\n[TEST 2] SQL with experience.end_date")
    print("-"*40)
    sql2 = f"""
    SELECT * FROM person 
    WHERE experience.company.name = '{company_name.lower()}'
    AND experience.end_date >= '{departure_date}'
    AND job_company_name != '{company_name.lower()}'
    LIMIT {max_credits}
    """
    
    response = requests.post(url, headers=headers, json={'sql': sql2})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data.get('data', []))} records")
        print(f"Total available: {data.get('total', 0)}")
    else:
        print(f"Error: {response.json().get('error', {}).get('message', 'Unknown')}")
    
    time.sleep(1)
    
    # Test 3: Elasticsearch query
    print("\n[TEST 3] Elasticsearch Query")
    print("-"*40)
    es_query = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'experience.company.name': company_name.lower()}},
                    {'range': {'job_last_changed': {'gte': departure_date}}}
                ],
                'must_not': [
                    {'term': {'job_company_name': company_name.lower()}}
                ]
            }
        },
        'size': max_credits
    }
    
    response = requests.post(url, headers=headers, json=es_query)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data.get('data', []))} records")
        print(f"Total available: {data.get('total', 0)}")
    else:
        print(f"Error: {response.json().get('error', {}).get('message', 'Unknown')}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE - Check which approach gives best results")
    print("="*60)


def main():
    """Main function for testing"""
    
    print("\n" + "="*60)
    print("PDL REST API EMPLOYEE FETCHER")
    print("="*60)
    
    # Test with small credits first
    COMPANY = "anthropic"
    MAX_CREDITS = 3
    DAYS_BACK = 90
    
    print(f"\nFetching {COMPANY} employees...")
    print(f"Max records: {MAX_CREDITS}")
    print(f"Days back: {DAYS_BACK}")
    
    result = fetch_company_departures_rest(
        company_name=COMPANY,
        max_credits=MAX_CREDITS,
        days_back=DAYS_BACK,
        verbose=True
    )
    
    if result:
        print(f"\n[SUCCESS] Data saved to: {result}")
    else:
        print(f"\n[FAILED] No data retrieved")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            # Test multiple approaches
            company = sys.argv[2] if len(sys.argv) > 2 else 'anthropic'
            test_multiple_approaches(company, max_credits=2)
        else:
            # Normal execution
            company = sys.argv[1]
            credits = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
            
            result = fetch_company_departures_rest(
                company_name=company,
                max_credits=credits,
                days_back=days,
                verbose=True
            )
    else:
        main()