"""
Run departure check without interaction
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.test_departure_check import TestDepartureChecker

def main():
    print("\n[RUNNING DEPARTURE CHECK]")
    print("="*60)
    
    checker = TestDepartureChecker()
    departures = checker.run_test_check()
    
    if departures:
        print(f"\n[RESULTS] Found {len(departures)} departures")
        
        # Show Level 2 departures specifically
        level2_deps = [d for d in departures if d.get('alert_level') == 2]
        if level2_deps:
            print(f"\n[LEVEL 2 ALERTS DETECTED]: {len(level2_deps)}")
            for dep in level2_deps:
                print(f"  - {dep['name']}")
                print(f"    From: {dep['old_company']} -> To: {dep['new_company']}")
                print(f"    Headline: {dep.get('headline', 'N/A')}")
                if dep.get('alert_signals'):
                    print(f"    Signals: {', '.join(dep['alert_signals'][:3])}")
    else:
        print("\n[RESULTS] No departures detected")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()