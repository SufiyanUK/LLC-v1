"""
UPDATED Founder Qualification Module
IMPROVEMENTS:
- Increased weight for very recent departures (2024 Q3/Q4 gets 4 points)
- Added startup readiness signals (previous startup experience)
- Enhanced AI/ML skill detection with LLM/GenAI focus
- Added network effects (worked with other high scorers)
- Raised minimum threshold to 4.5 for better precision
- Added co-founder pattern detection
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

def safe_string_get(obj, key, default=''):
    """Safely get string value from dict"""
    if not isinstance(obj, dict):
        return default
    value = obj.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        return str(value) if value else default
    return value.strip()

def safe_list_get(obj, key, default=None):
    """Safely get list value from dict"""
    if default is None:
        default = []
    if not isinstance(obj, dict):
        return default
    value = obj.get(key, default)
    if not isinstance(value, list):
        return default
    return value

def calculate_founder_potential_score(employee, other_employees=None):
    """
    UPDATED: Score employee based on founder potential (0-10 scale)
    Now includes startup readiness and network effects
    """
    if not isinstance(employee, dict):
        return 0
    
    score = 0
    current_date = datetime.now()
    
    # 1. UPDATED: Recent departure (0-4 points) - Increased weight
    departure = employee.get('last_big_tech_departure')
    if departure and isinstance(departure, dict):
        departure_date = departure.get('departure_date', '')
        if departure_date:
            # Parse departure date
            try:
                dep_date = datetime.strptime(departure_date[:10], '%Y-%m-%d')
                months_since = (current_date - dep_date).days / 30
                
                if months_since <= 3:  # Last 3 months
                    score += 4
                elif months_since <= 6:  # Last 6 months  
                    score += 3.5
                elif months_since <= 9:  # Q1/Q2 2024
                    score += 3
                elif months_since <= 12:  # Within a year
                    score += 2.5
                elif months_since <= 24:  # 2023
                    score += 2
                else:
                    score += 1
            except:
                # Fallback to string comparison
                if departure_date >= '2024-07':  # Q3/Q4 2024
                    score += 4
                elif departure_date >= '2024-01':  # Q1/Q2 2024
                    score += 3
                elif departure_date >= '2023-01':
                    score += 2
                elif departure_date >= '2022-01':
                    score += 1.5
    
    # 2. Role/Experience (0-2 points) - Same as before
    last_role = employee.get('last_known_role') or {}
    role = safe_string_get(last_role, 'role').lower()
    sub_role = safe_string_get(last_role, 'sub_role').lower()
    
    if role in ['engineering', 'research', 'product'] or sub_role in ['data_science', 'data_engineering', 'scientific']:
        score += 2
    elif role in ['analyst', 'sales', 'marketing', 'operations'] or sub_role in ['product_management', 'business_development', 'software']:
        score += 1.5
    elif sub_role in ['account_executive', 'solutions_engineer', 'customer_success']:
        score += 1
    
    # 3. Seniority (0-2 points) - Same as before
    levels = safe_list_get(last_role, 'levels')
    level_strings = [str(level).lower() for level in levels]
    
    if any(level in ['director', 'vp', 'cxo', 'head', 'chief'] for level in level_strings):
        score += 2
    elif any(level in ['senior', 'lead', 'principal', 'staff'] for level in level_strings):  # Added 'staff'
        score += 1.5
    elif any(level in ['manager'] for level in level_strings):
        score += 1
    
    # 4. UPDATED: Technical Skills (0-2 points) - Increased weight for LLM/GenAI
    skills = safe_list_get(employee, 'skills')
    skill_strings = [skill.lower() for skill in skills if isinstance(skill, str)]
    
    # Hot AI/ML skills for 2024
    llm_genai_skills = [
        'llm', 'large language model', 'gpt', 'generative ai', 'transformer',
        'prompt engineering', 'langchain', 'vector database', 'rag', 'fine-tuning'
    ]
    
    # Traditional AI/ML skills
    ai_ml_skills = [
        'machine learning', 'artificial intelligence', 'deep learning',
        'data science', 'neural networks', 'computer vision', 'nlp',
        'tensorflow', 'pytorch', 'scikit-learn'
    ]
    
    # Infrastructure skills (important for founders)
    infra_skills = [
        'kubernetes', 'docker', 'aws', 'gcp', 'azure', 'devops',
        'microservices', 'distributed systems', 'scaling'
    ]
    
    llm_skill_count = sum(1 for skill in llm_genai_skills if any(s in skill_str for skill_str in skill_strings for s in [skill]))
    ai_skill_count = sum(1 for skill in ai_ml_skills if any(s in skill_str for skill_str in skill_strings for s in [skill]))
    infra_skill_count = sum(1 for skill in infra_skills if any(s in skill_str for skill_str in skill_strings for s in [skill]))
    
    if llm_skill_count >= 2:  # NEW: LLM expertise highly valued
        score += 2
    elif llm_skill_count >= 1 and (ai_skill_count >= 1 or infra_skill_count >= 1):
        score += 1.75
    elif ai_skill_count >= 2:
        score += 1.5
    elif ai_skill_count >= 1 or infra_skill_count >= 2:
        score += 1
    elif infra_skill_count >= 1:
        score += 0.5
    
    # 5. Location (0-1 point) - Same as before
    location = employee.get('location') or {}
    job_location = location.get('job_location') or {}
    region = safe_string_get(job_location, 'region').lower()
    locality = safe_string_get(job_location, 'locality').lower()
    
    tier1_regions = ['california', 'washington']
    tier1_cities = ['san francisco', 'palo alto', 'mountain view', 'seattle', 'bellevue', 'menlo park']
    tier2_regions = ['new york', 'texas', 'massachusetts', 'colorado']
    tier2_cities = ['new york', 'austin', 'boston', 'cambridge', 'brooklyn', 'denver', 'boulder']
    
    if region in tier1_regions or any(city in locality for city in tier1_cities):
        score += 1
    elif region in tier2_regions or any(city in locality for city in tier2_cities):
        score += 0.5
    
    # 6. Education (0-1 point) - Same as before
    education = safe_list_get(employee, 'education')
    top_schools = [
        'stanford', 'mit', 'harvard', 'berkeley', 'carnegie mellon',
        'georgia tech', 'caltech', 'university of washington',
        'princeton', 'yale', 'columbia', 'cornell', 'oxford', 'cambridge'
    ]
    
    for edu in education:
        if isinstance(edu, dict):
            school = safe_string_get(edu, 'school').lower()
            if any(top_school in school for top_school in top_schools):
                score += 1
                break
    
    # 7. NEW: Startup Readiness (0-1.5 points)
    experiences = employee.get('experience', [])
    startup_experience = False
    previous_founder = False
    rapid_growth_exp = False
    
    for exp in experiences:
        if isinstance(exp, dict):
            company_data = exp.get('company', {})
            if isinstance(company_data, dict):
                company_size = company_data.get('size', '')
                company_name = safe_string_get(company_data, 'name').lower()
                title = safe_string_get(exp, 'title').lower()
                
                # Previous startup experience
                if company_size in ['1-10', '11-50', '51-200']:
                    startup_experience = True
                
                # Previous founder/co-founder
                if 'founder' in title or 'co-founder' in title:
                    previous_founder = True
                
                # Experience at high-growth companies
                high_growth = ['stripe', 'airbnb', 'uber', 'lyft', 'doordash', 'coinbase', 'robinhood']
                if any(hg in company_name for hg in high_growth):
                    rapid_growth_exp = True
    
    if previous_founder:
        score += 1.5
    elif startup_experience and rapid_growth_exp:
        score += 1
    elif startup_experience or rapid_growth_exp:
        score += 0.5
    
    # 8. NEW: Network Effects (0-1 point)
    if other_employees:
        # Check if worked with other high-scoring employees
        employee_companies = set()
        for exp in experiences:
            if isinstance(exp, dict):
                company_data = exp.get('company', {})
                if isinstance(company_data, dict):
                    company_name = safe_string_get(company_data, 'name').lower()
                    if company_name:
                        employee_companies.add(company_name)
        
        # Count connections with other potential founders
        connections = 0
        for other in other_employees:
            if other.get('pdl_id') != employee.get('pdl_id'):
                other_score = other.get('founder_score', 0)
                if other_score >= 6:  # Other person is high potential
                    other_experiences = other.get('experience', [])
                    for exp in other_experiences:
                        if isinstance(exp, dict):
                            company_data = exp.get('company', {})
                            if isinstance(company_data, dict):
                                other_company = safe_string_get(company_data, 'name').lower()
                                if other_company in employee_companies:
                                    connections += 1
                                    break
        
        if connections >= 3:
            score += 1
        elif connections >= 2:
            score += 0.75
        elif connections >= 1:
            score += 0.5
    
    return round(min(score, 10), 1)  # Cap at 10

def get_founder_qualification_reasons(employee):
    """
    UPDATED: More detailed qualification reasons
    """
    reasons = []
    
    # Departure info
    departure = employee.get('last_big_tech_departure')
    if departure and isinstance(departure, dict):
        company = departure.get('company')
        date = departure.get('departure_date')
        if company and date:
            try:
                dep_date = datetime.strptime(date[:10], '%Y-%m-%d')
                months_ago = (datetime.now() - dep_date).days / 30
                if months_ago <= 3:
                    reasons.append(f"Very recently left {company} ({int(months_ago)} months ago)")
                else:
                    reasons.append(f"Left {company} in {date[:7]}")
            except:
                reasons.append(f"Left {company}")
    
    # Current status
    current_company = (employee.get('job_company_name') or '').lower()
    current_title = (employee.get('job_title') or '').lower()
    
    if 'stealth' in current_company or 'building' in current_company:
        reasons.append(f"Currently at: {employee.get('job_company_name', 'stealth/building')}")
    elif 'founder' in current_title or 'co-founder' in current_title:
        reasons.append(f"Current role: {employee.get('job_title', 'founder role')}")
    
    # Technical expertise
    skills = safe_list_get(employee, 'skills')
    llm_skills = [s for s in skills if any(term in s.lower() for term in ['llm', 'gpt', 'generative', 'transformer'])]
    if llm_skills:
        reasons.append(f"LLM/GenAI expertise: {', '.join(llm_skills[:2])}")
    
    # Seniority
    last_role = employee.get('last_known_role') or {}
    levels = safe_list_get(last_role, 'levels')
    if any(level in str(levels).lower() for level in ['director', 'vp', 'chief', 'principal', 'staff']):
        reasons.append(f"Senior level: {', '.join(str(l) for l in levels[:2])}")
    
    # Previous startup experience
    experiences = employee.get('experience', [])
    for exp in experiences:
        if isinstance(exp, dict):
            title = safe_string_get(exp, 'title').lower()
            if 'founder' in title:
                company = exp.get('company', {}).get('name', 'previous company')
                reasons.append(f"Previous founder at {company}")
                break
    
    return reasons[:5]  # Top 5 reasons

def qualify_potential_founders(processed_employees, min_score=4.5):
    """
    UPDATED: Higher threshold (4.5) and network effect analysis
    """
    potential_founders = []
    
    print(f"Analyzing {len(processed_employees)} employees for founder potential...")
    print(f"Using minimum score threshold: {min_score}")
    
    # First pass - calculate initial scores
    for employee in processed_employees:
        score = calculate_founder_potential_score(employee)
        employee['founder_score'] = score
    
    # Second pass - add network effects
    for employee in processed_employees:
        score_with_network = calculate_founder_potential_score(employee, processed_employees)
        employee['founder_score'] = score_with_network
    
    # Score distribution
    score_distribution = {
        '0-2': 0, '2-4': 0, '4-4.5': 0, '4.5-6': 0, 
        '6-8': 0, '8-10': 0
    }
    
    for employee in processed_employees:
        score = employee.get('founder_score', 0)
        
        if score < 2:
            score_distribution['0-2'] += 1
        elif score < 4:
            score_distribution['2-4'] += 1
        elif score < 4.5:
            score_distribution['4-4.5'] += 1
        elif score < 6:
            score_distribution['4.5-6'] += 1
        elif score < 8:
            score_distribution['6-8'] += 1
        else:
            score_distribution['8-10'] += 1
        
        if score >= min_score:
            employee_copy = employee.copy()
            employee_copy['qualification_reasons'] = get_founder_qualification_reasons(employee)
            potential_founders.append(employee_copy)
    
    # Sort by score
    potential_founders.sort(key=lambda x: x['founder_score'], reverse=True)
    
    # Detect co-founder patterns
    cofounder_groups = detect_cofounder_patterns(potential_founders)
    
    # Print analysis
    print(f"\nFounder Score Distribution:")
    for range_key, count in score_distribution.items():
        print(f"  {range_key}: {count} employees")
    
    print(f"\n✅ Qualified {len(potential_founders)} employees as potential founders (score >= {min_score})")
    
    if cofounder_groups:
        print(f"\n🤝 Detected {len(cofounder_groups)} potential co-founder groups")
    
    return potential_founders, cofounder_groups

def detect_cofounder_patterns(founders):
    """
    NEW: Detect groups of people who might be co-founders
    """
    cofounder_groups = []
    
    # Group by departure time and company
    departure_groups = {}
    
    for founder in founders:
        departure = founder.get('last_big_tech_departure', {})
        if departure:
            company = departure.get('company', '')
            date = departure.get('departure_date', '')[:7]  # Year-month
            
            key = f"{company}_{date}"
            if key not in departure_groups:
                departure_groups[key] = []
            departure_groups[key].append(founder)
    
    # Find groups with 2+ people
    for key, group in departure_groups.items():
        if len(group) >= 2:
            # Check if they went to similar places
            current_companies = [f.get('job_company_name', '').lower() for f in group]
            
            # Similar destination (stealth, small company, etc)
            if any(c in ['stealth', 'building', 'new venture'] for c in current_companies):
                cofounder_groups.append({
                    'pattern': key,
                    'founders': [f.get('full_name', 'Unknown') for f in group],
                    'scores': [f.get('founder_score', 0) for f in group],
                    'current_companies': current_companies
                })
    
    return cofounder_groups

def process_potential_founders():
    """Main processing function"""
    print("=== UPDATED FOUNDER QUALIFICATION ===")
    
    INPUT_DIRECTORY = r'data\processed\pdl_employees'
    OUTPUT_FILE = r'data\processed\potential_founders_updated.json'
    min_score = 4.5  # UPDATED: Higher threshold
    
    if not os.path.exists(INPUT_DIRECTORY):
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIRECTORY}")
    
    jsonl_files = [
        os.path.join(INPUT_DIRECTORY, filename)
        for filename in os.listdir(INPUT_DIRECTORY)
        if filename.endswith('.jsonl')
    ]
    
    if not jsonl_files:
        raise ValueError(f"No JSONL files found in {INPUT_DIRECTORY}")
    
    print(f"Found {len(jsonl_files)} JSONL files to process")
    
    # Load all employees
    all_processed_employees = []
    
    for file_path in jsonl_files:
        print(f"Loading {os.path.basename(file_path)}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            employee = json.loads(line.strip())
                            all_processed_employees.append(employee)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"  Error loading {file_path}: {e}")
            continue
    
    print(f"\nTotal employees loaded: {len(all_processed_employees)}")
    
    # Qualify founders with network analysis
    qualified_founders, cofounder_groups = qualify_potential_founders(
        all_processed_employees, 
        min_score
    )
    
    # Save results
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    results = {
        'qualified_founders': qualified_founders,
        'cofounder_patterns': cofounder_groups,
        'statistics': {
            'total_analyzed': len(all_processed_employees),
            'qualified_count': len(qualified_founders),
            'qualification_rate': f"{len(qualified_founders)/len(all_processed_employees)*100:.1f}%",
            'cofounder_groups': len(cofounder_groups)
        }
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)
    
    print(f"\nSaved results to {OUTPUT_FILE}")
    
    # Print top founders
    print(f"\nTop 10 Potential Founders:")
    for i, founder in enumerate(qualified_founders[:10], 1):
        print(f"{i}. {founder.get('full_name', 'Unknown')} (Score: {founder['founder_score']})")
        for reason in founder.get('qualification_reasons', [])[:2]:
            print(f"   - {reason}")
    
    return results

if __name__ == "__main__":
    results = process_potential_founders()