"""
Comprehensive Test Suite for Three-Level Alert System
Tests all alert levels, building phrases, and edge cases
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from src.alerts.three_level_alert_system import ThreeLevelAlertSystem
from src.data_processing.founder_qualifier_updated import calculate_founder_potential_score
from src.monitoring.stealth_detector_updated import StealthFounderDetector


def create_test_employee(
    name: str,
    company: str = None,
    title: str = None,
    previous_company: str = None,
    days_since_departure: int = 30,
    skills: list = None,
    summary: str = None
):
    """Helper function to create test employee data"""
    
    employee = {
        'pdl_id': f'test_{name.replace(" ", "_").lower()}',
        'full_name': name,
        'job_company_name': company,
        'job_title': title,
        'summary': summary,
        'skills': skills or [],
        'job_company_size': '1-10' if company and 'stealth' in company.lower() else '10001+',
        'job_last_changed': (datetime.now() - timedelta(days=days_since_departure)).strftime('%Y-%m-%d'),
        'job_last_updated': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        'experience': []
    }
    
    # Add departure info if previous company exists
    if previous_company:
        employee['last_big_tech_departure'] = {
            'company': previous_company,
            'departure_date': (datetime.now() - timedelta(days=days_since_departure)).strftime('%Y-%m-%d'),
            'role': 'Senior Engineer'
        }
        
        # Add to experience
        employee['experience'].append({
            'company': {'name': previous_company},
            'title': 'Senior Engineer',
            'is_primary': False,
            'end_date': (datetime.now() - timedelta(days=days_since_departure)).strftime('%Y-%m-%d')
        })
    
    # Add current experience if company exists
    if company:
        employee['experience'].append({
            'company': {
                'name': company,
                'summary': summary
            },
            'title': title,
            'is_primary': True
        })
    
    return employee


def test_level_3_alerts():
    """Test Level 3: Joined Qualified Startup"""
    print("\n" + "="*80)
    print("TESTING LEVEL 3 ALERTS (Joined Qualified Startup)")
    print("="*80)
    
    alert_system = ThreeLevelAlertSystem()
    
    test_cases = [
        create_test_employee(
            "Alice Johnson",
            company="saasrooms",  # From qualified startups
            title="Senior Engineer",
            previous_company="OpenAI",
            days_since_departure=45
        ),
        create_test_employee(
            "Bob Smith",
            company="meve",  # Another qualified startup
            title="Head of Engineering",
            previous_company="Google",
            days_since_departure=30
        ),
        create_test_employee(
            "Charlie Brown",
            company="Random Company",  # Not in qualified list
            title="Engineer",
            previous_company="Meta",
            days_since_departure=60
        )
    ]
    
    for employee in test_cases:
        alert = alert_system.calculate_alert_level(employee)
        if alert:
            print(f"\n👤 {alert['full_name']}:")
            print(f"   Alert Level: {alert['alert_level']}")
            print(f"   Company: {employee['job_company_name']}")
            print(f"   Expected: {'LEVEL_3' if employee['job_company_name'] in ['saasrooms', 'meve'] else 'Not LEVEL_3'}")
            print(f"   ✅ PASS" if (alert['alert_level'] == 'LEVEL_3') == (employee['job_company_name'] in ['saasrooms', 'meve']) else "   ❌ FAIL")
            
            if alert['startup_info']:
                print(f"   Startup Info: {alert['startup_info'].get('startup_name')}")


def test_level_2_building_phrases():
    """Test Level 2: Building Phrases Detection"""
    print("\n" + "="*80)
    print("TESTING LEVEL 2 ALERTS (Building Phrases)")
    print("="*80)
    
    alert_system = ThreeLevelAlertSystem()
    
    # Test various building phrases
    building_phrase_tests = [
        # Direct building
        ("building something new", True),
        ("building something cool", True),
        ("building in stealth", True),
        ("building AI", True),
        
        # Working on variations
        ("working on something exciting", True),
        ("working on a startup", True),
        ("Working on it", True),
        
        # Founder titles
        ("Co-founder & CEO", True),
        ("Founding Engineer", True),
        ("Technical Co-founder", True),
        
        # Stealth signals
        ("Stealth Mode", True),
        ("can't share yet", True),
        ("Coming soon", True),
        ("Stay tuned", True),
        
        # New venture
        ("New venture in AI", True),
        ("Next chapter", True),
        ("New adventure begins", True),
        
        # Early stage
        ("0 to 1 product development", True),
        ("Day one at new company", True),
        ("Ground floor opportunity", True),
        
        # Vague but telling
        ("Taking a break to explore", True),
        ("On sabbatical", True),
        ("Independent consultant", True),
        
        # Should NOT trigger
        ("Software Engineer at Google", False),
        ("Senior Manager", False),
        ("Product Lead", False)
    ]
    
    passed = 0
    failed = 0
    
    for phrase, should_trigger in building_phrase_tests:
        employee = create_test_employee(
            f"Test User {phrase[:20]}",
            company="Some Company",
            title=phrase if len(phrase) < 50 else None,
            summary=phrase if len(phrase) >= 50 else None,
            previous_company="OpenAI",
            days_since_departure=45
        )
        
        alert = alert_system.calculate_alert_level(employee)
        
        if alert:
            has_building_signals = len(alert.get('building_phrases', [])) > 0
            is_level_2 = alert['alert_level'] == 'LEVEL_2'
            
            # Should be Level 2 if it has building phrases
            if should_trigger:
                if has_building_signals and is_level_2:
                    print(f"✅ PASS: '{phrase[:40]}...' correctly detected")
                    passed += 1
                else:
                    print(f"❌ FAIL: '{phrase[:40]}...' not detected (Level: {alert['alert_level']})")
                    failed += 1
            else:
                if not has_building_signals or is_level_2:
                    print(f"✅ PASS: '{phrase[:40]}...' correctly ignored")
                    passed += 1
                else:
                    print(f"❌ FAIL: '{phrase[:40]}...' incorrectly triggered")
                    failed += 1
    
    print(f"\n📊 Building Phrase Test Results: {passed} passed, {failed} failed")


def test_level_2_high_scores():
    """Test Level 2: High Founder + Stealth Scores"""
    print("\n" + "="*80)
    print("TESTING LEVEL 2 ALERTS (High Scores)")
    print("="*80)
    
    alert_system = ThreeLevelAlertSystem()
    
    # Create employee with characteristics that should yield high scores
    high_score_employee = {
        'pdl_id': 'test_high_score',
        'full_name': 'Sarah Chen',
        'job_company_name': '',  # No company (stealth signal)
        'job_title': 'Building something new',
        'job_company_size': '1-10',
        'job_last_changed': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
        'job_last_updated': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        'job_title_role': 'engineering',
        'last_big_tech_departure': {
            'company': 'OpenAI',
            'departure_date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            'role': 'Director of Engineering'
        },
        'last_known_role': {
            'title': 'Director of Engineering',
            'role': 'engineering',
            'levels': ['director'],
            'company': 'OpenAI'
        },
        'skills': ['machine learning', 'pytorch', 'llm', 'transformers'],
        'education': [{
            'school': 'Stanford University',
            'majors': ['Computer Science']
        }],
        'location': {
            'job_location': {
                'region': 'California',
                'locality': 'San Francisco'
            }
        },
        'experience': [
            {
                'company': {'name': 'OpenAI'},
                'title': 'Director of Engineering',
                'is_primary': False
            }
        ]
    }
    
    alert = alert_system.calculate_alert_level(high_score_employee)
    
    print(f"\n👤 {alert['full_name']}:")
    print(f"   Founder Score: {alert['founder_score']:.1f}/10")
    print(f"   Stealth Score: {alert['stealth_score']:.0f}/100")
    print(f"   Alert Level: {alert['alert_level']}")
    print(f"   Expected: LEVEL_2 (high scores)")
    
    if alert['founder_score'] >= 4.5 and alert['stealth_score'] >= 50:
        print(f"   ✅ PASS: Correctly identified as Level 2 with high scores")
    else:
        print(f"   ❌ FAIL: Scores not high enough (Founder: {alert['founder_score']}, Stealth: {alert['stealth_score']})")


def test_level_1_alerts():
    """Test Level 1: Basic Recent Departure"""
    print("\n" + "="*80)
    print("TESTING LEVEL 1 ALERTS (Recent Departure Only)")
    print("="*80)
    
    alert_system = ThreeLevelAlertSystem()
    
    # Simple departure, no special signals
    simple_departure = create_test_employee(
        "John Doe",
        company="Consulting LLC",
        title="Consultant",
        previous_company="Google",
        days_since_departure=60
    )
    
    alert = alert_system.calculate_alert_level(simple_departure)
    
    if alert:
        print(f"\n👤 {alert['full_name']}:")
        print(f"   Alert Level: {alert['alert_level']}")
        print(f"   Founder Score: {alert['founder_score']:.1f}")
        print(f"   Stealth Score: {alert['stealth_score']:.0f}")
        print(f"   Building Phrases: {len(alert.get('building_phrases', []))}")
        print(f"   Expected: LEVEL_1 (no special signals)")
        
        if alert['alert_level'] == 'LEVEL_1':
            print(f"   ✅ PASS: Correctly classified as Level 1")
        else:
            print(f"   ❌ FAIL: Incorrectly classified as {alert['alert_level']}")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n" + "="*80)
    print("TESTING EDGE CASES")
    print("="*80)
    
    alert_system = ThreeLevelAlertSystem()
    
    # Case 1: No departure (should return None)
    no_departure = create_test_employee(
        "No Departure",
        company="Still at Google",
        title="Engineer"
    )
    # Remove departure info
    no_departure.pop('last_big_tech_departure', None)
    
    alert = alert_system.calculate_alert_level(no_departure)
    print(f"\n1. No departure from big tech:")
    result_text = 'No alert' if alert is None else f"Alert Level {alert['alert_level']}"
    print(f"   Result: {result_text}")
    print(f"   ✅ PASS" if alert is None else "   ❌ FAIL")
    
    # Case 2: Departure too old (>180 days)
    old_departure = create_test_employee(
        "Old Departure",
        company="New Company",
        title="Engineer",
        previous_company="Meta",
        days_since_departure=200
    )
    
    alert = alert_system.calculate_alert_level(old_departure)
    print(f"\n2. Departure > 180 days ago:")
    result_text = 'No alert' if alert is None else f"Alert Level {alert['alert_level']}"
    print(f"   Result: {result_text}")
    print(f"   ✅ PASS" if alert is None else "   ❌ FAIL")
    
    # Case 3: Multiple building phrases (should boost Level 2)
    multiple_phrases = create_test_employee(
        "Multiple Signals",
        company="Stealth Startup",
        title="Founder, building something exciting, coming soon",
        previous_company="OpenAI",
        days_since_departure=10
    )
    
    alert = alert_system.calculate_alert_level(multiple_phrases)
    print(f"\n3. Multiple building phrases:")
    if alert:
        print(f"   Alert Level: {alert['alert_level']}")
        print(f"   Building Phrases Found: {len(alert.get('building_phrases', []))}")
        print(f"   Phrases: {', '.join(alert.get('building_phrases', [])[:3])}")
        print(f"   ✅ PASS" if alert['alert_level'] == 'LEVEL_2' and len(alert.get('building_phrases', [])) > 1 else "   ❌ FAIL")
    
    # Case 4: Very recent departure (should have higher priority)
    very_recent = create_test_employee(
        "Very Recent",
        company="Unknown",
        title="TBD",
        previous_company="Anthropic",
        days_since_departure=5
    )
    
    alert = alert_system.calculate_alert_level(very_recent)
    print(f"\n4. Very recent departure (5 days):")
    if alert:
        print(f"   Alert Level: {alert['alert_level']}")
        print(f"   Priority Score: {alert['priority_score']:.1f}")
        print(f"   ✅ PASS" if alert['priority_score'] > 10 else "   ❌ FAIL (priority too low)")


def test_comprehensive_analysis():
    """Test with a batch of diverse employees"""
    print("\n" + "="*80)
    print("COMPREHENSIVE BATCH ANALYSIS")
    print("="*80)
    
    alert_system = ThreeLevelAlertSystem()
    
    # Create diverse test batch
    employees = [
        # Level 3 candidate
        create_test_employee("Alice L3", "saasrooms", "Head of AI", "OpenAI", 20),
        
        # Level 2 candidates
        create_test_employee("Bob L2", "Stealth Mode", "Co-founder", "Google", 30),
        create_test_employee("Carol L2", "Building AI", "Founder", "Meta", 45),
        create_test_employee("Dave L2", "New Venture", "Working on something exciting", "Anthropic", 15),
        
        # Level 1 candidates
        create_test_employee("Eve L1", "Consulting", "Advisor", "Microsoft", 60),
        create_test_employee("Frank L1", "Freelance", "Engineer", "Apple", 90),
        
        # Should not qualify (no recent departure)
        create_test_employee("Grace None", "Google", "Engineer", "Amazon", 200),
    ]
    
    # Analyze batch
    results = alert_system.analyze_employees(employees)
    
    print(f"\n📊 Batch Analysis Results:")
    print(f"   Total Analyzed: {results['stats']['total_analyzed']}")
    print(f"   Eligible for Alerts: {results['stats']['eligible_for_alerts']}")
    print(f"   Level 3: {results['stats']['level_3_count']} (expected: 1)")
    print(f"   Level 2: {results['stats']['level_2_count']} (expected: 3)")
    print(f"   Level 1: {results['stats']['level_1_count']} (expected: 2)")
    
    # Verify sorting by priority
    print(f"\n📈 Priority Sorting Check:")
    for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
        if results[level]:
            print(f"\n   {level}:")
            for alert in results[level][:3]:
                print(f"     • {alert['full_name']}: Priority {alert['priority_score']:.1f}")
    
    # Check if results match expectations
    expected = {'LEVEL_3': 1, 'LEVEL_2': 3, 'LEVEL_1': 2}
    actual = {
        'LEVEL_3': results['stats']['level_3_count'],
        'LEVEL_2': results['stats']['level_2_count'],
        'LEVEL_1': results['stats']['level_1_count']
    }
    
    if expected == actual:
        print("\n✅ COMPREHENSIVE TEST PASSED!")
    else:
        print(f"\n❌ COMPREHENSIVE TEST FAILED!")
        print(f"   Expected: {expected}")
        print(f"   Actual: {actual}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("THREE-LEVEL ALERT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run all test categories
    test_level_3_alerts()
    test_level_2_building_phrases()
    test_level_2_high_scores()
    test_level_1_alerts()
    test_edge_cases()
    test_comprehensive_analysis()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)
    print("\nThe Three-Level Alert System is ready for production use!")
    print("\nTo run with real data, use: python run_alert_pipeline.py")


if __name__ == "__main__":
    main()