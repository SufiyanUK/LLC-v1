"""
Test Updated System with OpenAI Employees - 10 Credits Only
Uses the updated query logic, founder qualifier, and stealth detector
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

# Import PDL client
from src.data_collection.pdl_client import get_pdl_client

# Import UPDATED modules
from src.utils.query_updated import build_founder_query, get_optimal_query_sequence
from src.data_processing.founder_qualifier_updated import calculate_founder_potential_score, qualify_potential_founders
from src.monitoring.stealth_detector_updated import StealthFounderDetector

def main():
    """Run the updated pipeline with 10 credits on OpenAI employees"""
    
    print("="*80)
    print("TESTING UPDATED SYSTEM - OPENAI EMPLOYEES - 10 CREDITS")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80)
    
    # Load environment and check API key
    load_dotenv()
    if not os.getenv('API_KEY'):
        print("❌ No API_KEY found in .env file!")
        print("Please add: API_KEY=your_pdl_api_key")
        sys.exit(1)
    
    # Initialize PDL client
    client = get_pdl_client()
    
    # Configuration
    TOTAL_CREDITS = 10
    TARGET_COMPANY = "openai"
    
    # Create output directories
    os.makedirs('data/raw/updated_test', exist_ok=True)
    os.makedirs('data/processed/updated_test', exist_ok=True)
    os.makedirs('data/results/updated_test', exist_ok=True)
    
    print(f"\n📍 Target Company: {TARGET_COMPANY.upper()}")
    print(f"💳 Budget: {TOTAL_CREDITS} API credits")
    
    # STEP 1: Build Query using updated logic
    print("\n" + "="*60)
    print("STEP 1: BUILDING QUERY WITH UPDATED LOGIC")
    print("="*60)
    
    # Get optimal query sequence for 10 credits
    query_sequence = get_optimal_query_sequence(TOTAL_CREDITS)
    print("\nOptimal query strategy for 10 credits:")
    for query_type, credits in query_sequence:
        print(f"  - {query_type}: {credits:.0f} credits")
    
    # Since we have 10 credits, we'll use high_potential query
    query_type = "high_potential"
    
    # Build the JSON query object (Elasticsearch format)
    json_query = build_founder_query(
        companies=[TARGET_COMPANY],
        query_type=query_type
    )
    
    print(f"\nUsing query type: {query_type.upper()}")
    print(f"Query structure: Elasticsearch JSON format")
    
    # STEP 2: Fetch employees from PDL
    print("\n" + "="*60)
    print("STEP 2: FETCHING EMPLOYEES FROM PDL")
    print("="*60)
    
    # Check if raw data already exists from previous run
    raw_file = f'data/raw/updated_test/openai_{query_type}_{TOTAL_CREDITS}credits_raw.jsonl'
    
    if os.path.exists(raw_file):
        print(f"\n⚠️ Raw data already exists at: {raw_file}")
        print("Loading existing data instead of making new API call...")
        
        employees = []
        with open(raw_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    employees.append(json.loads(line.strip()))
        
        print(f"✅ Loaded {len(employees)} employees from existing file")
        print("💰 No API credits consumed!")
        
    else:
        # PDL API expects a JSON query object in Elasticsearch format
        params = {
            'query': json_query,  # Use the JSON query object
            'size': TOTAL_CREDITS,  # Use all 10 credits
            'pretty': True
        }
        
        print(f"\nSending request to PDL API...")
        print(f"  - Query type: {query_type}")
        print(f"  - Max results: {TOTAL_CREDITS}")
        
        response_confirm = input("\n⚠️ This will consume 10 API credits. Continue? (yes/no): ")
        if response_confirm.lower() != 'yes':
            print("Aborted by user")
            sys.exit(0)
        
        try:
            response = client.person.search(**params)
            
            if response.status_code == 200:
                data = response.json()
                employees = data.get('data', [])
                total_found = data.get('total', 0)
                
                print(f"\n✅ API call successful!")
                print(f"  - Total matching profiles in PDL: {total_found:,}")
                print(f"  - Fetched with 10 credits: {len(employees)}")
                
                # Save raw data immediately
                os.makedirs('data/raw/updated_test', exist_ok=True)
                with open(raw_file, 'w', encoding='utf-8') as f:
                    for emp in employees:
                        f.write(json.dumps(emp) + '\n')
                print(f"\n💾 Saved raw data to: {raw_file}")
                
            else:
                print(f"\n❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                sys.exit(1)
                
        except Exception as e:
            print(f"\n❌ Error calling PDL API: {e}")
            sys.exit(1)
    
    # STEP 3: Process employees to extract relevant data
    print("\n" + "="*60)
    print("STEP 3: PROCESSING EMPLOYEE DATA")
    print("="*60)
    
    # Import the individual processing functions
    from src.data_processing.employee_processor import (
        extract_location, get_current_company, get_previous_companies,
        get_last_role, get_last_big_tech_departure, extract_education
    )
    from config.companies import AI_FOCUSED_BIG_TECH
    
    processed_employees = []
    for emp in employees:
        # Process each employee directly
        processed = {
            'pdl_id': emp.get('id'),
            'full_name': emp.get('full_name'),
            'first_name': emp.get('first_name'), 
            'last_name': emp.get('last_name'),
            'location': extract_location(emp),
            'current_company': get_current_company(emp),
            'previous_companies': get_previous_companies(emp),
            'last_known_role': get_last_role(emp),
            'last_big_tech_departure': get_last_big_tech_departure(emp, AI_FOCUSED_BIG_TECH),
            'linkedin_url': emp.get('linkedin_url'),
            'skills': emp.get('skills', []),
            'education': extract_education(emp),
            'job_company_name': emp.get('job_company_name'),
            'job_title': emp.get('job_title'),
            'job_company_size': emp.get('job_company_size'),
            'job_last_changed': emp.get('job_last_changed'),
            'job_last_updated': emp.get('job_last_updated'),
            'job_title_role': emp.get('job_title_role'),
            'job_title_sub_role': emp.get('job_title_sub_role'),
            'experience': emp.get('experience', [])
        }
        processed_employees.append(processed)
    
    print(f"Processed {len(processed_employees)} employees")
    
    # Save processed data
    processed_file = f'data/processed/updated_test/openai_{query_type}_{TOTAL_CREDITS}credits_processed.jsonl'
    with open(processed_file, 'w', encoding='utf-8') as f:
        for emp in processed_employees:
            f.write(json.dumps(emp) + '\n')
    print(f"💾 Saved processed data to: {processed_file}")
    
    # STEP 4: Apply Updated Founder Qualifier
    print("\n" + "="*60)
    print("STEP 4: APPLYING UPDATED FOUNDER QUALIFIER")
    print("="*60)
    
    MIN_SCORE = 4.5  # Updated threshold
    print(f"Using minimum score threshold: {MIN_SCORE}")
    
    # Calculate scores with network effects
    qualified_founders, cofounder_groups = qualify_potential_founders(
        processed_employees, 
        min_score=MIN_SCORE
    )
    
    print(f"\n📊 Founder Qualification Results:")
    print(f"  - Total analyzed: {len(processed_employees)}")
    print(f"  - Qualified founders (score ≥ {MIN_SCORE}): {len(qualified_founders)}")
    print(f"  - Qualification rate: {len(qualified_founders)/len(processed_employees)*100:.1f}%")
    
    if cofounder_groups:
        print(f"  - Potential co-founder groups: {len(cofounder_groups)}")
    
    # Show score distribution
    score_dist = {'<3': 0, '3-4': 0, '4-4.5': 0, '4.5-6': 0, '6-8': 0, '8+': 0}
    for emp in processed_employees:
        score = emp.get('founder_score', 0)
        if score < 3: score_dist['<3'] += 1
        elif score < 4: score_dist['3-4'] += 1  
        elif score < 4.5: score_dist['4-4.5'] += 1
        elif score < 6: score_dist['4.5-6'] += 1
        elif score < 8: score_dist['6-8'] += 1
        else: score_dist['8+'] += 1
    
    print(f"\n📈 Score Distribution:")
    for range_key, count in score_dist.items():
        bar = '█' * (count * 2)  # Simple bar chart
        print(f"  {range_key:8s}: {count:2d} {bar}")
    
    # STEP 5: Apply Updated Stealth Detector
    print("\n" + "="*60)
    print("STEP 5: APPLYING UPDATED STEALTH DETECTOR")
    print("="*60)
    
    detector = StealthFounderDetector()
    
    # Analyze all processed employees (not just qualified)
    stealth_results = detector.analyze_bulk_employees(processed_employees)
    
    print(f"\n🔍 Stealth Detection Results:")
    print(f"  - VIP tier (≥75 score): {stealth_results['stats']['vip_count']}")
    print(f"  - Watch tier (≥40 score): {stealth_results['stats']['watch_count']}")
    print(f"  - General tier: {stealth_results['stats']['general_count']}")
    print(f"  - Average stealth score: {stealth_results['stats'].get('average_score', 0):.1f}")
    print(f"  - Employees with stealth signals (≥50): {stealth_results['stats']['stealth_detected']}")
    
    # STEP 6: Combine Results and Save
    print("\n" + "="*60)
    print("STEP 6: FINAL RESULTS")
    print("="*60)
    
    # Create final results combining founder score and stealth detection
    final_results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'target_company': TARGET_COMPANY,
            'api_credits_used': TOTAL_CREDITS,
            'query_type': query_type,
            'total_fetched': len(employees),
            'total_processed': len(processed_employees)
        },
        'qualified_founders': qualified_founders,
        'cofounder_groups': cofounder_groups,
        'stealth_detection': {
            'vip': stealth_results['vip'],
            'watch': stealth_results['watch'],
            'stats': stealth_results['stats']
        },
        'high_priority_candidates': []  # Founders who are both qualified AND show stealth signals
    }
    
    # Find high priority candidates (qualified + stealth)
    for founder in qualified_founders:
        # Find their stealth score
        for tier in ['vip', 'watch', 'general']:
            for stealth_emp in stealth_results[tier]:
                if stealth_emp['pdl_id'] == founder.get('pdl_id'):
                    if stealth_emp['stealth_score'] >= 50:
                        final_results['high_priority_candidates'].append({
                            'name': founder.get('full_name'),
                            'founder_score': founder.get('founder_score'),
                            'stealth_score': stealth_emp['stealth_score'],
                            'stealth_signals': stealth_emp['signals'][:3],
                            'qualification_reasons': founder.get('qualification_reasons', [])[:3]
                        })
                    break
    
    # Save final results
    results_file = f'data/results/updated_test/openai_final_results_{TOTAL_CREDITS}credits.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2)
    print(f"\n💾 Saved final results to: {results_file}")
    
    # Print top candidates
    print("\n🎯 TOP HIGH-PRIORITY CANDIDATES (Qualified + Stealth Signals):")
    print("-" * 60)
    
    if final_results['high_priority_candidates']:
        for i, candidate in enumerate(final_results['high_priority_candidates'][:5], 1):
            print(f"\n{i}. {candidate['name']}")
            print(f"   Founder Score: {candidate['founder_score']:.1f} | Stealth Score: {candidate['stealth_score']:.0f}")
            print(f"   Qualifications: {', '.join(candidate['qualification_reasons'][:2])}")
            print(f"   Stealth Signals: {', '.join(candidate['stealth_signals'][:2])}")
    else:
        print("No candidates met both qualification and stealth criteria")
    
    # Print top qualified founders (even if no stealth signals)
    if qualified_founders:
        print("\n📋 TOP QUALIFIED FOUNDERS:")
        print("-" * 60)
        for i, founder in enumerate(qualified_founders[:5], 1):
            print(f"{i}. {founder.get('full_name')} (Score: {founder.get('founder_score'):.1f})")
            reasons = founder.get('qualification_reasons', [])
            if reasons:
                print(f"   - {reasons[0]}")
    
    # Print top stealth signals (even if not qualified)
    if stealth_results['vip']:
        print("\n🕵️ TOP STEALTH SIGNALS (VIP Monitoring):")
        print("-" * 60)
        for i, emp in enumerate(stealth_results['vip'][:5], 1):
            print(f"{i}. {emp['full_name']} (Score: {emp['stealth_score']:.0f})")
            if emp['signals']:
                print(f"   - {emp['signals'][0]}")
    
    print("\n" + "="*80)
    print("✅ UPDATED PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"\nSummary:")
    print(f"  - Used {TOTAL_CREDITS} API credits")
    print(f"  - Found {len(qualified_founders)} qualified founders")
    print(f"  - Detected {stealth_results['stats']['stealth_detected']} with stealth signals")
    print(f"  - Identified {len(final_results['high_priority_candidates'])} high-priority candidates")
    
    return final_results

if __name__ == "__main__":
    results = main()