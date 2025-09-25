"""
Generic Company Employee Fetcher
Fetches recent departures from any specified company using PeopleDataLabs API
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.pdl_client import get_pdl_client
from src.utils.query_updated import build_simple_sql_query, get_optimal_query_sequence

def fetch_company_employees(
    company_name,
    max_credits=10,
    days_back=90,
    output_dir='data/raw/updated_test',
    verbose=True
):
    """
    Fetch employees who recently left a specified company
    
    Args:
        company_name: Name of the company (e.g., 'openai', 'google', 'deepseek')
        max_credits: Maximum API credits to use (default 10)
        days_back: How many days back to search for departures (default 90)
        output_dir: Directory to save the results
        verbose: Print progress messages
        
    Returns:
        Path to the saved file
    """
    
    # Initialize PDL client
    load_dotenv()
    client = get_pdl_client()
    
    if verbose:
        print(f"\n[FETCHING] Employees from {company_name}")
        print(f"  - Max credits: {max_credits}")
        print(f"  - Days back: {days_back}")
        print("="*60)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Build query for the specific company
    target_company = company_name.lower()
    
    # Calculate date for recent departures
    departure_date = start_date.strftime('%Y-%m-%d')
    
    # Build dict query for recent departures from the target company
    # This finds people who previously worked at the company but don't anymore
    query = {
        'bool': {
            'must': [
                {'term': {'experience.company.name': target_company}},  # Worked at this company
                {'range': {'job_last_changed': {'gte': departure_date}}},  # Changed job recently
                {
                    'bool': {
                        'should': [
                            {'terms': {'job_title_role': ['engineering', 'research', 'product', 'design']}},
                            {'terms': {'job_title_levels': ['senior', 'lead', 'principal', 'staff', 'director', 'vp']}}
                        ]
                    }
                }
            ],
            'must_not': [
                {'term': {'job_company_name': target_company}}  # No longer at the company
            ]
        }
    }
    
    if verbose:
        print(f"\n[QUERY] Searching for {target_company} departures")
        print(f"  Date range: {departure_date} to now")
        print(f"  Focus: Senior and technical roles")
    
    all_employees = []
    total_credits_used = 0
    batch_size = 100
    
    # Execute paginated queries
    while total_credits_used < max_credits:
        if verbose and total_credits_used > 0:
            print(f"\n[BATCH {total_credits_used + 1}] Fetching more results...")
        
        try:
            # Execute PDL query
            response = client.person.search(
                query=query,
                size=batch_size,
                from_=total_credits_used * batch_size
            ).json()
            
            if response.get('status') == 200:
                records = response.get('data', [])
                
                if not records:
                    if verbose:
                        print(f"  [COMPLETE] No more results found")
                    break
                
                all_employees.extend(records)
                total_credits_used += 1
                
                if verbose:
                    print(f"  [OK] Found {len(records)} employees")
                    print(f"  Credits used: {total_credits_used}/{max_credits}")
                    print(f"  Total fetched: {len(all_employees)}")
                
                # Check if we got all available results
                total_available = response.get('total', 0)
                if len(all_employees) >= total_available:
                    if verbose:
                        print(f"  [COMPLETE] Retrieved all {total_available} available results")
                    break
            else:
                if verbose:
                    error = response.get('error', {})
                    print(f"  [ERROR] Query failed: {error.get('message', 'Unknown error')}")
                break
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            if verbose:
                print(f"  [ERROR] Exception: {str(e)}")
            continue
    
    # Remove duplicates based on PDL ID
    unique_employees = {}
    for emp in all_employees:
        # Try both 'id' and 'pdl_id' fields
        pdl_id = emp.get('id') or emp.get('pdl_id')
        if pdl_id:
            unique_employees[pdl_id] = emp
    
    employees_list = list(unique_employees.values())
    
    if verbose:
        print(f"\n[RESULTS]")
        print(f"  Total employees found: {len(employees_list)}")
        print(f"  Total credits used: {total_credits_used}")
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{company_name.lower()}_employees_{max_credits}credits_{timestamp}.jsonl"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for employee in employees_list:
            f.write(json.dumps(employee) + '\n')
    
    if verbose:
        print(f"\n[SAVED] Results to: {filepath}")
        print(f"  File size: {os.path.getsize(filepath) / 1024:.2f} KB")
        
        # Show sample of job titles found
        print(f"\n[SAMPLE] Job titles found:")
        job_titles = {}
        for emp in employees_list[:50]:  # Sample first 50
            title = emp.get('job_title', 'Unknown')
            if title:
                job_titles[title] = job_titles.get(title, 0) + 1
        
        for title, count in sorted(job_titles.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {title}: {count}")
    
    print("\n" + "="*60)
    print(f"[COMPLETE] Fetched {len(employees_list)} {company_name} employees")
    print("="*60)
    
    return filepath


def main():
    """Main function with examples"""
    
    print("\n" + "="*60)
    print("GENERIC COMPANY EMPLOYEE FETCHER")
    print("="*60)
    
    # You can modify these parameters
    COMPANY_NAME = "openai"  # Change this to any company: 'google', 'meta', 'deepseek', etc.
    MAX_CREDITS = 10
    DAYS_BACK = 90
    
    # Fetch employees
    saved_file = fetch_company_employees(
        company_name=COMPANY_NAME,
        max_credits=MAX_CREDITS,
        days_back=DAYS_BACK,
        output_dir='data/raw/updated_test',
        verbose=True
    )
    
    print(f"\nYou can now run the alert pipeline with this file:")
    print(f"python run_alert_pipeline_v2.py")
    
    # Example: Fetch from multiple companies
    # for company in ['openai', 'anthropic', 'google', 'meta']:
    #     fetch_company_employees(company, max_credits=5)


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        company = sys.argv[1]
        credits = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
        
        print(f"\nFetching {company} employees with {credits} credits for last {days} days...")
        fetch_company_employees(
            company_name=company,
            max_credits=credits,
            days_back=days
        )
    else:
        # Run with default parameters
        main()
        
        print("\n[TIP] You can also run with command line arguments:")
        print("python fetch_company_employees.py <company_name> <max_credits> <days_back>")
        print("Example: python fetch_company_employees.py deepseek 20 60")