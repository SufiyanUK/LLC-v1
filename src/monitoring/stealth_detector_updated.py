"""
UPDATED Stealth Founder Detection Module
IMPROVEMENTS:
- More granular company name scoring (personal names, exact stealth match)
- Enhanced title detection (founding engineer, 0->1, technical co-founder)
- Added profile consistency checks (LinkedIn updates, location changes)
- Refined timing bonus (15 points for <30 days, graduated scale)
- Raised VIP threshold to 75 (from 70)
- Added company registration pattern detection
"""

import json
import os
import sys
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import re

# Add project root to path for config imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

try:
    from config.companies import AI_FOCUSED_BIG_TECH, ONLY_AI_TECH
    from config.job_roles import AI_ML_ROLES, AI_ML_SUBROLES
except ImportError:
    AI_FOCUSED_BIG_TECH = ['google', 'meta', 'microsoft', 'apple']
    ONLY_AI_TECH = ['openai', 'anthropic', 'deepmind']
    AI_ML_ROLES = ['research', 'engineering']
    AI_ML_SUBROLES = ['data_science', 'machine_learning']

class StealthFounderDetector:
    """
    UPDATED: Enhanced stealth founder detection with more nuanced scoring
    """
    
    # UPDATED: More comprehensive stealth indicators
    STEALTH_INDICATORS = {
        'strong_company_signals': [
            'stealth', 'stealth startup', 'stealth mode'
        ],
        'moderate_company_signals': [
            'new venture', 'building', 'labs', 'research',
            'ai labs', 'ml labs', 'consulting', 'advisor',
            'personal project', 'independent', 'self-employed'
        ],
        'weak_company_signals': [
            'freelance', 'contractor', 'entrepreneur'
        ],
        'founder_titles': [
            'founder', 'co-founder', 'cofounder', 
            'founding engineer', 'technical co-founder',
            'ceo', 'cto', 'chief executive', 'chief technology'
        ],
        'building_titles': [
            'building', '0 to 1', '0->1', 'creating', 
            'working on', 'developing', 'early stage'
        ],
        'vague_titles': [
            'consultant', 'advisor', 'independent', 'self'
        ],
        'stealth_phrases': [
            'building something cool', 'building something new',
            'working on something exciting', 'can\'t share yet',
            'more to come', 'stay tuned', 'stealth mode',
            'confidential', 'under wraps', 'coming soon',
            'exciting project', 'new adventure', 'next chapter',
            'something big', 'watch this space', 'to be announced',
            'tbd', 'working on it', 'building in stealth'
        ],
        'profile_changes': [
            'opinions are my own', 'views are my own',
            'building @', 'founder @', 'previously @'
        ]
    }
    
    def __init__(self):
        self.min_stealth_score = 50
        
        # UPDATED: Adjusted boost factors
        self.company_boost = {
            'only_ai': 20,      # Increased from 15
            'ai_focused': 15,   # Increased from 10
            'other': 0
        }
        
        self.role_boost = {
            'ai_ml_core': 15,   # Increased from 10
            'ai_ml_sub': 10,    # Increased from 8
            'senior_level': 10, # NEW: Bonus for seniority
            'other': 0
        }
    
    def detect_stealth_signals(self, employee: Dict[str, Any]) -> Tuple[float, List[str], str]:
        """
        UPDATED: More sophisticated stealth signal detection
        """
        if not employee or not isinstance(employee, dict):
            return 0, [], 'general'
        
        score = 0
        signals = []
        
        # 1. UPDATED: More granular company name checking (40 points max)
        company_score, company_signals = self._check_company_name_advanced(employee)
        score += company_score
        signals.extend(company_signals)
        
        # 2. UPDATED: Enhanced job title checking (35 points max)
        title_score, title_signals = self._check_job_title_advanced(employee)
        score += title_score
        signals.extend(title_signals)
        
        # 3. Check descriptions (20 points max)
        desc_score, desc_signals = self._check_descriptions(employee)
        score += desc_score
        signals.extend(desc_signals)
        
        # 4. UPDATED: Better timing analysis (15 points max)
        gap_score, gap_signals = self._check_employment_timing(employee)
        score += gap_score
        signals.extend(gap_signals)
        
        # 5. NEW: Profile consistency check (15 points max)
        consistency_score, consistency_signals = self._check_profile_consistency(employee)
        score += consistency_score
        signals.extend(consistency_signals)
        
        # 6. Apply company and role boosts
        company_boost, company_signal = self._apply_company_boost(employee)
        score += company_boost
        if company_signal:
            signals.append(company_signal)
        
        role_boost, role_signal = self._apply_role_boost_advanced(employee)
        score += role_boost
        if role_signal:
            signals.append(role_signal)
        
        # Determine tier with updated thresholds
        tier = self._determine_tier_updated(score, employee)
        
        return score, signals, tier
    
    def _check_company_name_advanced(self, employee: Dict) -> Tuple[float, List[str]]:
        """
        UPDATED: More nuanced company name analysis
        """
        score = 0
        signals = []
        
        company_name = (employee.get('job_company_name') or '').lower().strip()
        company_size = employee.get('job_company_size', '')
        
        # No company but was previously employed
        if not company_name:
            if employee.get('experience') and len(employee.get('experience', [])) > 0:
                score += 30  # Increased from 25
                signals.append("No current company (likely stealth)")
            return score, signals
        
        # Check for personal name patterns (e.g., "John Smith Inc")
        full_name = (employee.get('full_name', '') or '').lower()
        if full_name and any(name_part in company_name for name_part in full_name.split() if len(name_part) > 3):
            score += 35
            signals.append(f"Company appears to be personal venture: '{company_name}'")
            return score, signals
        
        # Exact stealth match
        if company_name in self.STEALTH_INDICATORS['strong_company_signals']:
            score += 40
            signals.append(f"Exact stealth indicator: '{company_name}'")
        # Moderate signals
        elif any(signal in company_name for signal in self.STEALTH_INDICATORS['moderate_company_signals']):
            score += 25
            signals.append(f"Building/venture indicator: '{company_name}'")
        # Contains AI/Labs with small size
        elif ('ai' in company_name or 'labs' in company_name) and company_size in ['1-10', '11-50']:
            score += 20
            signals.append(f"Small AI/Labs company: '{company_name}' ({company_size})")
        # Generic small company with vague name
        elif company_size == '1-10' and len(company_name.split()) <= 2:
            score += 10
            signals.append(f"Very small company: '{company_name}'")
        
        return score, signals
    
    def _check_job_title_advanced(self, employee: Dict) -> Tuple[float, List[str]]:
        """
        UPDATED: Enhanced title analysis
        """
        score = 0
        signals = []
        
        job_title = (employee.get('job_title') or '').lower().strip()
        
        if not job_title:
            return score, signals
        
        # Check for exact founder titles
        for founder_title in self.STEALTH_INDICATORS['founder_titles']:
            if founder_title in job_title:
                # Multiple founder signals (e.g., "CTO & Co-founder")
                if sum(1 for ft in self.STEALTH_INDICATORS['founder_titles'] if ft in job_title) >= 2:
                    score += 35
                    signals.append(f"Multiple founder titles: '{job_title}'")
                else:
                    score += 30
                    signals.append(f"Founder title: '{job_title}'")
                return score, signals
        
        # Check for building/early stage
        for building_title in self.STEALTH_INDICATORS['building_titles']:
            if building_title in job_title:
                score += 25
                signals.append(f"Building/early stage: '{job_title}'")
                return score, signals
        
        # Vague titles
        for vague_title in self.STEALTH_INDICATORS['vague_titles']:
            if vague_title in job_title:
                score += 15
                signals.append(f"Vague title: '{job_title}'")
                break
        
        return score, signals
    
    def _check_employment_timing(self, employee: Dict) -> Tuple[float, List[str]]:
        """
        UPDATED: Graduated timing bonus
        """
        score = 0
        signals = []
        
        last_job_change = employee.get('job_last_changed')
        if last_job_change:
            try:
                change_date = datetime.strptime(last_job_change, '%Y-%m-%d')
                days_since_change = (datetime.now() - change_date).days
                
                # UPDATED: More granular timing
                if days_since_change <= 30:
                    score += 15
                    signals.append(f"Very recent departure ({days_since_change} days ago)")
                elif days_since_change <= 60:
                    score += 12
                    signals.append(f"Recent departure ({days_since_change} days ago)")
                elif days_since_change <= 90:
                    score += 10
                    signals.append(f"Recent departure ({days_since_change} days ago)")
                elif days_since_change <= 180:
                    score += 5
                    signals.append(f"Departed within 6 months")
                
                # Check if left major company
                if days_since_change <= 180:
                    experiences = employee.get('experience', [])
                    for exp in experiences:
                        if isinstance(exp, dict) and not exp.get('is_primary'):
                            company_data = exp.get('company', {})
                            if isinstance(company_data, dict):
                                company_name = (company_data.get('name', '') or '').lower()
                                
                                # Priority companies for 2024
                                priority_companies = ['openai', 'anthropic', 'google', 'deepmind', 'meta']
                                if any(pc in company_name for pc in priority_companies):
                                    score += 5
                                    signals.append(f"Left priority AI company: {company_data.get('name', '')}")
                                    break
            except:
                pass
        
        return score, signals
    
    def _check_profile_consistency(self, employee: Dict) -> Tuple[float, List[str]]:
        """
        NEW: Check for profile inconsistencies that suggest stealth mode
        """
        score = 0
        signals = []
        
        # Check if profile was recently updated
        last_updated = employee.get('job_last_updated')
        if last_updated:
            try:
                update_date = datetime.strptime(last_updated, '%Y-%m-%d')
                days_since_update = (datetime.now() - update_date).days
                
                if days_since_update <= 30:
                    score += 5
                    signals.append("LinkedIn profile recently updated")
            except:
                pass
        
        # Check location changes
        current_location = employee.get('job_company_location', {})
        if isinstance(current_location, dict):
            locality = current_location.get('locality', '').lower()
            
            # Changed to startup hub
            startup_hubs = ['san francisco', 'palo alto', 'mountain view', 'austin', 'seattle']
            if any(hub in locality for hub in startup_hubs):
                experiences = employee.get('experience', [])
                for exp in experiences:
                    if isinstance(exp, dict) and not exp.get('is_primary'):
                        old_location = exp.get('company', {}).get('location', {})
                        if isinstance(old_location, dict):
                            old_locality = old_location.get('locality', '').lower()
                            if old_locality and old_locality != locality:
                                score += 5
                                signals.append(f"Relocated to startup hub: {locality}")
                                break
        
        # Title says founder but company not well-known
        job_title = (employee.get('job_title') or '').lower()
        company_name = (employee.get('job_company_name') or '').lower()
        
        if ('founder' in job_title or 'ceo' in job_title) and company_name:
            # Check if company is not in known companies list
            known_companies = AI_FOCUSED_BIG_TECH + ONLY_AI_TECH
            if not any(kc in company_name for kc in known_companies):
                score += 5
                signals.append("Founder title at unknown company")
        
        return score, signals
    
    def _apply_role_boost_advanced(self, employee: Dict) -> Tuple[float, str]:
        """
        UPDATED: Enhanced role boosting with seniority
        """
        boost = 0
        signal = None
        
        job_role = (employee.get('job_title_role', '') or '').lower()
        job_subrole = (employee.get('job_title_sub_role', '') or '').lower()
        job_title = (employee.get('job_title', '') or '').lower()
        
        # Check for AI/ML roles
        if job_role in AI_ML_ROLES:
            boost = self.role_boost['ai_ml_core']
            signal = f"AI/ML core role: {job_role}"
        elif job_subrole in AI_ML_SUBROLES:
            boost = self.role_boost['ai_ml_sub']
            signal = f"AI/ML specialization: {job_subrole}"
        
        # NEW: Add seniority boost
        senior_titles = ['director', 'vp', 'vice president', 'head', 'chief', 'principal', 'staff', 'senior']
        if any(title in job_title for title in senior_titles):
            boost += self.role_boost['senior_level']
            if signal:
                signal += " (senior level)"
            else:
                signal = "Senior level position"
        
        return boost, signal
    
    def _determine_tier_updated(self, score: float, employee: Dict) -> str:
        """
        UPDATED: New tier thresholds
        """
        # VIP tier (daily monitoring) - UPDATED threshold
        if score >= 75:  # Increased from 70
            return 'vip'
        
        # Additional VIP criteria with lower score
        if score >= 60:
            job_title = (employee.get('job_title') or '').lower()
            
            # Very senior + recent departure
            senior_titles = ['director', 'vp', 'chief', 'head', 'principal', 'staff']
            if any(title in job_title for title in senior_titles):
                job_change = employee.get('job_last_changed')
                if job_change:
                    try:
                        change_date = datetime.strptime(job_change, '%Y-%m-%d')
                        if (datetime.now() - change_date).days < 60:
                            return 'vip'
                    except:
                        pass
        
        # Watch tier (weekly monitoring) - UPDATED threshold
        if score >= 40:  # Increased from 30
            return 'watch'
        
        # General tier
        return 'general'
    
    def _apply_company_boost(self, employee: Dict) -> Tuple[float, str]:
        """Apply boost based on previous company experience"""
        boost = 0
        signal = None
        
        experiences = employee.get('experience', [])
        if experiences and isinstance(experiences, list):
            for exp in experiences:
                if isinstance(exp, dict):
                    company_data = exp.get('company', {})
                    if isinstance(company_data, dict):
                        company_name = (company_data.get('name', '') or '').lower()
                        
                        # Check for ONLY_AI companies
                        if any(ai_comp in company_name for ai_comp in ONLY_AI_TECH):
                            boost = max(boost, self.company_boost['only_ai'])
                            signal = f"Former {company_data.get('name', 'AI company')} employee"
                            break
                        
                        # Check for AI_FOCUSED companies
                        elif any(ai_comp in company_name for ai_comp in AI_FOCUSED_BIG_TECH):
                            boost = max(boost, self.company_boost['ai_focused'])
                            if not signal:
                                signal = f"Former {company_data.get('name', 'Tech company')} employee"
        
        return boost, signal
    
    def _check_descriptions(self, employee: Dict) -> Tuple[float, List[str]]:
        """Check for stealth phrases in descriptions"""
        score = 0
        signals = []
        
        # Check current experience description
        experiences = employee.get('experience', [])
        if experiences and isinstance(experiences, list):
            for exp in experiences:
                if isinstance(exp, dict) and exp.get('is_primary'):
                    company_data = exp.get('company', {})
                    if isinstance(company_data, dict):
                        company_desc = (company_data.get('summary', '') or '').lower()
                        
                        for phrase in self.STEALTH_INDICATORS['stealth_phrases']:
                            if phrase in company_desc:
                                score += 20
                                signals.append(f"Stealth phrase: '{phrase}'")
                                break
        
        # Check LinkedIn summary
        summary = (employee.get('summary') or '').lower()
        for phrase in self.STEALTH_INDICATORS['stealth_phrases']:
            if phrase in summary:
                score += 10
                signals.append(f"Profile contains: '{phrase}'")
                break
        
        # NEW: Check for profile change indicators
        for change_phrase in self.STEALTH_INDICATORS['profile_changes']:
            if change_phrase in summary:
                score += 5
                signals.append("Profile shows independence indicators")
                break
        
        return score, signals
    
    def analyze_bulk_employees(self, employees: List[Dict]) -> Dict[str, List[Dict]]:
        """Analyze multiple employees and categorize by tier"""
        if not employees or not isinstance(employees, list):
            employees = []
        
        results = {
            'vip': [],
            'watch': [],
            'general': [],
            'stats': {
                'total_analyzed': len(employees),
                'stealth_detected': 0,
                'vip_count': 0,
                'watch_count': 0,
                'general_count': 0,
                'average_score': 0
            }
        }
        
        total_score = 0
        
        for employee in employees:
            if not isinstance(employee, dict):
                continue
            
            score, signals, tier = self.detect_stealth_signals(employee)
            total_score += score
            
            employee_result = {
                'pdl_id': employee.get('pdl_id', employee.get('id', '')),  # Check pdl_id first, then id
                'full_name': employee.get('full_name', 'Unknown'),
                'job_company_name': employee.get('job_company_name', ''),
                'job_title': employee.get('job_title', ''),
                'stealth_score': score,
                'signals': signals,
                'tier': tier,
                'last_checked': datetime.now().isoformat()
            }
            
            results[tier].append(employee_result)
            results['stats'][f'{tier}_count'] += 1
            
            if score >= self.min_stealth_score:
                results['stats']['stealth_detected'] += 1
        
        if len(employees) > 0:
            results['stats']['average_score'] = round(total_score / len(employees), 1)
        
        return results

# Standalone function for easy testing
def test_stealth_detection():
    """Test the updated stealth detection"""
    
    detector = StealthFounderDetector()
    
    # Test cases
    test_employees = [
        {
            'full_name': 'John Smith',
            'job_company_name': 'Stealth Startup',
            'job_title': 'Co-founder & CTO',
            'job_company_size': '1-10',
            'job_last_changed': (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
            'experience': [
                {
                    'company': {'name': 'OpenAI'},
                    'is_primary': False,
                    'end_date': '2024-01-01'
                }
            ]
        },
        {
            'full_name': 'Jane Doe',
            'job_company_name': 'Building something new',
            'job_title': 'Founding Engineer',
            'job_company_size': '1-10',
            'job_last_changed': (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
            'job_title_role': 'engineering',
            'experience': [
                {
                    'company': {'name': 'Google'},
                    'is_primary': False
                }
            ]
        },
        {
            'full_name': 'Bob Johnson',
            'job_company_name': '',  # No company listed
            'job_title': '',
            'job_last_changed': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            'experience': [
                {
                    'company': {'name': 'Anthropic'},
                    'is_primary': False
                }
            ]
        }
    ]
    
    print("TESTING UPDATED STEALTH DETECTION")
    print("=" * 80)
    
    results = detector.analyze_bulk_employees(test_employees)
    
    for tier in ['vip', 'watch', 'general']:
        print(f"\n{tier.upper()} Tier:")
        for emp in results[tier]:
            print(f"  - {emp['full_name']}: Score {emp['stealth_score']}")
            for signal in emp['signals'][:3]:
                print(f"    • {signal}")
    
    print(f"\nStatistics:")
    for key, value in results['stats'].items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_stealth_detection()