"""
Test Level 2 Alert Classification
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.departure_classifier import DepartureClassifier

def test_level2_classification():
    """Test that Level 2 alerts are properly classified"""
    
    classifier = DepartureClassifier()
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Level 2 - Independent Consultant',
            'departure': {
                'old_company': 'OpenAI',
                'new_company': 'Independent Consultant',
                'headline': 'Building something new in AI | Ex-OpenAI',
                'summary': 'Working on exciting stealth project',
                'job_company_size': '',
                'job_company_type': ''
            },
            'expected': 2
        },
        {
            'name': 'Level 2 - Stealth Mode',
            'departure': {
                'old_company': 'Anthropic',
                'new_company': 'Stealth Mode',
                'headline': 'Working on something new | Ex-Anthropic',
                'summary': 'Building in stealth. Stay tuned!',
                'job_company_size': '',
                'job_company_type': ''
            },
            'expected': 2
        },
        {
            'name': 'Level 3 - Small Startup',
            'departure': {
                'old_company': 'Meta',
                'new_company': 'TinyAI Startup',
                'headline': 'CTO at TinyAI',
                'job_company_size': '1-10',
                'job_company_type': 'startup',
                'job_company_founded': '2024'
            },
            'expected': 3
        },
        {
            'name': 'Level 1 - Big Tech',
            'departure': {
                'old_company': 'Google',
                'new_company': 'Microsoft',
                'headline': 'Principal Engineer at Microsoft',
                'job_company_size': '10000+',
                'job_company_type': 'technology'
            },
            'expected': 1
        }
    ]
    
    print("\n" + "="*60)
    print("TESTING ALERT LEVEL CLASSIFICATION")
    print("="*60)
    
    all_passed = True
    
    for test in test_cases:
        level, signals = classifier.classify_departure(test['departure'])
        
        if level == test['expected']:
            print(f"\n[PASS] {test['name']}")
            print(f"  Expected: Level {test['expected']}, Got: Level {level}")
        else:
            print(f"\n[FAIL] {test['name']}")
            print(f"  Expected: Level {test['expected']}, Got: Level {level}")
            all_passed = False
        
        if signals:
            print(f"  Signals: {', '.join(signals[:3])}")
    
    print("\n" + "="*60)
    if all_passed:
        print("[SUCCESS] All tests passed!")
    else:
        print("[ERROR] Some tests failed - check classification logic")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    test_level2_classification()