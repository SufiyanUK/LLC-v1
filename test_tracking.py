"""
Test the employee tracking system with minimal credits
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from scripts.employee_tracker import EmployeeTracker

def test_tracking():
    """Test with 2 employees from OpenAI"""
    
    print("\n" + "="*60)
    print("TESTING EMPLOYEE TRACKER")
    print("="*60)
    
    tracker = EmployeeTracker()
    
    # Test with just OpenAI, 2 employees
    config = {'openai': 2}
    
    print(f"\nTest config: {config}")
    print("This will use only 2 credits")
    
    confirm = input("\nProceed? (y/n): ")
    if confirm.lower() != 'y':
        print("Test cancelled")
        return
    
    # Initialize tracking
    result = tracker.initialize_tracking(config)
    
    print(f"\n[RESULTS]")
    print(f"Total tracked: {result['total_tracked']}")
    print(f"Companies: {list(result['companies'].keys())}")
    
    # Show status
    status = tracker.get_tracking_status()
    print(f"\n[STATUS]")
    print(f"Active employees: {status['active']}")
    print(f"Companies tracked: {status['companies']}")
    
    # Show tracked employees
    tracking_data = tracker.load_tracking_data()
    if tracking_data:
        print(f"\n[TRACKED EMPLOYEES]")
        for pdl_id, emp in tracking_data['by_pdl_id'].items():
            print(f"- {emp['name']}: {emp['title']} at {emp['company']}")

if __name__ == "__main__":
    test_tracking()