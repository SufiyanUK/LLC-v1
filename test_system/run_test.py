#!/usr/bin/env python3
"""
Simple test runner for the Employee Tracker system
Cross-platform alternative to the batch file
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("EMPLOYEE TRACKER TEST SYSTEM")
    print("=" * 60)
    print("\nThis will test the departure detection and")
    print("alert classification system without using")
    print("any PDL credits.\n")
    
    input("Press Enter to start the test...")
    
    # Get the directory of this script
    test_dir = Path(__file__).parent
    
    # Run the test
    try:
        result = subprocess.run(
            [sys.executable, "test_departure_system.py"],
            cwd=test_dir,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ All tests passed successfully!")
        else:
            print("\n❌ Some tests failed. Please review the output above.")
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    
    input("\nPress Enter to exit...")
    return 0

if __name__ == "__main__":
    sys.exit(main())