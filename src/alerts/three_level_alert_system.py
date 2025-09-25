"""
Three-Level Alert System for Founder Detection
Level 3: Left big tech + joined qualified startup (HIGHEST)
Level 2: Left big tech + building signals OR high scores (HIGH)
Level 1: Left big tech recently (BASELINE)

Created with comprehensive phrase detection and error handling
"""

import json
import os
import sys
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import re

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

# Import existing modules
from src.data_processing.founder_qualifier_updated import calculate_founder_potential_score
from src.monitoring.stealth_detector_updated import StealthFounderDetector


class ThreeLevelAlertSystem:
    """
    Comprehensive alert system with three priority levels
    """
    
    def __init__(self, qualified_startups_path: str = None):
        """
        Initialize alert system with qualified startups list
        
        Args:
            qualified_startups_path: Path to qualified_startups.json
        """
        # Load qualified startups
        self.qualified_startups = self._load_qualified_startups(qualified_startups_path)
        
        # Initialize stealth detector
        self.stealth_detector = StealthFounderDetector()
        
        # Define big tech companies (high priority departures)
        self.big_tech_companies = [
            # Pure AI companies (highest priority)
            'openai', 'anthropic', 'deepmind', 'inflection ai', 'character ai',
            'cohere', 'hugging face', 'stability ai', 'midjourney', 'runway',
            
            # Major tech with AI focus
            'google', 'alphabet', 'meta', 'facebook', 'microsoft', 'apple',
            'amazon', 'nvidia', 'tesla', 'netflix', 'adobe', 'salesforce',
            
            # Chinese AI companies
            'deepseek', 'baidu', 'alibaba', 'tencent', 'bytedance',
            
            # Other notable AI/Tech
            'palantir', 'databricks', 'scale ai', 'cruise', 'waymo',
            'neuralink', 'figure', 'boston dynamics'
        ]
        
        # COMPREHENSIVE BUILDING/STEALTH PHRASES (50+ combinations)
        self.building_phrases = [
            # Direct building statements
            'building something new',
            'building something cool', 
            'building something exciting',
            'building something big',
            'building something special',
            'building in stealth',
            'building in public',
            'building the future',
            'building next generation',
            'building ai',
            
            # Working on variations
            'working on something new',
            'working on something exciting',
            'working on something cool',
            'working on something big',
            'working on a new venture',
            'working on a startup',
            'working on stealth',
            'working on something special',
            'working on the next big thing',
            'working on it',
            
            # Creating/Developing
            'creating something new',
            'creating the future',
            'developing something exciting',
            'developing new technology',
            'launching soon',
            'launching startup',
            'starting something new',
            'starting a company',
            
            # Founder/Entrepreneur
            'founder',
            'co-founder',
            'cofounder',
            'founding team',
            'founding member',
            'founding engineer',
            'technical co-founder',
            'entrepreneur',
            'solopreneur',
            
            # Stealth/Confidential
            'stealth mode',
            'stealth startup',
            'stealth',
            'confidential',
            'can\'t share yet',
            'cannot share yet',
            'under wraps',
            'under nda',
            'hush hush',
            
            # Coming soon/Future
            'coming soon',
            'more to come',
            'stay tuned',
            'watch this space',
            'big things coming',
            'exciting things ahead',
            'to be announced',
            'tba',
            'tbd',
            'announcement coming',
            
            # New venture/Chapter
            'new venture',
            'new adventure',
            'new chapter',
            'new journey',
            'next chapter',
            'next adventure',
            'new beginning',
            'pursuing new opportunities',
            'exploring opportunities',
            
            # Early stage
            '0 to 1',
            '0->1',
            'zero to one',
            'day one',
            'day zero',
            'ground floor',
            'early stage',
            'pre-seed',
            'seed stage',
            'bootstrap',
            
            # Vague but telling
            'taking a break',
            'on sabbatical',
            'figuring out what\'s next',
            'exploring ideas',
            'independent',
            'self-employed',
            'consultant',
            'advisor',
            'angel investor',
            
            # AI/Tech specific
            'ai startup',
            'ml startup',
            'building ai',
            'building agi',
            'ai research',
            'independent research',
            'research lab',
            'ai lab',
            'new lab',
            
            # Team building
            'hiring soon',
            'building a team',
            'looking for co-founders',
            'assembling team',
            'join us',
            'we\'re hiring',
            'recruiting founding team'
        ]
        
        # Compile regex patterns for efficient matching
        self.building_patterns = self._compile_patterns(self.building_phrases)
        
        # Alert level definitions
        self.alert_levels = {
            'LEVEL_3': {
                'name': 'Joined Qualified Startup',
                'priority': 3,
                'action': 'IMMEDIATE',
                'color': 'red'
            },
            'LEVEL_2': {
                'name': 'Building Signals Detected',
                'priority': 2,
                'action': 'HIGH_PRIORITY',
                'color': 'orange'
            },
            'LEVEL_1': {
                'name': 'Recently Left Big Tech',
                'priority': 1,
                'action': 'MONITOR',
                'color': 'yellow'
            }
        }
    
    def _load_qualified_startups(self, path: str = None) -> List[Dict]:
        """Load qualified startups from JSON file"""
        if path is None:
            path = os.path.join(project_root, 'data', 'processed', 'qualified_startups.json')
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    startups = json.load(f)
                    print(f"[OK] Loaded {len(startups)} qualified startups")
                    return startups
            except Exception as e:
                print(f"[WARNING] Error loading qualified startups: {e}")
                return []
        else:
            print(f"[WARNING] Qualified startups file not found at {path}")
            return []
    
    def _compile_patterns(self, phrases: List[str]) -> List:
        """Compile regex patterns for efficient matching"""
        patterns = []
        for phrase in phrases:
            # Create case-insensitive pattern with word boundaries where appropriate
            if len(phrase.split()) == 1:  # Single word
                pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            else:  # Multi-word phrase
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def recently_left_big_tech(self, employee: Dict, days: int = 180) -> Tuple[bool, Optional[Dict]]:
        """
        Check if employee recently left a big tech company
        
        Returns:
            (is_recent_departure, departure_info)
        """
        # Check for big tech departure info
        departure = employee.get('last_big_tech_departure')
        if not departure:
            return False, None
        
        # Check if it's a big tech company
        company = (departure.get('company', '') or '').lower()
        if not any(big_tech in company for big_tech in self.big_tech_companies):
            # Double-check in experience
            experiences = employee.get('experience', [])
            found_big_tech = False
            for exp in experiences:
                if isinstance(exp, dict):
                    exp_company = (exp.get('company', {}).get('name', '') or '').lower()
                    if any(big_tech in exp_company for big_tech in self.big_tech_companies):
                        found_big_tech = True
                        company = exp_company
                        break
            
            if not found_big_tech:
                return False, None
        
        # Check recency
        departure_date = departure.get('departure_date', '')
        if departure_date:
            try:
                dep_date = datetime.strptime(departure_date[:10], '%Y-%m-%d')
                days_since = (datetime.now() - dep_date).days
                
                if days_since <= days:
                    return True, {
                        'company': departure.get('company', company),
                        'date': departure_date,
                        'days_ago': days_since,
                        'role': departure.get('role', '')
                    }
            except:
                pass
        
        # Alternative: Check job_last_changed
        last_changed = employee.get('job_last_changed')
        if last_changed:
            try:
                change_date = datetime.strptime(last_changed[:10], '%Y-%m-%d')
                days_since = (datetime.now() - change_date).days
                
                if days_since <= days:
                    return True, {
                        'company': company,
                        'date': last_changed,
                        'days_ago': days_since,
                        'role': employee.get('job_title', '')
                    }
            except:
                pass
        
        return False, None
    
    def joined_qualified_startup(self, employee: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Check if employee joined a qualified startup from our list
        
        Returns:
            (joined_qualified, startup_info)
        """
        current_company = (employee.get('job_company_name', '') or '').lower().strip()
        
        if not current_company:
            return False, None
        
        # Check against qualified startups
        for startup in self.qualified_startups:
            startup_name = (startup.get('name', '') or '').lower().strip()
            
            # Exact match or contains
            if startup_name and (startup_name == current_company or startup_name in current_company):
                return True, {
                    'startup_name': startup.get('name'),
                    'startup_id': startup.get('id'),
                    'tech_score': startup.get('tech_score', 0),
                    'founded': startup.get('founded'),
                    'size': startup.get('size'),
                    'industry': startup.get('industry')
                }
        
        return False, None
    
    def has_building_phrases(self, employee: Dict) -> Tuple[bool, List[str]]:
        """
        Check if employee profile contains building/stealth phrases
        
        Returns:
            (has_phrases, found_phrases)
        """
        found_phrases = []
        
        # Check multiple fields for building phrases
        fields_to_check = [
            employee.get('job_title', ''),
            employee.get('job_company_name', ''),
            employee.get('summary', ''),
            employee.get('headline', ''),
            employee.get('bio', '')
        ]
        
        # Also check experience descriptions
        experiences = employee.get('experience', [])
        for exp in experiences:
            if isinstance(exp, dict):
                fields_to_check.append(exp.get('title', ''))
                fields_to_check.append(exp.get('description', ''))
                company_data = exp.get('company', {})
                if isinstance(company_data, dict):
                    fields_to_check.append(company_data.get('summary', ''))
        
        # Combine all text
        combined_text = ' '.join(str(field) for field in fields_to_check if field)
        
        # Check each pattern
        for i, pattern in enumerate(self.building_patterns):
            if pattern.search(combined_text):
                found_phrases.append(self.building_phrases[i])
        
        # Remove duplicates while preserving order
        found_phrases = list(dict.fromkeys(found_phrases))
        
        return len(found_phrases) > 0, found_phrases[:5]  # Return top 5 phrases
    
    def calculate_alert_level(self, employee: Dict) -> Dict[str, Any]:
        """
        Main function to determine alert level for an employee
        
        Returns comprehensive alert information
        """
        # Initialize result
        alert = {
            'pdl_id': employee.get('pdl_id', employee.get('id', '')),
            'full_name': employee.get('full_name', 'Unknown'),
            'alert_level': None,
            'alert_reasons': [],
            'priority_score': 0,
            'departure_info': None,
            'startup_info': None,
            'building_phrases': [],
            'founder_score': 0,
            'stealth_score': 0,
            'stealth_signals': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 1: Check if recently left big tech (required for all levels)
        left_big_tech, departure_info = self.recently_left_big_tech(employee)
        
        if not left_big_tech:
            return None  # Not eligible for any alert
        
        alert['departure_info'] = departure_info
        
        # Step 2: Calculate founder and stealth scores
        try:
            alert['founder_score'] = calculate_founder_potential_score(employee)
        except Exception as e:
            print(f"Error calculating founder score: {e}")
            alert['founder_score'] = 0
        
        try:
            stealth_score, stealth_signals, _ = self.stealth_detector.detect_stealth_signals(employee)
            alert['stealth_score'] = stealth_score
            alert['stealth_signals'] = stealth_signals[:3]  # Top 3 signals
        except Exception as e:
            print(f"Error calculating stealth score: {e}")
            alert['stealth_score'] = 0
            alert['stealth_signals'] = []
        
        # Step 3: Determine alert level (check highest priority first)
        
        # LEVEL 3: Joined qualified startup (HIGHEST)
        joined_startup, startup_info = self.joined_qualified_startup(employee)
        if joined_startup:
            alert['alert_level'] = 'LEVEL_3'
            alert['startup_info'] = startup_info
            alert['alert_reasons'].append(f"Joined qualified startup: {startup_info.get('startup_name')}")
            alert['priority_score'] = 100 + alert['founder_score']  # Base 100 + founder score
            
            # Add context
            if departure_info:
                alert['alert_reasons'].append(
                    f"Previously at {departure_info['company']} ({departure_info['days_ago']} days ago)"
                )
            
            return alert
        
        # LEVEL 2: Building signals OR high scores
        has_phrases, building_phrases = self.has_building_phrases(employee)
        
        # Check for Level 2 criteria
        is_level_2 = False
        
        # Criteria 2A: Has building phrases
        if has_phrases:
            alert['building_phrases'] = building_phrases
            alert['alert_reasons'].append(f"Building signals: {', '.join(building_phrases[:2])}")
            is_level_2 = True
        
        # Criteria 2B: High founder + stealth scores
        if alert['founder_score'] >= 4.5 and alert['stealth_score'] >= 50:
            alert['alert_reasons'].append(
                f"High confidence scores (Founder: {alert['founder_score']:.1f}, Stealth: {alert['stealth_score']:.0f})"
            )
            is_level_2 = True
        
        if is_level_2:
            alert['alert_level'] = 'LEVEL_2'
            # Priority within Level 2 based on combined scores
            alert['priority_score'] = 50 + (alert['founder_score'] * 3) + (alert['stealth_score'] / 2)
            
            # Add departure context
            if departure_info:
                alert['alert_reasons'].append(
                    f"Left {departure_info['company']} {departure_info['days_ago']} days ago"
                )
            
            return alert
        
        # LEVEL 1: Just left big tech (baseline monitoring)
        alert['alert_level'] = 'LEVEL_1'
        alert['alert_reasons'].append(
            f"Recently left {departure_info['company']} ({departure_info['days_ago']} days ago)"
        )
        
        # Add potential indicators even if not Level 2
        if alert['founder_score'] >= 4.5:
            alert['alert_reasons'].append(f"Qualified founder (score: {alert['founder_score']:.1f})")
        
        if alert['stealth_score'] >= 30:
            alert['alert_reasons'].append(f"Some stealth signals (score: {alert['stealth_score']:.0f})")
        
        # Priority within Level 1 based on founder score and recency
        recency_bonus = max(0, 30 - (departure_info['days_ago'] / 6))  # More recent = higher bonus
        alert['priority_score'] = alert['founder_score'] + recency_bonus
        
        return alert
    
    def analyze_employees(self, employees: List[Dict]) -> Dict[str, Any]:
        """
        Analyze multiple employees and categorize by alert level
        
        Returns comprehensive results with statistics
        """
        results = {
            'LEVEL_3': [],
            'LEVEL_2': [],
            'LEVEL_1': [],
            'stats': {
                'total_analyzed': len(employees),
                'eligible_for_alerts': 0,
                'level_3_count': 0,
                'level_2_count': 0,
                'level_1_count': 0,
                'avg_founder_score': 0,
                'avg_stealth_score': 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        total_founder_score = 0
        total_stealth_score = 0
        
        for employee in employees:
            try:
                alert = self.calculate_alert_level(employee)
                
                if alert:
                    results[alert['alert_level']].append(alert)
                    results['stats'][f"{alert['alert_level'].lower()}_count"] += 1
                    results['stats']['eligible_for_alerts'] += 1
                    
                    total_founder_score += alert['founder_score']
                    total_stealth_score += alert['stealth_score']
                    
            except Exception as e:
                print(f"Error analyzing employee {employee.get('full_name', 'Unknown')}: {e}")
                continue
        
        # Calculate averages
        if results['stats']['eligible_for_alerts'] > 0:
            results['stats']['avg_founder_score'] = round(
                total_founder_score / results['stats']['eligible_for_alerts'], 2
            )
            results['stats']['avg_stealth_score'] = round(
                total_stealth_score / results['stats']['eligible_for_alerts'], 2
            )
        
        # Sort each level by priority score
        for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
            results[level].sort(key=lambda x: x['priority_score'], reverse=True)
        
        return results
    
    def format_alert_message(self, alert: Dict) -> str:
        """
        Format an alert for display or notification
        """
        level_info = self.alert_levels[alert['alert_level']]
        
        message = f"""
{'='*60}
🚨 {level_info['name']} Alert
{'='*60}
Name: {alert['full_name']}
Alert Level: {alert['alert_level']} ({level_info['action']})
Priority Score: {alert['priority_score']:.1f}

Reasons:
{chr(10).join(f"  • {reason}" for reason in alert['alert_reasons'])}

Scores:
  - Founder Score: {alert['founder_score']:.1f}/10
  - Stealth Score: {alert['stealth_score']:.0f}/100
"""
        
        if alert.get('building_phrases'):
            message += f"\nBuilding Phrases Detected:\n"
            message += chr(10).join(f"  • {phrase}" for phrase in alert['building_phrases'])
        
        if alert.get('stealth_signals'):
            message += f"\nStealth Signals:\n"
            message += chr(10).join(f"  • {signal}" for signal in alert['stealth_signals'])
        
        if alert.get('startup_info'):
            info = alert['startup_info']
            message += f"\nStartup Details:\n"
            message += f"  • Name: {info.get('startup_name')}\n"
            message += f"  • Tech Score: {info.get('tech_score')}\n"
            message += f"  • Size: {info.get('size')}\n"
        
        message += f"\nTimestamp: {alert['timestamp']}\n"
        message += '='*60
        
        return message
    
    def save_alerts(self, results: Dict, output_path: str = None):
        """Save alert results to JSON file"""
        if output_path is None:
            output_dir = os.path.join(project_root, 'data', 'alerts')
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_dir, f'alerts_{timestamp}.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved alerts to: {output_path}")
        return output_path


# Test function
def test_alert_system():
    """Test the three-level alert system"""
    
    print("\n" + "="*80)
    print("TESTING THREE-LEVEL ALERT SYSTEM")
    print("="*80)
    
    # Initialize system
    alert_system = ThreeLevelAlertSystem()
    
    # Test employees
    test_employees = [
        {
            'pdl_id': 'test1',
            'full_name': 'John Doe',
            'job_company_name': 'Stealth Startup',
            'job_title': 'Co-founder & CTO',
            'last_big_tech_departure': {
                'company': 'OpenAI',
                'departure_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            }
        },
        {
            'pdl_id': 'test2',
            'full_name': 'Jane Smith',
            'job_company_name': 'saasrooms',  # From qualified startups
            'last_big_tech_departure': {
                'company': 'Google',
                'departure_date': (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
            }
        },
        {
            'pdl_id': 'test3',
            'full_name': 'Bob Wilson',
            'job_company_name': 'Consulting',
            'job_title': 'Working on something exciting',
            'last_big_tech_departure': {
                'company': 'Meta',
                'departure_date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
            }
        },
        {
            'pdl_id': 'test4',
            'full_name': 'Alice Chen',
            'job_company_name': 'Microsoft',  # Didn't leave
            'last_big_tech_departure': None
        }
    ]
    
    # Analyze
    results = alert_system.analyze_employees(test_employees)
    
    # Display results
    print("\n📊 ANALYSIS RESULTS:")
    print(f"Total analyzed: {results['stats']['total_analyzed']}")
    print(f"Eligible for alerts: {results['stats']['eligible_for_alerts']}")
    print(f"Level 3 (Joined Startup): {results['stats']['level_3_count']}")
    print(f"Level 2 (Building Signals): {results['stats']['level_2_count']}")
    print(f"Level 1 (Recently Left): {results['stats']['level_1_count']}")
    
    # Show alerts by level
    for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
        if results[level]:
            print(f"\n{level} ALERTS:")
            for alert in results[level]:
                print(f"  • {alert['full_name']}: {alert['alert_reasons'][0]}")
    
    print("\n✅ Alert system test completed successfully!")


if __name__ == "__main__":
    test_alert_system()