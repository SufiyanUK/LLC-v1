"""
UPDATED Query Builder for AI/ML Founder Detection
IMPROVEMENTS:
- Added seniority level filters (senior, staff, principal, director, vp)
- Enhanced stealth detection with company size and founding year
- Added technical skill requirements (LLM, PyTorch, TensorFlow)
- Improved timing filters with profile update tracking
- Added co-founder pattern detection
"""

import json
from datetime import datetime, timedelta

# Target companies configuration
AI_FOCUSED_BIG_TECH = [
    "google", "deepmind", "alphabet",
    "openai", "anthropic", 
    "meta", "facebook",
    "microsoft", 
    "nvidia",
    "amazon",
    "apple",
    "tesla",
    "uber",
    "netflix"
]

# AI/ML roles and subroles
AI_ML_ROLES = ["research", "engineering", "product", "analyst"]

AI_ML_SUBROLES = [
    "data_science",
    "data_engineering", 
    "scientific",
    "data_analyst",
    "software",
    "product_management"
]

# NEW: Technical skills for founders
FOUNDER_TECHNICAL_SKILLS = [
    "machine learning",
    "deep learning", 
    "llm",
    "large language models",
    "pytorch",
    "tensorflow",
    "generative ai",
    "transformer",
    "gpt",
    "computer vision",
    "nlp",
    "reinforcement learning"
]

# NEW: Seniority indicators
SENIORITY_LEVELS = [
    "senior",
    "staff", 
    "principal",
    "director",
    "vp",
    "vice president",
    "head",
    "chief",
    "lead"
]

# Exclude these subroles
EXCLUDE_SUBROLES = [
    "administrative",
    "hair_stylist",
    "dental",
    "nursing",
    "retail",
    "restaurants", 
    "warehouse",
    "transport"
]

def build_founder_query(companies=None, query_type="high_potential"):
    """
    Build PDL query for finding potential AI founders
    
    Query Types:
    - high_potential: Senior people with recent departures and stealth signals
    - recent_departures: People who left in last 90 days  
    - stealth_founders: People with founder/building signals
    - technical_experts: People with strong AI/ML skills
    """
    
    if companies is None:
        companies = AI_FOCUSED_BIG_TECH
    
    # Base query structure
    query = {
        "query": {
            "bool": {
                "must": [],
                "should": [],
                "must_not": []
            }
        }
    }
    
    # Time calculations
    last_30_days = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    last_90_days = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    last_180_days = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    if query_type == "high_potential":
        # UPDATED: Most likely founders - senior, recent departure, small company
        query["query"]["bool"]["must"] = [
            {
                "bool": {
                    "should": [
                        {"term": {"experience.company.name": company}} 
                        for company in companies
                    ]
                }
            },
            {
                "range": {
                    "experience.end_date": {
                        "gte": last_90_days
                    }
                }
            }
        ]
        
        # NEW: Must be senior level
        query["query"]["bool"]["should"] = [
            {"term": {"experience.title.levels": level}}
            for level in SENIORITY_LEVELS
        ]
        
        # NEW: Prefer small companies or stealth
        query["query"]["bool"]["should"].extend([
            {"term": {"job_company_size": "1-10"}},
            {"term": {"job_company_size": "11-50"}},
            {"wildcard": {"job_company_name": "*stealth*"}},
            {"wildcard": {"job_company_name": "*labs*"}},
            {"wildcard": {"job_title": "*founder*"}},
            {"wildcard": {"job_title": "*ceo*"}},
            {"wildcard": {"job_title": "*cto*"}}
        ])
        
    elif query_type == "recent_departures":
        # UPDATED: Very recent departures with profile updates
        query["query"]["bool"]["must"] = [
            {
                "bool": {
                    "should": [
                        {"term": {"experience.company.name": company}}
                        for company in companies
                    ]
                }
            },
            {
                "range": {
                    "job_last_changed": {
                        "gte": last_30_days  # Changed from 180 to 30 days
                    }
                }
            },
            {
                "range": {
                    "job_last_updated": {  # NEW: Profile recently updated
                        "gte": last_30_days
                    }
                }
            }
        ]
        
        # NEW: Not at same big company
        query["query"]["bool"]["must_not"] = [
            {"term": {"job_company_name": company}}
            for company in companies
        ]
        
    elif query_type == "stealth_founders":
        # UPDATED: Clear founder signals
        query["query"]["bool"]["must"] = [
            {
                "bool": {
                    "should": [
                        {"term": {"experience.company.name": company}}
                        for company in companies
                    ]
                }
            }
        ]
        
        # NEW: Strong founder indicators
        query["query"]["bool"]["should"] = [
            {"match": {"job_company_name": "stealth"}},
            {"match": {"job_company_name": "building"}},
            {"match": {"job_company_name": "new venture"}},
            {"match": {"job_company_name": "labs"}},
            {"match": {"job_company_name": "research"}},
            {"match": {"job_title": "founder"}},
            {"match": {"job_title": "co-founder"}},
            {"match": {"job_title": "founding engineer"}},
            {"match": {"job_title": "technical co-founder"}},
            {"match": {"job_title": "ceo"}},
            {"match": {"job_title": "cto"}},
            {"match": {"job_title": "building"}},
            {"match": {"job_title": "0 to 1"}}  # NEW: Early stage indicator
        ]
        
        # NEW: Small company and recent founding
        query["query"]["bool"]["must"].append({
            "bool": {
                "should": [
                    {"term": {"job_company_size": "1-10"}},
                    {"term": {"job_company_size": "11-50"}},
                    {"range": {"job_company_founded": {"gte": "2022"}}}  # NEW
                ]
            }
        })
        
    elif query_type == "technical_experts":
        # NEW: Technical founders with AI expertise
        query["query"]["bool"]["must"] = [
            {
                "bool": {
                    "should": [
                        {"term": {"experience.company.name": company}}
                        for company in companies
                    ]
                }
            },
            {
                "range": {
                    "experience.end_date": {
                        "gte": last_180_days
                    }
                }
            }
        ]
        
        # NEW: Must have AI/ML skills
        query["query"]["bool"]["should"] = [
            {"term": {"skills": skill}}
            for skill in FOUNDER_TECHNICAL_SKILLS
        ]
        
        # NEW: Senior technical roles
        query["query"]["bool"]["should"].extend([
            {"term": {"experience.title.levels": "senior"}},
            {"term": {"experience.title.levels": "staff"}},
            {"term": {"experience.title.levels": "principal"}},
            {"term": {"experience.title.levels": "lead"}}
        ])
    
    # Always exclude non-relevant roles
    query["query"]["bool"]["must_not"] = [
        {"term": {"experience.title.sub_role": role}}
        for role in EXCLUDE_SUBROLES
    ]
    
    return query

def build_simple_sql_query(companies=None, query_type="high_potential"):
    """
    Build SQL-style query string for PDL API
    Using proper PDL SQL syntax
    """
    
    if companies is None:
        companies = AI_FOCUSED_BIG_TECH
    
    # Build company list for SQL IN clause
    company_list = ', '.join([f"'{c}'" for c in companies])
    
    # Time calculations
    last_30_days = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    last_90_days = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    if query_type == "high_potential":
        # UPDATED: Using proper PDL SQL syntax
        query = f"""
        SELECT * FROM person 
        WHERE experience.company.name IN ({company_list})
        AND experience.end_date >= '{last_90_days}'
        AND (
            experience.title.levels IN ('senior', 'staff', 'principal', 'director', 'vp', 'head')
            OR job_title_levels IN ('senior', 'staff', 'principal', 'director', 'vp', 'head')
        )
        AND (
            job_company_size IN ('1-10', '11-50')
            OR job_company_name ILIKE '%stealth%'
            OR job_title ILIKE '%founder%'
            OR job_title ILIKE '%co-founder%'
        )
        """
        
    elif query_type == "recent_departures":
        # UPDATED: Using proper PDL SQL syntax
        query = f"""
        SELECT * FROM person 
        WHERE experience.company.name IN ({company_list})
        AND job_last_changed >= '{last_30_days}'
        AND job_company_name NOT IN ({company_list})
        """
        
    elif query_type == "stealth_founders":
        # UPDATED: Using proper PDL SQL syntax
        query = f"""
        SELECT * FROM person 
        WHERE experience.company.name IN ({company_list})
        AND (
            job_company_name ILIKE '%stealth%'
            OR job_company_name ILIKE '%building%'
            OR job_company_name ILIKE '%new venture%'
            OR job_title ILIKE '%founder%'
            OR job_title ILIKE '%co-founder%'
            OR job_title ILIKE '%ceo%'
            OR job_title ILIKE '%cto%'
        )
        AND job_company_size IN ('1-10', '11-50')
        """
        
    elif query_type == "technical_experts":
        # NEW: AI/ML experts who left recently
        skills_list = ', '.join([f"'{s}'" for s in FOUNDER_TECHNICAL_SKILLS[:5]])
        query = f"""
        SELECT * FROM person 
        WHERE experience.company.name IN ({company_list})
        AND experience.end_date >= '{last_90_days}'
        AND skills IN ({skills_list})
        AND (
            experience.title.levels IN ('senior', 'staff', 'principal', 'lead')
            OR job_title_levels IN ('senior', 'staff', 'principal', 'lead')
        )
        """
    
    else:
        # Default fallback
        query = f"""
        SELECT * FROM person 
        WHERE experience.company.name IN ({company_list})
        """
    
    return query.strip()

def get_optimal_query_sequence(total_budget=100):
    """
    NEW: Get optimal query sequence based on API credit budget
    Returns list of (query_type, credits_to_use) tuples
    """
    
    if total_budget <= 10:
        # Very limited budget - focus on highest signals
        return [
            ("high_potential", total_budget)
        ]
    
    elif total_budget <= 50:
        # Moderate budget - cover key patterns
        return [
            ("high_potential", total_budget * 0.4),
            ("stealth_founders", total_budget * 0.3),
            ("recent_departures", total_budget * 0.3)
        ]
    
    else:
        # Good budget - comprehensive search
        return [
            ("high_potential", total_budget * 0.3),
            ("stealth_founders", total_budget * 0.25),
            ("recent_departures", total_budget * 0.25),
            ("technical_experts", total_budget * 0.2)
        ]

# Test the query builder
if __name__ == "__main__":
    # Test different query types
    query_types = ["high_potential", "recent_departures", "stealth_founders", "technical_experts"]
    
    print("UPDATED QUERY EXAMPLES")
    print("=" * 80)
    
    for qtype in query_types:
        print(f"\n{qtype.upper()} Query:")
        print("-" * 40)
        
        # Build SQL-style query (simpler to read)
        sql_query = build_simple_sql_query(
            companies=["openai", "anthropic", "google"],
            query_type=qtype
        )
        print(sql_query)
    
    print("\n" + "=" * 80)
    print("OPTIMAL QUERY SEQUENCE FOR DIFFERENT BUDGETS:")
    print("-" * 40)
    
    for budget in [10, 50, 100]:
        sequence = get_optimal_query_sequence(budget)
        print(f"\nBudget: {budget} credits")
        for query_type, credits in sequence:
            print(f"  - {query_type}: {credits:.0f} credits")