"""
Departure Alert Classifier
Classifies departures into 3 alert levels based on signals
"""

import json
import os
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class DepartureClassifier:
    """
    Classifies employee departures into 3 alert levels:
    Level 3 (RED): Joined startup/small company
    Level 2 (ORANGE): Building signals detected
    Level 1 (YELLOW): Standard departure from big tech
    """
    
    def __init__(self):
        # Load qualified startups
        self.qualified_startups = self._load_qualified_startups()
        
        # Big tech companies list
        self.big_tech_companies = [
            'openai', 'anthropic', 'deepmind', 'google deepmind', 'inflection ai',
            'character ai', 'cohere', 'hugging face', 'stability ai', 'midjourney',
            'mistral', 'mistral ai', 'perplexity', 'adept', 'aleph alpha',
            'google', 'alphabet', 'meta', 'facebook', 'microsoft', 'apple',
            'amazon', 'nvidia', 'tesla', 'netflix', 'adobe', 'salesforce',
            'palantir', 'databricks', 'scale ai', 'uber', 'airbnb', 'linkedin'
        ]
        
        # Building/stealth phrases to detect
        self.building_phrases = [
            # Direct building statements
            'building something new', 'building something cool', 'building something exciting',
            'building something big', 'building something special', 'building in stealth',
            'building the future', 'building next generation', 'building ai',
            
            # Working on variations
            'working on something new', 'working on something exciting', 'working on something cool',
            'working on something big', 'working on a new venture', 'working on a startup',
            'working on stealth', 'working on something special', 'working on the next',
            
            # Creating/Developing
            'creating something new', 'creating the future', 'developing something',
            'launching soon', 'launching startup', 'starting something new',
            'starting a company', 'new venture', 'new project',
            
            # Founder/Entrepreneur signals
            'founder', 'co-founder', 'cofounder', 'founding team', 'entrepreneur',
            'stealth', 'stealth mode', 'stealth startup', 'pre-launch', 'pre-seed',
            
            # Other signals
            'something new', 'stay tuned', 'more to come', 'exciting things',
            'big things coming', 'next chapter', 'new journey', 'new adventure',
            'exploring opportunities', 'taking a break', 'sabbatical'
        ]
        
        # Compile regex patterns for efficiency
        self.building_patterns = self._compile_patterns(self.building_phrases)
    
    def _load_qualified_startups(self) -> List[Dict]:
        """Load qualified startups from JSON file"""
        startup_file = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'qualified_startups.json'
        
        if startup_file.exists():
            try:
                with open(startup_file, 'r', encoding='utf-8') as f:
                    startups = json.load(f)
                    print(f"  Loaded {len(startups)} qualified startups for classification")
                    return startups
            except Exception as e:
                print(f"  Warning: Could not load qualified startups: {e}")
                return []
        return []
    
    def _compile_patterns(self, phrases: List[str]) -> List:
        """Compile regex patterns for efficient matching"""
        patterns = []
        for phrase in phrases:
            # Create case-insensitive pattern
            if len(phrase.split()) == 1:  # Single word
                pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            else:  # Multi-word phrase
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            patterns.append((phrase, pattern))
        return patterns
    
    def classify_departure(self, departure: Dict) -> Tuple[int, List[str]]:
        """
        Classify a departure into alert level with signals
        
        Returns:
            (alert_level, list_of_detected_signals)
        """
        signals = []
        
        # Check if they left big tech
        old_company = (departure.get('old_company', '') or '').lower()
        is_big_tech = any(tech in old_company for tech in self.big_tech_companies)
        
        if not is_big_tech:
            # Not from big tech, no alert
            return 0, []
        
        # They left big tech - at minimum Level 1
        alert_level = 1
        signals.append(f"Left {departure.get('old_company')}")
        
        # Check new company
        new_company = (departure.get('new_company', '') or '').lower()
        
        # LEVEL 3 CHECK: Joined a startup or small company
        if self._is_startup_or_small_company(departure):
            alert_level = 3
            
            # Check if it's a known qualified startup
            if any(startup.get('name', '').lower() in new_company for startup in self.qualified_startups):
                signals.append(f"Joined qualified startup: {departure.get('new_company')}")
            else:
                # Check company size
                company_size = departure.get('job_company_size', '')
                if company_size:
                    try:
                        size = int(str(company_size).replace('+', '').replace(',', ''))
                        if size < 100:
                            signals.append(f"Joined small company ({size} employees)")
                    except:
                        pass
                
                # Check company type
                company_type = (departure.get('job_company_type', '') or '').lower()
                if 'startup' in company_type or 'early stage' in company_type:
                    signals.append(f"Joined {company_type}")
                
                # Check if tech/AI company
                industry = (departure.get('job_company_industry', '') or '').lower()
                if any(term in industry for term in ['technology', 'software', 'ai', 'artificial intelligence', 'machine learning']):
                    signals.append(f"Tech/AI company: {industry}")
        
        # LEVEL 2 CHECK: Building signals (only if not already Level 3)
        if alert_level < 3:
            building_signals = self._detect_building_signals(departure)
            if building_signals:
                alert_level = 2
                signals.extend(building_signals)
        
        return alert_level, signals
    
    def _is_startup_or_small_company(self, departure: Dict) -> bool:
        """Check if the new company is a startup or small company"""
        new_company = (departure.get('new_company', '') or '').lower()
        
        # Check if it's building/consulting first (these should be Level 2, not 3)
        if any(term in new_company for term in ['consultant', 'consulting', 'freelance', 'advisor', 'stealth mode', 'independent']):
            return False  # These are Level 2 candidates
        
        # Unknown company often means stealth or very early
        if new_company in ['unknown', '', 'n/a', 'self-employed', 'self employed']:
            # Check if they have founder/CEO title - that's Level 3
            job_title = (departure.get('job_title', '') or departure.get('new_title', '')).lower()
            if any(term in job_title for term in ['ceo', 'founder', 'co-founder', 'cofounder']):
                return True  # CEO/Founder with no company = stealth startup (Level 3)
            # Otherwise check if they have building signals - if so, Level 2 is more appropriate
            if self._detect_building_signals(departure):
                return False  # Has building signals, should be Level 2
            return True  # No signals, assume startup
        
        # Check against qualified startups
        if any(startup.get('name', '').lower() in new_company for startup in self.qualified_startups):
            return True
        
        # Check company size
        company_size = departure.get('job_company_size', '')
        if company_size:
            try:
                size = int(str(company_size).replace('+', '').replace(',', '').split('-')[0])
                if size < 100:
                    return True
            except:
                pass
        
        # Check company type
        company_type = (departure.get('job_company_type', '') or '').lower()
        if any(term in company_type for term in ['startup', 'early stage', 'seed', 'series a', 'pre-seed']):
            return True
        
        # Check founded date (companies less than 5 years old)
        founded = departure.get('job_company_founded', '')
        if founded:
            try:
                founded_year = int(str(founded)[:4])
                if founded_year > 2019:
                    return True
            except:
                pass
        
        return False
    
    def _detect_building_signals(self, departure: Dict) -> List[str]:
        """Detect building/founder signals in profile text"""
        detected_signals = []
        
        # Fields to check
        fields_to_check = [
            ('headline', departure.get('headline', '')),
            ('summary', departure.get('summary', '')),
            ('job_summary', departure.get('job_summary', '')),
            ('new_title', departure.get('new_title', ''))
        ]
        
        # Check each field for building phrases
        for field_name, field_text in fields_to_check:
            if not field_text:
                continue
                
            for phrase, pattern in self.building_patterns:
                if pattern.search(field_text):
                    detected_signals.append(f'"{phrase}" in {field_name}')
                    break  # Only report first match per field
        
        # Check for founder/entrepreneur in title
        title = (departure.get('new_title', '') or '').lower()
        if any(term in title for term in ['founder', 'co-founder', 'cofounder', 'entrepreneur', 'ceo', 'chief executive']):
            detected_signals.append(f'Founder/CEO title: {departure.get("new_title")}')
        
        return detected_signals
    
    def classify_all_departures(self, departures: List[Dict]) -> List[Dict]:
        """
        Classify all departures and add alert levels
        
        Returns:
            List of departures with alert_level and alert_signals added
        """
        classified = []
        
        level_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        
        for departure in departures:
            alert_level, signals = self.classify_departure(departure)
            
            departure['alert_level'] = alert_level
            departure['alert_signals'] = signals
            
            level_counts[alert_level] += 1
            
            if alert_level > 0:
                classified.append(departure)
                
                # Print classification
                level_names = {
                    3: "[LEVEL 3] (Startup)",
                    2: "[LEVEL 2] (Building)",
                    1: "[LEVEL 1] (Departed)"
                }
                
                print(f"    {level_names.get(alert_level)}: {departure['name']}")
                if signals and alert_level > 1:
                    print(f"      Signals: {', '.join(signals[:3])}")
        
        # Print summary
        if classified:
            print(f"\n  Alert Summary:")
            if level_counts[3] > 0:
                print(f"    [LEVEL 3] (Startup): {level_counts[3]}")
            if level_counts[2] > 0:
                print(f"    [LEVEL 2] (Building): {level_counts[2]}")
            if level_counts[1] > 0:
                print(f"    [LEVEL 1] (Departed): {level_counts[1]}")
        
        return classified