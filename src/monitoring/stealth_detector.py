"""
Stealth Founder Detection Module
Detects signals of employees who may be building stealth startups
Enhanced with company and role configurations
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
    # Default values if configs not available
    AI_FOCUSED_BIG_TECH = ['google', 'meta', 'microsoft', 'apple']
    ONLY_AI_TECH = ['openai', 'anthropic', 'deepmind']
    AI_ML_ROLES = ['research', 'engineering']
    AI_ML_SUBROLES = ['data_science', 'machine_learning']

class StealthFounderDetector:
    """
    Detects stealth founder signals from employee data
    """
    
    # Key patterns that indicate stealth mode
    STEALTH_INDICATORS = {
        'company_names': [
            'stealth', 'stealth startup', 'stealth mode',
            'new venture', 'self-employed', 'self employed',
            'independent', 'consulting', 'advisor', 'personal project',
            'freelance', 'contractor', 'entrepreneur', 'founder'
        ],
        'job_titles': [
            'founder', 'co-founder', 'cofounder', 'building',
            'working on', 'creating', 'developing', 'entrepreneur',
            'chief executive', 'chief technology', 'chief product'
        ],
        'vague_phrases': [
            'building something cool', 'building something new',
            'working on something exciting', 'can\'t share yet',
            'more to come', 'stay tuned', 'stealth mode',
            'confidential', 'under wraps', 'coming soon',
            'exciting project', 'new adventure', 'next chapter',
            'something big', 'watch this space', 'to be announced',
            'tbd', 'stealth', 'working on it'
        ],
        'departure_signals': [
            'exploring opportunities', 'taking a break',
            'on sabbatical', 'pursuing new challenges',
            'open to opportunities', 'considering next steps'
        ]
    }
    
    def __init__(self):
        self.min_stealth_score = 50  # Minimum score to flag as stealth
        
        # Company and role boost factors
        self.company_boost = {
            'only_ai': 15,      # OpenAI, Anthropic boost
            'ai_focused': 10,   # Google, Meta boost
            'other': 0
        }
        
        self.role_boost = {
            'ai_ml_core': 10,   # Research, engineering boost
            'ai_ml_sub': 8,     # Data science boost
            'other': 0
        }
    
    def detect_stealth_signals(self, employee: Dict[str, Any]) -> Tuple[float, List[str], str]:
        """
        Analyze employee data for stealth founder signals
        
        Returns:
            - score: 0-100 indicating likelihood of being a stealth founder
            - signals: List of detected signals
            - tier: 'high', 'medium', or 'low' priority
        """
        # Validate input is a dictionary
        if not employee or not isinstance(employee, dict):
            return 0, [], 'general'
        
        score = 0
        signals = []
        
        # 1. Check current company name (40 points max)
        company_score, company_signals = self._check_company_name(employee)
        score += company_score
        signals.extend(company_signals)
        
        # 2. Check job title (30 points max)
        title_score, title_signals = self._check_job_title(employee)
        score += title_score
        signals.extend(title_signals)
        
        # 3. Check for vague descriptions (20 points max)
        desc_score, desc_signals = self._check_descriptions(employee)
        score += desc_score
        signals.extend(desc_signals)
        
        # 4. Check employment gaps/transitions (10 points max)
        gap_score, gap_signals = self._check_employment_gaps(employee)
        score += gap_score
        signals.extend(gap_signals)
        
        # 5. Apply company and role boosts
        company_boost, company_signal = self._apply_company_boost(employee)
        score += company_boost
        if company_signal:
            signals.append(company_signal)
        
        role_boost, role_signal = self._apply_role_boost(employee)
        score += role_boost
        if role_signal:
            signals.append(role_signal)
        
        # Determine monitoring tier
        tier = self._determine_tier(score, employee)
        
        return score, signals, tier
    
    def _check_company_name(self, employee: Dict) -> Tuple[float, List[str]]:
        """Check if current company indicates stealth mode"""
        score = 0
        signals = []
        
        company_name = (employee.get('job_company_name') or '').lower().strip()
        
        if not company_name:
            # No company listed but was previously employed
            if employee.get('experience') and len(employee.get('experience', [])) > 0:
                score += 25
                signals.append("No current company listed (possible stealth)")
            return score, signals
        
        # Check for exact stealth indicators
        for indicator in self.STEALTH_INDICATORS['company_names']:
            if indicator in company_name:
                score += 40
                signals.append(f"Stealth company indicator: '{company_name}'")
                break
        
        # Check if company size is very small (1-10) with vague name
        company_size = employee.get('job_company_size', '')
        if company_size == '1-10' and len(company_name) < 20:
            score += 10
            signals.append(f"Very small company: {company_name} ({company_size})")
        
        return score, signals
    
    def _check_job_title(self, employee: Dict) -> Tuple[float, List[str]]:
        """Check if job title indicates founder/building status"""
        score = 0
        signals = []
        
        job_title = (employee.get('job_title') or '').lower().strip()
        
        if not job_title:
            return score, signals
        
        # Check for founder-related titles
        for indicator in self.STEALTH_INDICATORS['job_titles']:
            if indicator in job_title:
                score += 30
                signals.append(f"Founder-indicating title: '{job_title}'")
                break
        
        # Check for vague titles
        vague_titles = ['consultant', 'advisor', 'independent', 'self']
        for vague in vague_titles:
            if vague in job_title:
                score += 15
                signals.append(f"Vague title: '{job_title}'")
                break
        
        return score, signals
    
    def _check_descriptions(self, employee: Dict) -> Tuple[float, List[str]]:
        """Check experience descriptions for stealth phrases"""
        score = 0
        signals = []
        
        # Check current experience description
        experiences = employee.get('experience', [])
        if experiences and isinstance(experiences, list):
            for exp in experiences:
                if isinstance(exp, dict) and exp.get('is_primary'):
                    # Check company description/summary
                    company_data = exp.get('company', {})
                    if isinstance(company_data, dict):
                        company_desc = (company_data.get('summary', '') or '').lower()
                        
                        for phrase in self.STEALTH_INDICATORS['vague_phrases']:
                            if phrase in company_desc:
                                score += 20
                                signals.append(f"Stealth phrase detected: '{phrase}'")
                                break
        
        # Check if LinkedIn summary has stealth signals (if available)
        summary = (employee.get('summary') or '').lower()
        for phrase in self.STEALTH_INDICATORS['vague_phrases']:
            if phrase in summary:
                score += 10
                signals.append(f"Profile contains: '{phrase}'")
                break
        
        return score, signals
    
    def _check_employment_gaps(self, employee: Dict) -> Tuple[float, List[str]]:
        """Check for recent departure with no clear next role"""
        score = 0
        signals = []
        
        # Check if recently left a big tech company
        last_job_change = employee.get('job_last_changed')
        if last_job_change:
            try:
                # Parse date and check if recent
                change_date = datetime.strptime(last_job_change, '%Y-%m-%d')
                days_since_change = (datetime.now() - change_date).days
                
                if days_since_change < 180:  # Within 6 months
                    # Check if left a major company
                    experiences = employee.get('experience', [])
                    if experiences and isinstance(experiences, list):
                        for exp in experiences:
                            if isinstance(exp, dict) and not exp.get('is_primary') and exp.get('end_date'):
                                company_data = exp.get('company', {})
                                if isinstance(company_data, dict):
                                    company_name = (company_data.get('name', '') or '').lower()
                                    big_tech = ['google', 'meta', 'facebook', 'apple', 'microsoft', 
                                               'amazon', 'netflix', 'openai', 'anthropic', 'nvidia']
                                    
                                    if any(tech in company_name for tech in big_tech):
                                        score += 10
                                        signals.append(f"Recently left {company_data.get('name', 'Big Tech')} ({days_since_change} days ago)")
                                        break
            except:
                pass
        
        return score, signals
    
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
                            signal = f"Former employee of pure AI company ({company_data.get('name', 'AI company')})"
                            break
                        
                        # Check for AI_FOCUSED companies
                        elif any(ai_comp in company_name for ai_comp in AI_FOCUSED_BIG_TECH):
                            boost = max(boost, self.company_boost['ai_focused'])
                            if not signal:
                                signal = f"Former employee of AI-focused company ({company_data.get('name', 'Tech company')})"
        
        return boost, signal
    
    def _apply_role_boost(self, employee: Dict) -> Tuple[float, str]:
        """Apply boost based on AI/ML role experience"""
        boost = 0
        signal = None
        
        # Check current role
        job_role = (employee.get('job_title_role', '') or '').lower()
        job_subrole = (employee.get('job_title_sub_role', '') or '').lower()
        
        if job_role in AI_ML_ROLES:
            boost = self.role_boost['ai_ml_core']
            signal = f"AI/ML core role: {employee.get('job_title_role', 'AI role')}"
        elif job_subrole in AI_ML_SUBROLES:
            boost = self.role_boost['ai_ml_sub']
            signal = f"AI/ML specialization: {employee.get('job_title_sub_role', 'ML role')}"
        
        return boost, signal
    
    def _determine_tier(self, score: float, employee: Dict) -> str:
        """
        Determine monitoring priority tier based on score and other factors
        
        Returns: 'vip', 'watch', or 'general'
        """
        # VIP tier (daily monitoring)
        if score >= 70:
            return 'vip'
        
        # Additional VIP criteria
        if score >= 50:
            # Check for senior roles
            job_title = (employee.get('job_title') or '').lower()
            senior_titles = ['director', 'vp', 'vice president', 'head', 'chief', 'principal', 'staff']
            if any(title in job_title for title in senior_titles):
                return 'vip'
            
            # Recent departure from key companies
            job_change = employee.get('job_last_changed')
            if job_change:
                try:
                    change_date = datetime.strptime(job_change, '%Y-%m-%d')
                    if (datetime.now() - change_date).days < 30:
                        return 'vip'
                except:
                    pass
        
        # Watch tier (weekly monitoring)
        if score >= 30:
            return 'watch'
        
        # General tier (monthly monitoring)
        return 'general'
    
    def analyze_bulk_employees(self, employees: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Analyze multiple employees and categorize by tier
        
        Returns dict with 'vip', 'watch', 'general' lists
        """
        # Validate input
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
                'general_count': 0
            }
        }
        
        for employee in employees:
            # Skip if not a dictionary
            if not isinstance(employee, dict):
                continue
                
            score, signals, tier = self.detect_stealth_signals(employee)
            
            employee_result = {
                'pdl_id': employee.get('id', ''),
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
        
        return results
    
    def get_monitoring_priority(self, employee_result: Dict) -> Dict[str, Any]:
        """
        Determine specific monitoring schedule for an employee
        """
        tier = employee_result.get('tier', 'general')
        score = employee_result.get('stealth_score', 0)
        
        schedules = {
            'vip': {
                'frequency': 'daily',
                'next_check': (datetime.now() + timedelta(days=1)).isoformat(),
                'priority': 1,
                'reason': 'High stealth signals detected'
            },
            'watch': {
                'frequency': 'weekly', 
                'next_check': (datetime.now() + timedelta(days=7)).isoformat(),
                'priority': 2,
                'reason': 'Moderate stealth signals'
            },
            'general': {
                'frequency': 'monthly',
                'next_check': (datetime.now() + timedelta(days=30)).isoformat(),
                'priority': 3,
                'reason': 'Low stealth signals'
            }
        }
        
        schedule = schedules.get(tier, schedules['general'])
        schedule['tier'] = tier
        schedule['score'] = score
        
        return schedule