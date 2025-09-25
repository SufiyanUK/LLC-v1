"""
Proper PDL REST API Implementation
This fetches employees correctly by post-processing the results
Since PDL doesn't support complex array filtering, we fetch broader results and filter locally
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_left_company_recently(employee: Dict, company_name: str, days_back: int = 90) -> tuple[bool, Optional[str]]:
    """
    Check if employee left the specified company within the specified days
    
    Returns:
        (True/False, departure_date or None)
    """
    company_name_lower = company_name.lower()
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    experiences = employee.get('experience', [])
    
    for exp in experiences:
        if isinstance(exp, dict):
            # Check company info
            company_data = exp.get('company', {})
            if isinstance(company_data, dict):
                exp_company_name = (company_data.get('name', '') or '').lower()
                
                # Check if this is the target company
                if company_name_lower in exp_company_name:
                    # Check end date
                    end_date_str = exp.get('end_date')
                    if end_date_str:
                        try:
                            # Parse various date formats
                            if len(end_date_str) == 7:  # YYYY-MM format
                                end_date = datetime.strptime(end_date_str, '%Y-%m')
                            elif len(end_date_str) == 10:  # YYYY-MM-DD format
                                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                            else:
                                continue
                            
                            # Check if they left within our time window
                            if end_date >= cutoff_date:
                                return True, end_date_str
                        except:
                            continue
    
    return False, None


def fetch_and_filter_departures(
    company_name: str,
    max_final_results: int = 10,
    days_back: int = 90,
    initial_fetch_size: int = 500,
    output_dir: str = 'data/raw/updated_test',
    verbose: bool = True
):
    """
    Fetch employees from PDL and filter locally for actual departures
    
    Args:
        company_name: Company to search for departures
        max_final_results: Maximum number of verified departures to return
        days_back: How many days back to look for departures
        initial_fetch_size: How many records to fetch from PDL (will be filtered down)
        output_dir: Where to save results
        verbose: Print progress
        
    Returns:
        Path to saved file or None
    """
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        raise ValueError("No API_KEY found in .env file")
    
    if verbose:
        print(f"\n[REST API] Fetching and filtering {company_name} departures")
        print(f"  Target: {max_final_results} verified departures")
        print(f"  Days back: {days_back}")
        print(f"  Initial fetch size: {initial_fetch_size} records")
        print("="*60)
    
    # PDL REST API endpoint
    url = "https://api.peopledatalabs.com/v5/person/search"
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Calculate date for rough filtering
    rough_date = (datetime.now() - timedelta(days=days_back + 30)).strftime('%Y-%m-%d')
    
    # Use a broader query that we'll filter locally
    # This gets people who worked at the company and changed jobs recently
    sql_query = f"""
    SELECT * FROM person 
    WHERE experience.company.name = '{company_name.lower()}'
    AND job_last_changed >= '{rough_date}'
    AND job_company_name != '{company_name.lower()}'
    AND (
        job_title_role IN ('engineering', 'research', 'product', 'design', 'management')
        OR job_title_levels IN ('senior', 'lead', 'principal', 'staff', 'director', 'vp', 'head', 'chief')
    )
    """
    
    if verbose:
        print(f"\n[STRATEGY] Two-phase approach:")
        print(f"  1. Fetch up to {initial_fetch_size} candidates from PDL")
        print(f"  2. Filter locally for actual {company_name} departures")
        print(f"\n[SQL QUERY]")
        print(sql_query)
    
    params = {
        'sql': sql_query.strip(),
        'size': initial_fetch_size,
        'pretty': True
    }
    
    try:
        # Phase 1: Fetch from PDL
        if verbose:
            print(f"\n[PHASE 1] Fetching from PDL...")
        
        response = requests.post(url, headers=headers, json=params)
        
        if response.status_code != 200:
            error_data = response.json()
            print(f"[ERROR] API returned {response.status_code}")
            print(f"  Message: {error_data.get('error', {}).get('message', 'Unknown')}")
            return None
        
        data = response.json()
        candidates = data.get('data', [])
        total_available = data.get('total', 0)
        
        if verbose:
            print(f"  Retrieved {len(candidates)} candidates")
            print(f"  Total available in PDL: {total_available}")
            
            # Note about credits
            credits_used = len(candidates)
            print(f"  Credits used: {credits_used}")
        
        if not candidates:
            print("[NO RESULTS] No candidates found")
            return None
        
        # Phase 2: Filter locally for actual departures
        if verbose:
            print(f"\n[PHASE 2] Filtering for actual {company_name} departures...")
        
        verified_departures = []
        
        for employee in candidates:
            # Check if this person actually left the company recently
            left_recently, departure_date = check_left_company_recently(
                employee, company_name, days_back
            )
            
            if left_recently:
                # Add departure info to the record
                employee['_departure_verified'] = True
                employee['_departure_date'] = departure_date
                employee['_departure_company'] = company_name
                
                verified_departures.append(employee)
                
                if verbose and len(verified_departures) <= 5:
                    print(f"  ✓ {employee.get('full_name', 'Unknown')} - Left {departure_date}")
                
                # Stop if we have enough results
                if len(verified_departures) >= max_final_results:
                    break
        
        if verbose:
            print(f"\n[RESULTS]")
            print(f"  Candidates fetched: {len(candidates)}")
            print(f"  Verified departures: {len(verified_departures)}")
            print(f"  Filter rate: {len(verified_departures)/len(candidates)*100:.1f}%")
        
        # Save results
        if verified_departures:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save the verified departures
            filename = f"{company_name.lower()}_verified_departures_{len(verified_departures)}records_{timestamp}.jsonl"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for emp in verified_departures:
                    f.write(json.dumps(emp) + '\n')
            
            if verbose:
                print(f"\n[SAVED] {filepath}")
                print(f"  File size: {os.path.getsize(filepath) / 1024:.2f} KB")
                
                # Show summary
                print(f"\n[DEPARTURE SUMMARY]")
                for i, emp in enumerate(verified_departures[:10], 1):
                    print(f"\n  {i}. {emp.get('full_name', 'Unknown')}")
                    print(f"     Left {company_name}: {emp.get('_departure_date', 'Unknown')}")
                    print(f"     Now at: {emp.get('job_company_name', 'Unknown')}")
                    print(f"     Current role: {emp.get('job_title', 'Unknown')}")
            
            # Also save the full candidate list for analysis
            debug_filename = f"{company_name.lower()}_all_candidates_{len(candidates)}records_{timestamp}.jsonl"
            debug_filepath = os.path.join(output_dir, debug_filename)
            
            with open(debug_filepath, 'w', encoding='utf-8') as f:
                for emp in candidates:
                    f.write(json.dumps(emp) + '\n')
            
            if verbose:
                print(f"\n[DEBUG] Also saved all candidates to: {debug_filename}")
            
            return filepath
            
        else:
            print(f"\n[NO VERIFIED DEPARTURES] None of the {len(candidates)} candidates actually left {company_name} recently")
            return None
            
    except Exception as e:
        print(f"\n[EXCEPTION] {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def analyze_departure_patterns(company_name: str, sample_size: int = 100):
    """
    Analyze patterns in departure data to understand the data structure
    """
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("[ERROR] No API_KEY found")
        return
    
    print(f"\n[ANALYZING] Departure patterns for {company_name}")
    print("="*60)
    
    url = "https://api.peopledatalabs.com/v5/person/search"
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    
    # Get a sample of people who worked at the company
    sql = f"""
    SELECT * FROM person 
    WHERE experience.company.name = '{company_name.lower()}'
    AND job_company_name != '{company_name.lower()}'
    LIMIT {sample_size}
    """
    
    response = requests.post(url, headers=headers, json={'sql': sql, 'size': sample_size})
    
    if response.status_code == 200:
        data = response.json()
        employees = data.get('data', [])
        
        print(f"Analyzing {len(employees)} employees...\n")
        
        recent_departures = []
        date_formats = {}
        
        for emp in employees:
            experiences = emp.get('experience', [])
            for exp in experiences:
                if isinstance(exp, dict):
                    company = exp.get('company', {})
                    if isinstance(company, dict):
                        if company_name.lower() in (company.get('name', '') or '').lower():
                            end_date = exp.get('end_date')
                            if end_date:
                                # Track date format
                                date_format = f"Length: {len(end_date)}"
                                date_formats[date_format] = date_formats.get(date_format, 0) + 1
                                
                                # Check if recent
                                try:
                                    if len(end_date) >= 7:  # At least YYYY-MM
                                        year = int(end_date[:4])
                                        month = int(end_date[5:7]) if len(end_date) >= 7 else 1
                                        
                                        if year >= 2024 or (year == 2023 and month >= 9):
                                            recent_departures.append({
                                                'name': emp.get('full_name'),
                                                'end_date': end_date,
                                                'current_company': emp.get('job_company_name'),
                                                'job_last_changed': emp.get('job_last_changed')
                                            })
                                except:
                                    pass
        
        print(f"Date format distribution:")
        for fmt, count in date_formats.items():
            print(f"  {fmt}: {count} occurrences")
        
        print(f"\nRecent departures found: {len(recent_departures)}")
        for dep in recent_departures[:5]:
            print(f"  - {dep['name']}: Left {dep['end_date']}, Now at {dep['current_company']}")
        
    else:
        print(f"Error: {response.status_code}")


def main():
    """Main function"""
    
    print("\n" + "="*60)
    print("PDL REST API - PROPER DEPARTURE DETECTION")
    print("="*60)
    
    # Default test
    company = "meta"
    max_results = 10
    days = 90
    
    print(f"\nFetching verified {company} departures...")
    print(f"Target results: {max_results} people who actually left")
    print(f"Time window: Last {days} days")
    
    result = fetch_and_filter_departures(
        company_name=company,
        max_final_results=max_results,
        days_back=days,
        initial_fetch_size=200,  # Fetch more candidates to filter
        verbose=True
    )
    
    if result:
        print(f"\n[SUCCESS] Verified departures saved to: {result}")
    else:
        print(f"\n[FAILED] Could not find verified departures")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--analyze':
            # Analyze patterns
            company = sys.argv[2] if len(sys.argv) > 2 else 'meta'
            analyze_departure_patterns(company, sample_size=50)
        else:
            # Normal execution
            company = sys.argv[1]
            max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
            
            # Fetch more candidates than needed since we'll filter
            initial_size = min(max_results * 20, 500)  # Fetch 20x more to filter down
            
            result = fetch_and_filter_departures(
                company_name=company,
                max_final_results=max_results,
                days_back=days,
                initial_fetch_size=initial_size,
                verbose=True
            )
    else:
        main()