"""
Fixed Company Employee Fetcher - Proper Credit Management
IMPORTANT: 1 PDL Credit = 1 Person Record (not 1 API call!)
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
    
    CREDIT USAGE WARNING:
    - 1 credit = 1 person record
    - Setting max_credits=10 means you get UP TO 10 employee records
    - NOT 10 API calls of 100 records each!
    
    Args:
        company_name: Name of the company (e.g., 'openai', 'google', 'deepseek')
        max_credits: Maximum API credits to use (= max employee records to fetch)
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
        print(f"  - Max credits (= max employees): {max_credits}")
        print(f"  - Days back: {days_back}")
        print(f"  WARNING: 1 credit = 1 employee record")
        print("="*60)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Build query for the specific company
    target_company = company_name.lower()
    
    # Calculate date for recent departures
    departure_date = start_date.strftime('%Y-%m-%d')
    
    # Build dict query for recent departures from the target company
    # PDL doesn't support nested queries, so using their simpler format
    query = {
        'bool': {
            'must': [
                {'term': {'experience.company.name': target_company}},  # Worked at this company
                {'range': {'experience.end_date': {'gte': departure_date}}},  # LEFT this company recently (end_date)
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
                {'term': {'job_company_name': target_company}}  # Currently not at the company
            ]
        }
    }
    
    if verbose:
        print(f"\n[QUERY] Searching for {target_company} departures")
        print(f"  Looking for people who LEFT {target_company} after: {departure_date}")
        print(f"  Focus: Senior and technical roles")
        print(f"  Using experience.end_date to find actual departure dates")
    
    all_employees = []
    total_credits_used = 0
    
    # FIXED: Set batch size based on credits remaining
    # Never request more records than we have credits for
    remaining_credits = max_credits
    
    # Execute queries with proper credit management
    while total_credits_used < max_credits:
        # Calculate how many records to request this batch
        # Never request more than remaining credits
        batch_size = min(remaining_credits, 100)  # PDL max is usually 100 per call
        
        if batch_size <= 0:
            break
            
        if verbose:
            print(f"\n[BATCH] Requesting {batch_size} records...")
            print(f"  Credits used so far: {total_credits_used}/{max_credits}")
            print(f"  Remaining credits: {remaining_credits}")
        
        try:
            # Execute PDL query
            # IMPORTANT: 'size' parameter = number of credits that will be consumed
            response = client.person.search(
                query=query,
                size=batch_size,  # This is how many credits we'll use!
                from_=total_credits_used  # Offset for pagination
            ).json()
            
            if response.get('status') == 200:
                records = response.get('data', [])
                
                if not records:
                    if verbose:
                        print(f"  [COMPLETE] No more results found")
                    break
                
                # Add records to our list
                all_employees.extend(records)
                
                # FIXED: Count actual records returned (each costs 1 credit)
                credits_consumed = len(records)
                total_credits_used += credits_consumed
                remaining_credits = max_credits - total_credits_used
                
                if verbose:
                    print(f"  [OK] Found {len(records)} employees")
                    print(f"  Credits consumed this batch: {credits_consumed}")
                    print(f"  Total credits used: {total_credits_used}/{max_credits}")
                    print(f"  Total employees fetched: {len(all_employees)}")
                
                # Check if we got all available results
                total_available = response.get('total', 0)
                if verbose and total_available > 0:
                    print(f"  Total available in query: {total_available}")
                    if total_available > max_credits:
                        print(f"  WARNING: {total_available - max_credits} more records available but credit limit reached")
                
                # If we got fewer records than requested, we've exhausted the results
                if len(records) < batch_size:
                    if verbose:
                        print(f"  [COMPLETE] All available results retrieved")
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
            break  # Stop on error to avoid wasting credits
    
    # Remove duplicates based on PDL ID
    unique_employees = {}
    for emp in all_employees:
        pdl_id = emp.get('id') or emp.get('pdl_id')
        if pdl_id:
            unique_employees[pdl_id] = emp
    
    employees_list = list(unique_employees.values())
    
    if verbose:
        print(f"\n[RESULTS]")
        print(f"  Total unique employees found: {len(employees_list)}")
        print(f"  Total credits used: {total_credits_used}")
        print(f"  Credits remaining: {max_credits - total_credits_used}")
        
        if total_credits_used > max_credits:
            print(f"  WARNING: Used {total_credits_used - max_credits} more credits than intended!")
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{company_name.lower()}_employees_{total_credits_used}credits_{timestamp}.jsonl"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for employee in employees_list:
            f.write(json.dumps(employee) + '\n')
    
    if verbose:
        print(f"\n[SAVED] Results to: {filepath}")
        print(f"  File size: {os.path.getsize(filepath) / 1024:.2f} KB")
        
        # Show sample of job titles found
        if employees_list:
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
    print(f"[CREDITS] Used exactly {total_credits_used} credits")
    print("="*60)
    
    return filepath


def safe_test_mode():
    """
    Safe test mode with minimal credit usage
    """
    print("\n" + "="*60)
    print("SAFE TEST MODE - MINIMAL CREDIT USAGE")
    print("="*60)
    
    # VERY CONSERVATIVE SETTINGS FOR TESTING
    COMPANY_NAME = "openai"
    MAX_CREDITS = 5  # Only use 5 credits = get 5 employees MAX
    DAYS_BACK = 30   # Recent departures only
    
    print(f"\nThis will fetch UP TO {MAX_CREDITS} employees from {COMPANY_NAME}")
    print(f"Each employee record costs 1 credit")
    print(f"Maximum cost: {MAX_CREDITS} credits\n")
    
    confirm = input("Continue with safe test? (y/n): ")
    if confirm.lower() != 'y':
        print("Test cancelled")
        return
    
    saved_file = fetch_company_employees(
        company_name=COMPANY_NAME,
        max_credits=MAX_CREDITS,
        days_back=DAYS_BACK,
        output_dir='data/raw/updated_test',
        verbose=True
    )
    
    print(f"\nSafe test complete!")
    print(f"File saved: {saved_file}")
    return saved_file


def main():
    """Main function with credit warnings"""
    
    print("\n" + "="*60)
    print("COMPANY EMPLOYEE FETCHER - FIXED CREDIT MANAGEMENT")
    print("="*60)
    print("\nIMPORTANT CREDIT INFORMATION:")
    print("  * 1 credit = 1 employee record")
    print("  * max_credits=10 means you get UP TO 10 employees")
    print("  * This is NOT 10 batches of 100 employees!")
    print("="*60)
    
    # Default parameters - CONSERVATIVE
    COMPANY_NAME = "openai"
    MAX_CREDITS = 10  # This means MAX 10 employees, not 1000!
    DAYS_BACK = 90
    
    print(f"\nDefault settings:")
    print(f"  Company: {COMPANY_NAME}")
    print(f"  Max employees to fetch: {MAX_CREDITS}")
    print(f"  Days back: {DAYS_BACK}")
    print(f"  Estimated credit cost: {MAX_CREDITS} credits")
    
    # Ask for confirmation
    confirm = input("\nProceed with these settings? (y/n/test): ")
    
    if confirm.lower() == 'test':
        safe_test_mode()
        return
    elif confirm.lower() != 'y':
        print("Cancelled by user")
        return
    
    # Fetch employees
    saved_file = fetch_company_employees(
        company_name=COMPANY_NAME,
        max_credits=MAX_CREDITS,
        days_back=DAYS_BACK,
        output_dir='data/raw/updated_test',
        verbose=True
    )
    
    print(f"\nYou can now run the alert pipeline with this file:")
    print(f"python run_alert_pipeline_v2.py {os.path.basename(saved_file)}")


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            # Safe test mode
            safe_test_mode()
        else:
            company = sys.argv[1]
            credits = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
            
            # Skip confirmation when called from API (has 3 arguments)
            # Only ask for confirmation when run manually with partial arguments
            if len(sys.argv) == 4:
                # Called from API with all arguments - no confirmation needed
                print(f"\n[API MODE] Fetching up to {credits} {company} employees")
                fetch_company_employees(
                    company_name=company,
                    max_credits=credits,
                    days_back=days
                )
            else:
                # Manual run - ask for confirmation
                print(f"\nCREDIT WARNING:")
                print(f"This will use UP TO {credits} credits to fetch {credits} employee records")
                print(f"NOT {credits} batches of 100 employees!")
                
                confirm = input(f"\nConfirm: Fetch up to {credits} {company} employees? (y/n): ")
                if confirm.lower() == 'y':
                    fetch_company_employees(
                        company_name=company,
                        max_credits=credits,
                        days_back=days
                    )
                else:
                    print("Cancelled by user")
    else:
        # Run with default parameters
        print("\n[TIP] Command line usage:")
        print("  python fetch_company_employees_fixed.py <company> <max_credits> <days>")
        print("  python fetch_company_employees_fixed.py openai 5 30")
        print("  python fetch_company_employees_fixed.py --test  # Safe test mode")
        print()
        
        main()