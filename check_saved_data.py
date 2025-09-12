"""
Check what tracking data is currently saved
"""

import json
from pathlib import Path

def check_saved_data():
    print("\n" + "="*60)
    print("CHECKING SAVED TRACKING DATA")
    print("="*60)
    
    # Check for tracking file
    tracking_file = Path(__file__).parent / 'data' / 'tracking' / 'tracked_employees.json'
    
    if tracking_file.exists():
        print(f"\n✓ Tracking file found: {tracking_file}")
        
        with open(tracking_file, 'r') as f:
            data = json.load(f)
        
        print(f"\nTracking Summary:")
        print(f"  Initialized: {data.get('initialized', 'Unknown')}")
        print(f"  Total tracked: {data.get('total_tracked', 0)}")
        print(f"  Companies: {list(data.get('companies', {}).keys())}")
        
        print(f"\nBy Company:")
        for company, info in data.get('companies', {}).items():
            print(f"  {company}: {info.get('count', 0)} employees")
        
        print(f"\nTracked Employees:")
        for pdl_id, emp in list(data.get('by_pdl_id', {}).items())[:10]:  # Show first 10
            print(f"  - {emp['name']} ({emp['title']}) @ {emp['company']} - Status: {emp['status']}")
        
        if data.get('total_tracked', 0) > 10:
            print(f"  ... and {data['total_tracked'] - 10} more")
            
    else:
        print(f"\n✗ No tracking file found at: {tracking_file}")
        print("  You need to initialize tracking first")
    
    # Check for departure history
    history_file = Path(__file__).parent / 'data' / 'tracking' / 'departure_history.jsonl'
    
    if history_file.exists():
        print(f"\n✓ Departure history found: {history_file}")
        
        departures = []
        with open(history_file, 'r') as f:
            for line in f:
                departures.append(json.loads(line))
        
        print(f"  Total departures recorded: {len(departures)}")
        for dep in departures[:5]:
            print(f"  - {dep['name']}: {dep['old_company']} → {dep['new_company']}")
    else:
        print(f"\n✗ No departure history yet")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_saved_data()