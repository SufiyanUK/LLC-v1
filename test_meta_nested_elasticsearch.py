"""
Test Elasticsearch Nested Query for Meta Departures
Using the nested query to ensure conditions apply to the SAME experience object
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

def test_nested_elasticsearch_query():
    """
    Test using Elasticsearch nested query to find actual Meta departures
    This should properly filter for the SAME experience having both conditions
    """
    
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("[ERROR] No API_KEY found in .env file")
        return
    
    print("\n" + "="*60)
    print("TESTING ELASTICSEARCH NESTED QUERY FOR META DEPARTURES")
    print("="*60)
    
    # Calculate date for 90 days ago
    departure_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    print(f"\nLooking for people who LEFT Meta after: {departure_date}")
    print("Using NESTED query to ensure same experience has both conditions")
    
    # PDL REST API endpoint
    url = "https://api.peopledatalabs.com/v5/person/search"
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Elasticsearch query with nested
    es_query = {
        "size": 5,  # Using 5 credits for test
        "query": {
            "bool": {
                "must": [
                    # NESTED query - ensures same experience has both conditions
                    {
                        "nested": {
                            "path": "experience",
                            "query": {
                                "bool": {
                                    "must": [
                                        {
                                            "term": {
                                                "experience.company.name": "meta"
                                            }
                                        },
                                        {
                                            "range": {
                                                "experience.end_date": {
                                                    "gte": departure_date
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    # Not currently at Meta
                    {
                        "bool": {
                            "must_not": {
                                "term": {
                                    "job_company_name": "meta"
                                }
                            }
                        }
                    },
                    # Senior/technical roles
                    {
                        "bool": {
                            "should": [
                                {
                                    "terms": {
                                        "job_title_role": ["engineering", "research", "product", "design", "management"]
                                    }
                                },
                                {
                                    "terms": {
                                        "job_title_levels": ["senior", "lead", "principal", "staff", "director", "vp"]
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        }
    }
    
    print("\n[ELASTICSEARCH NESTED QUERY]")
    print(json.dumps(es_query, indent=2))
    
    print("\n[EXECUTING] Sending nested query to PDL...")
    
    response = requests.post(url, headers=headers, json=es_query)
    
    print(f"\n[RESPONSE] Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        records = data.get('data', [])
        total = data.get('total', 0)
        
        print(f"[SUCCESS] Retrieved {len(records)} records")
        print(f"Total available: {total}")
        
        if records:
            print("\n[VERIFYING RESULTS]")
            print("Checking if these are ACTUAL Meta departures...")
            print("-"*40)
            
            verified_count = 0
            
            for i, person in enumerate(records, 1):
                name = person.get('full_name', 'Unknown')
                current_company = person.get('job_company_name', 'Unknown')
                
                print(f"\n{i}. {name}")
                print(f"   Current: {person.get('job_title', 'Unknown')} @ {current_company}")
                
                # Verify Meta departure
                meta_found = False
                for exp in person.get('experience', []):
                    if isinstance(exp, dict):
                        company = exp.get('company', {})
                        if isinstance(company, dict):
                            company_name = (company.get('name', '') or '').lower()
                            if 'meta' in company_name or 'facebook' in company_name:
                                end_date = exp.get('end_date')
                                if end_date:
                                    print(f"   LEFT Meta: {end_date} ✓")
                                    meta_found = True
                                    verified_count += 1
                                else:
                                    print(f"   Still at Meta (no end_date)")
                                break
                
                if not meta_found:
                    print(f"   WARNING: No Meta departure found in experience!")
            
            print("\n" + "="*60)
            print(f"RESULTS SUMMARY:")
            print(f"  Records returned: {len(records)}")
            print(f"  Verified Meta departures: {verified_count}")
            print(f"  Accuracy: {verified_count}/{len(records)} = {verified_count/len(records)*100:.0f}%")
            
            if verified_count == len(records):
                print("\n[SUCCESS!] Nested query worked perfectly!")
                print("All returned records are actual Meta departures.")
            else:
                print("\n[PARTIAL SUCCESS] Some false positives still present")
                print("The nested query helped but didn't eliminate all issues")
                
        else:
            print("\n[NO RESULTS] The nested query returned no records")
            print("This could mean:")
            print("1. No one left Meta in the last 90 days (unlikely)")
            print("2. The nested query syntax isn't supported as expected")
            
    else:
        error_data = response.json()
        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
        
        print(f"[ERROR] Query failed")
        print(f"Message: {error_msg}")
        
        # Check if it's a syntax error
        if 'nested' in error_msg.lower() or 'query' in error_msg.lower():
            print("\n[IMPORTANT] The nested query syntax may not be supported!")
            print("PDL might not support Elasticsearch nested queries despite using ES syntax")
            
        print("\nFull error response:")
        print(json.dumps(error_data, indent=2))
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    if response.status_code == 200:
        print("- The nested query executed successfully")
        print(f"- Accuracy: {verified_count}/{len(records) if records else 1} departures verified")
    else:
        print("- The nested query failed - PDL may not support this syntax")
        print("- We need to stick with the fetch + local filter approach")
    print("="*60)

def test_alternative_formats():
    """
    Test alternative query formats that might work
    """
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        return
    
    print("\n\n[TESTING ALTERNATIVE FORMATS]")
    print("="*60)
    
    url = "https://api.peopledatalabs.com/v5/person/search"
    headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
    
    departure_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    # Try a simpler combined query
    print("\n[ALTERNATIVE 1] Simple combined term query")
    
    alt_query = {
        "size": 2,
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
    
    print(json.dumps(alt_query, indent=2))
    
    response = requests.post(url, headers=headers, json=alt_query)
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data.get('data', []))} records")
    else:
        print(f"Failed: {response.status_code}")

if __name__ == "__main__":
    print("\nThis test will use 5-7 PDL credits")
    print("It tests if Elasticsearch nested queries work with PDL")
    confirm = input("\nProceed? (y/n): ")
    if confirm.lower() == 'y':
        test_nested_elasticsearch_query()
        
        print("\n\nTest alternative formats too? (uses 2 more credits)")
        if input("(y/n): ").lower() == 'y':
            test_alternative_formats()
    else:
        print("Cancelled")