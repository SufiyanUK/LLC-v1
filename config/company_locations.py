"""
Dynamic Company Location Mapping
Based on actual employee distribution patterns
"""

# Primary headquarters and major office locations
COMPANY_HEADQUARTERS = {
    # West Coast - California dominant
    'openai': {
        'hq_state': 'california',
        'hq_city': 'san francisco',
        'major_offices': ['california'],
        'search_priority': ['california', 'washington', 'new york']
    },
    'anthropic': {
        'hq_state': 'california', 
        'hq_city': 'san francisco',
        'major_offices': ['california'],
        'search_priority': ['california']
    },
    'google': {
        'hq_state': 'california',
        'hq_city': 'mountain view', 
        'major_offices': ['california', 'new york', 'washington', 'texas', 'colorado'],
        'search_priority': ['california', 'new york', 'washington']
    },
    'deepmind': {
        'hq_state': 'california',
        'hq_city': 'mountain view',
        'major_offices': ['california', 'london'],
        'search_priority': ['california', 'new york']
    },
    'meta': {
        'hq_state': 'california',
        'hq_city': 'menlo park',
        'major_offices': ['california', 'new york', 'washington', 'texas'],
        'search_priority': ['california', 'new york', 'washington']
    },
    'apple': {
        'hq_state': 'california',
        'hq_city': 'cupertino',
        'major_offices': ['california', 'texas', 'new york'],
        'search_priority': ['california', 'texas']
    },
    'nvidia': {
        'hq_state': 'california',
        'hq_city': 'santa clara',
        'major_offices': ['california', 'texas', 'washington'],
        'search_priority': ['california', 'texas']
    },
    'tesla': {
        'hq_state': 'texas',  # Moved from California
        'hq_city': 'austin',
        'major_offices': ['texas', 'california', 'nevada'],
        'search_priority': ['texas', 'california']
    },
    
    # West Coast - Washington
    'microsoft': {
        'hq_state': 'washington',
        'hq_city': 'redmond',
        'major_offices': ['washington', 'california', 'new york', 'texas'],
        'search_priority': ['washington', 'california']
    },
    'amazon': {
        'hq_state': 'washington',
        'hq_city': 'seattle',
        'major_offices': ['washington', 'virginia', 'california', 'new york', 'texas'],
        'search_priority': ['washington', 'california', 'virginia']
    },
    
    # Other locations
    'uber': {
        'hq_state': 'california',
        'hq_city': 'san francisco',
        'major_offices': ['california', 'new york', 'colorado'],
        'search_priority': ['california', 'new york']
    },
    'netflix': {
        'hq_state': 'california',
        'hq_city': 'los gatos',
        'major_offices': ['california'],
        'search_priority': ['california']
    },
    'adobe': {
        'hq_state': 'california',
        'hq_city': 'san jose',
        'major_offices': ['california', 'utah', 'washington'],
        'search_priority': ['california', 'utah']
    },
    'salesforce': {
        'hq_state': 'california',
        'hq_city': 'san francisco',
        'major_offices': ['california', 'new york', 'texas'],
        'search_priority': ['california', 'new york']
    },
    'oracle': {
        'hq_state': 'texas',  # Moved from California
        'hq_city': 'austin',
        'major_offices': ['texas', 'california', 'colorado'],
        'search_priority': ['texas', 'california']
    },
    'ibm': {
        'hq_state': 'new york',
        'hq_city': 'armonk',
        'major_offices': ['new york', 'texas', 'north carolina', 'california'],
        'search_priority': ['new york', 'texas', 'california']
    },
    'intel': {
        'hq_state': 'california',
        'hq_city': 'santa clara',
        'major_offices': ['california', 'oregon', 'arizona'],
        'search_priority': ['california', 'oregon']
    },
    'huggingface': {
        'hq_state': 'new york',
        'hq_city': 'new york',
        'major_offices': ['new york', 'california'],
        'search_priority': ['new york', 'california']
    }
}

# Tech hub cities by state (where startups cluster)
TECH_HUB_CITIES = {
    'california': [
        # Bay Area
        'san francisco', 'san jose', 'oakland', 'berkeley',
        'palo alto', 'mountain view', 'sunnyvale', 'cupertino',
        'menlo park', 'redwood city', 'san mateo', 'fremont',
        # SoCal
        'los angeles', 'san diego', 'santa monica', 'irvine', 'pasadena'
    ],
    'washington': [
        'seattle', 'bellevue', 'redmond', 'kirkland', 'tacoma', 'spokane'
    ],
    'texas': [
        'austin', 'dallas', 'houston', 'san antonio', 'plano', 'irving'
    ],
    'new york': [
        'new york', 'brooklyn', 'manhattan', 'queens', 'bronx', 'buffalo'
    ],
    'massachusetts': [
        'boston', 'cambridge', 'somerville', 'quincy', 'waltham'
    ],
    'colorado': [
        'denver', 'boulder', 'fort collins', 'colorado springs'
    ],
    'georgia': [
        'atlanta', 'alpharetta', 'sandy springs'
    ],
    'illinois': [
        'chicago', 'evanston', 'schaumburg'
    ],
    'oregon': [
        'portland', 'beaverton', 'hillsboro', 'eugene'
    ],
    'north carolina': [
        'raleigh', 'durham', 'charlotte', 'cary', 'chapel hill'
    ],
    'virginia': [
        'arlington', 'alexandria', 'richmond', 'mclean', 'reston'
    ],
    'pennsylvania': [
        'philadelphia', 'pittsburgh'
    ],
    'florida': [
        'miami', 'orlando', 'tampa', 'fort lauderdale', 'jacksonville'
    ],
    'utah': [
        'salt lake city', 'provo', 'park city', 'lehi'
    ],
    'arizona': [
        'phoenix', 'scottsdale', 'tempe', 'chandler'
    ]
}

# States where companies commonly incorporate (legal, not physical)
INCORPORATION_STATES = [
    'delaware',      # ~60% of Fortune 500
    'nevada',        # Tax benefits
    'wyoming',       # Privacy benefits
    'california',    # If operating there
    'new york',      # If operating there
    'texas'          # Business-friendly
]

# Mapping of incorporation state to likely operating states
INCORPORATION_TO_OPERATION = {
    'delaware': ['california', 'new york', 'texas', 'washington', 'massachusetts'],
    'nevada': ['california', 'texas', 'arizona'],
    'wyoming': ['california', 'colorado', 'texas']
}

def get_search_states_for_company(company_name: str) -> list:
    """
    Get prioritized list of states to search for a company's alumni startups
    """
    company_lower = company_name.lower()
    
    if company_lower in COMPANY_HEADQUARTERS:
        return COMPANY_HEADQUARTERS[company_lower]['search_priority']
    
    # Default to major tech hubs
    return ['california', 'new york', 'texas', 'washington', 'massachusetts']

def get_tech_cities_for_state(state: str) -> list:
    """
    Get list of tech hub cities for a state
    """
    state_lower = state.lower()
    return TECH_HUB_CITIES.get(state_lower, [])

def should_check_delaware(company_state: str) -> bool:
    """
    Determine if we should also check Delaware for incorporations
    """
    # Always check Delaware for companies not already in Delaware
    return company_state.lower() != 'delaware'

def get_geographic_search_strategy(company: str, employee_data: list = None) -> dict:
    """
    Build comprehensive geographic search strategy
    
    Returns:
        {
            'primary_states': [],      # Where employees are
            'incorporation_states': [], # Where companies incorporate
            'tech_hub_cities': [],     # Cities to focus on
            'search_radius_miles': 50  # For proximity matching
        }
    """
    strategy = {
        'company': company,
        'primary_states': get_search_states_for_company(company),
        'incorporation_states': ['delaware'],  # Always check
        'tech_hub_cities': [],
        'search_radius_miles': 50
    }
    
    # Add tech hub cities for primary states
    for state in strategy['primary_states']:
        cities = get_tech_cities_for_state(state)
        strategy['tech_hub_cities'].extend(cities[:5])  # Top 5 cities per state
    
    # If we have actual employee data, refine the strategy
    if employee_data:
        state_counts = {}
        for emp in employee_data:
            state = emp.get('job_company_location_region', '').lower()
            if state:
                state_counts[state] = state_counts.get(state, 0) + 1
        
        # Add states where >10% of employees are
        total = sum(state_counts.values())
        for state, count in state_counts.items():
            if count / total >= 0.1 and state not in strategy['primary_states']:
                strategy['primary_states'].append(state)
    
    return strategy