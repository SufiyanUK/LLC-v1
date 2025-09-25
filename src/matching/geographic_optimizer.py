"""
Geographic Optimizer for Company-State Mapping
Dynamically determines where companies' employees are actually located
"""

import json
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeographicOptimizer:
    """
    Intelligently maps companies to their actual employee locations
    and optimizes matching based on geographic patterns
    """
    
    def __init__(self):
        # Pre-known headquarters (can be overridden by data)
        self.known_headquarters = {
            # California companies
            'openai': {'primary': 'california', 'cities': ['san francisco']},
            'google': {'primary': 'california', 'cities': ['mountain view', 'san francisco', 'sunnyvale']},
            'meta': {'primary': 'california', 'cities': ['menlo park', 'san francisco']},
            'apple': {'primary': 'california', 'cities': ['cupertino', 'san francisco']},
            'nvidia': {'primary': 'california', 'cities': ['santa clara', 'san francisco']},
            'anthropic': {'primary': 'california', 'cities': ['san francisco']},
            
            # Multi-state companies
            'microsoft': {'primary': 'washington', 'cities': ['redmond', 'seattle']},
            'amazon': {'primary': 'washington', 'cities': ['seattle', 'bellevue']},
            
            # East Coast
            'ibm': {'primary': 'new york', 'cities': ['armonk', 'new york city']},
        }
        
        # Secondary offices (for large companies)
        self.secondary_offices = {
            'google': ['new york', 'washington', 'texas', 'colorado'],
            'meta': ['new york', 'washington', 'texas'],
            'microsoft': ['california', 'new york', 'texas'],
            'amazon': ['california', 'new york', 'virginia', 'texas'],
            'apple': ['texas', 'new york'],
        }
        
        # Tech hub cities by state
        self.tech_hubs = {
            'california': ['san francisco', 'san jose', 'palo alto', 'mountain view', 
                          'sunnyvale', 'san mateo', 'redwood city', 'menlo park',
                          'los angeles', 'san diego', 'santa monica', 'irvine'],
            'washington': ['seattle', 'redmond', 'bellevue', 'kirkland', 'tacoma'],
            'texas': ['austin', 'dallas', 'houston', 'plano', 'san antonio'],
            'new york': ['new york', 'brooklyn', 'manhattan', 'queens'],
            'massachusetts': ['boston', 'cambridge'],
            'colorado': ['denver', 'boulder'],
            'georgia': ['atlanta'],
            'illinois': ['chicago'],
            'oregon': ['portland'],
            'north carolina': ['raleigh', 'durham', 'charlotte'],
        }
    
    def analyze_employee_distribution(self, employees: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze where a company's employees are actually located
        Returns distribution of employees by state and city
        """
        distribution = defaultdict(lambda: defaultdict(int))
        
        for emp in employees:
            # Get employee's work location
            state = emp.get('job_company_location_region', '').lower()
            city = emp.get('job_company_location_locality', '').lower()
            
            if state:
                distribution[state]['total'] += 1
                if city:
                    distribution[state][city] += 1
        
        # Calculate percentages and identify primary locations
        total_employees = sum(d['total'] for d in distribution.values())
        
        result = {
            'total_employees': total_employees,
            'states': {},
            'primary_state': None,
            'primary_cities': [],
            'recommended_search_states': []
        }
        
        for state, data in distribution.items():
            percentage = (data['total'] / total_employees * 100) if total_employees > 0 else 0
            result['states'][state] = {
                'count': data['total'],
                'percentage': round(percentage, 1),
                'top_cities': sorted(
                    [(city, count) for city, count in data.items() if city != 'total'],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }
        
        # Identify primary state (where most employees are)
        if result['states']:
            primary = max(result['states'].items(), key=lambda x: x[1]['count'])
            result['primary_state'] = primary[0]
            result['primary_cities'] = [city for city, _ in primary[1]['top_cities'][:3]]
        
        # Recommend states to search (>10% of employees)
        result['recommended_search_states'] = [
            state for state, data in result['states'].items()
            if data['percentage'] >= 10
        ]
        
        return result
    
    def optimize_search_strategy(self, company_name: str, employee_sample: List[Dict] = None) -> Dict:
        """
        Create optimized search strategy for a company
        """
        company_lower = company_name.lower()
        strategy = {
            'company': company_name,
            'search_states': [],
            'search_cities': [],
            'incorporation_states': ['delaware'],  # Always check Delaware
            'search_radius_miles': 50,
            'include_remote': True
        }
        
        # Use known data if available
        if company_lower in self.known_headquarters:
            hq = self.known_headquarters[company_lower]
            strategy['search_states'].append(hq['primary'])
            strategy['search_cities'].extend(hq['cities'])
        
        # Add secondary offices
        if company_lower in self.secondary_offices:
            strategy['search_states'].extend(self.secondary_offices[company_lower])
        
        # Analyze actual employee distribution if sample provided
        if employee_sample:
            distribution = self.analyze_employee_distribution(employee_sample)
            
            # Override with actual data
            if distribution['primary_state']:
                if distribution['primary_state'] not in strategy['search_states']:
                    strategy['search_states'].insert(0, distribution['primary_state'])
            
            # Add states with significant presence
            for state in distribution['recommended_search_states']:
                if state not in strategy['search_states']:
                    strategy['search_states'].append(state)
            
            # Add actual cities where employees are
            for city in distribution['primary_cities']:
                if city not in strategy['search_cities']:
                    strategy['search_cities'].append(city)
        
        # For startups, focus on tech hubs in those states
        strategy['tech_hub_cities'] = []
        for state in strategy['search_states']:
            if state in self.tech_hubs:
                strategy['tech_hub_cities'].extend(self.tech_hubs[state])
        
        return strategy
    
    def match_by_geography(self, founder: Dict, startup: Dict, strategy: Dict = None) -> Tuple[float, List[str]]:
        """
        Enhanced geographic matching with multiple signals
        Returns (score, reasons)
        """
        score = 0
        reasons = []
        
        # Get locations
        founder_state = (founder.get('job_company_location_region', '') or '').lower()
        founder_city = (founder.get('job_company_location_locality', '') or '').lower()
        startup_state = (startup.get('location', {}).get('region', '') or '').lower()
        startup_city = (startup.get('location', {}).get('locality', '') or '').lower()
        
        # Check for Delaware incorporation pattern
        if startup_state == 'delaware' and founder_state in ['california', 'new york', 'texas', 'washington']:
            score += 15
            reasons.append(f"Common pattern: {founder_state} founder, Delaware incorporation")
        
        # Same state match
        if founder_state and startup_state:
            if founder_state == startup_state:
                score += 30
                reasons.append(f"Same state: {founder_state}")
                
                # Same city bonus
                if founder_city == startup_city:
                    score += 20
                    reasons.append(f"Same city: {founder_city}")
        
        # Tech hub proximity
        if strategy and 'tech_hub_cities' in strategy:
            if founder_city in strategy['tech_hub_cities'] and startup_city in strategy['tech_hub_cities']:
                score += 15
                reasons.append("Both in tech hub cities")
        
        # Remote work consideration
        if not startup_city or startup_city == 'remote':
            score += 10
            reasons.append("Startup may be remote/distributed")
        
        # Stealth mode locations
        stealth_indicators = ['stealth', 'undisclosed', 'confidential']
        if any(ind in startup.get('name', '').lower() for ind in stealth_indicators):
            score += 10
            reasons.append("Stealth mode - location may be hidden")
        
        return score, reasons

class EnhancedMatcher:
    """
    Improved matching system with multiple strategies
    """
    
    def __init__(self):
        self.geo_optimizer = GeographicOptimizer()
        self.matching_strategies = {
            'exact_name': self.match_exact_name,
            'fuzzy_name': self.match_fuzzy_name,
            'timing': self.match_timing,
            'skills': self.match_skills,
            'network': self.match_network,
            'signals': self.match_signals
        }
    
    def match_exact_name(self, founder: Dict, startup: Dict) -> Tuple[float, str]:
        """Direct company name match"""
        founder_company = (founder.get('job_company_name', '') or '').lower().strip()
        startup_name = (startup.get('name', '') or '').lower().strip()
        
        if founder_company and startup_name:
            if founder_company == startup_name:
                return 50, "Exact company name match"
            
            # Normalize and check again
            founder_norm = founder_company.replace(' ', '').replace('-', '').replace('.', '')
            startup_norm = startup_name.replace(' ', '').replace('-', '').replace('.', '')
            if founder_norm == startup_norm:
                return 45, "Normalized name match"
        
        return 0, ""
    
    def match_fuzzy_name(self, founder: Dict, startup: Dict) -> Tuple[float, str]:
        """Fuzzy name matching for variants"""
        from difflib import SequenceMatcher
        
        founder_company = (founder.get('job_company_name', '') or '').lower()
        startup_name = (startup.get('name', '') or '').lower()
        
        if len(founder_company) > 3 and len(startup_name) > 3:
            similarity = SequenceMatcher(None, founder_company, startup_name).ratio()
            
            if similarity > 0.8:
                return 35, f"High name similarity ({similarity:.0%})"
            elif similarity > 0.6:
                return 20, f"Moderate name similarity ({similarity:.0%})"
        
        # Check if one contains the other
        if founder_company in startup_name or startup_name in founder_company:
            return 25, "Partial name match"
        
        return 0, ""
    
    def match_timing(self, founder: Dict, startup: Dict) -> Tuple[float, str]:
        """Match based on departure and founding timing"""
        departure = founder.get('last_big_tech_departure', {})
        departure_date = departure.get('departure_date', '')
        founded = startup.get('founded')
        
        if departure_date and founded:
            try:
                # Convert to comparable format
                dep_year = int(departure_date[:4]) if departure_date else 0
                found_year = int(founded) if founded else 0
                
                # Ideal: left 0-1 years before founding
                gap = found_year - dep_year
                if 0 <= gap <= 1:
                    return 25, f"Perfect timing: left {dep_year}, founded {found_year}"
                elif 0 <= gap <= 2:
                    return 15, f"Good timing: left {dep_year}, founded {found_year}"
                elif gap < 0 and gap >= -1:
                    return 10, "Joined existing early-stage startup"
            except:
                pass
        
        return 0, ""
    
    def match_skills(self, founder: Dict, startup: Dict) -> Tuple[float, str]:
        """Match technical skills to startup focus"""
        founder_skills = founder.get('skills', [])
        startup_industry = (startup.get('industry', '') or '').lower()
        startup_description = (startup.get('summary', '') or '').lower()
        
        ai_ml_skills = ['machine learning', 'deep learning', 'artificial intelligence', 
                       'tensorflow', 'pytorch', 'neural networks', 'nlp', 'computer vision']
        
        score = 0
        if any(skill.lower() in ai_ml_skills for skill in founder_skills):
            if 'artificial intelligence' in startup_industry or 'ai' in startup_description:
                score = 20
                return score, "AI/ML skills match startup focus"
        
        return 0, ""
    
    def match_network(self, founder: Dict, startup: Dict) -> Tuple[float, str]:
        """Check for co-founder connections"""
        # This would need LinkedIn/social graph data
        # Placeholder for future enhancement
        return 0, ""
    
    def match_signals(self, founder: Dict, startup: Dict) -> Tuple[float, str]:
        """Match on various founder signals"""
        score = 0
        signals = []
        
        # Founder title
        title = (founder.get('job_title', '') or '').lower()
        founder_keywords = ['founder', 'co-founder', 'ceo', 'cto', 'chief', 'building']
        if any(kw in title for kw in founder_keywords):
            score += 15
            signals.append("Has founder/leadership title")
        
        # Stealth signals
        company = (founder.get('job_company_name', '') or '').lower()
        stealth_keywords = ['stealth', 'startup', 'labs', 'ai', 'ml', 'tech']
        if any(kw in company for kw in stealth_keywords):
            score += 10
            signals.append("Company name suggests startup")
        
        # Company size
        if founder.get('job_company_size') == '1-10' and startup.get('size') == '1-10':
            score += 10
            signals.append("Both are small companies")
        
        return score, "; ".join(signals) if signals else ""
    
    def comprehensive_match(self, founder: Dict, startup: Dict, search_strategy: Dict = None) -> Dict:
        """
        Perform comprehensive matching with all strategies
        """
        total_score = 0
        all_reasons = []
        breakdown = {}
        
        # Apply each matching strategy
        for strategy_name, strategy_func in self.matching_strategies.items():
            score, reason = strategy_func(founder, startup)
            if score > 0:
                total_score += score
                if reason:
                    all_reasons.append(reason)
                breakdown[strategy_name] = score
        
        # Geographic matching
        geo_score, geo_reasons = self.geo_optimizer.match_by_geography(
            founder, startup, search_strategy
        )
        if geo_score > 0:
            total_score += geo_score
            all_reasons.extend(geo_reasons)
            breakdown['geography'] = geo_score
        
        # Determine confidence tier
        if total_score >= 80:
            tier = 'HIGH'
        elif total_score >= 50:
            tier = 'MEDIUM'
        elif total_score >= 30:
            tier = 'LOW'
        else:
            tier = 'UNLIKELY'
        
        return {
            'total_score': total_score,
            'confidence_tier': tier,
            'reasons': all_reasons,
            'breakdown': breakdown,
            'founder': {
                'name': founder.get('full_name'),
                'company': founder.get('job_company_name'),
                'title': founder.get('job_title')
            },
            'startup': {
                'name': startup.get('name'),
                'industry': startup.get('industry'),
                'location': startup.get('location', {}).get('locality')
            }
        }

# Usage example
if __name__ == "__main__":
    # Initialize
    geo_opt = GeographicOptimizer()
    matcher = EnhancedMatcher()
    
    # Example: Optimize search for OpenAI
    print("OpenAI Search Strategy:")
    strategy = geo_opt.optimize_search_strategy('openai')
    print(json.dumps(strategy, indent=2))
    
    print("\n" + "="*50)
    print("Geographic Matching Improvements:")
    print("1. Dynamic location analysis based on actual employee data")
    print("2. Multi-state search strategies for large companies")
    print("3. Delaware incorporation + actual operation location pattern")
    print("4. Tech hub proximity scoring")
    print("5. Remote/stealth mode considerations")
    print("6. Comprehensive matching with 6+ strategies")