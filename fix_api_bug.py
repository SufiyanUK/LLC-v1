"""
Fix for the API bug in api_v2.py
The add_company_to_tracking method returns a Dict, but the API treats it as a boolean
"""

import os
import sys
from pathlib import Path

# Path to api_v2.py
api_file = Path(__file__).parent / "api_v2.py"

def show_current_issue():
    """Show the current problematic code"""
    print("\n" + "="*60)
    print("CURRENT BUG IN api_v2.py (line 219)")
    print("="*60)
    print("""
The issue is here:
    success = tracker.add_company_to_tracking(config.company, config.employee_count)
    if success:  # <-- This treats Dict as boolean!

But add_company_to_tracking returns:
    return {'success': True, 'added': 5, 'updated': 0, 'total_tracked': 30}

The fix:
    result = tracker.add_company_to_tracking(config.company, config.employee_count)
    if result.get('success'):  # <-- Properly check the 'success' key
    """)

def fix_api_file():
    """Apply the fix to api_v2.py"""
    print("\n" + "="*60)
    print("APPLYING FIX")
    print("="*60)

    # Read the file with UTF-8 encoding
    with open(api_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find and fix the issue (around line 219)
    fixed = False
    for i, line in enumerate(lines):
        if "success = tracker.add_company_to_tracking" in line:
            # Replace this line
            lines[i] = "    result = tracker.add_company_to_tracking(config.company, config.employee_count)\n"

            # Fix the next line too (the if statement)
            if i + 1 < len(lines) and "if success:" in lines[i + 1]:
                lines[i + 1] = "    \n    if result and result.get('success'):\n"
                fixed = True
                print(f"✓ Fixed line {i+1}: Changed 'success' to 'result'")
                print(f"✓ Fixed line {i+2}: Changed 'if success:' to 'if result and result.get('success'):'")

                # Also update the return statement to use actual added count
                for j in range(i+2, min(i+15, len(lines))):
                    if '"message": f"Added {config.employee_count}' in lines[j]:
                        lines[j] = lines[j].replace(
                            'f"Added {config.employee_count} employees',
                            'f"Added {result.get(\'added\', 0)} employees'
                        )
                        print(f"✓ Fixed line {j+1}: Updated message to show actual added count")
                        break
                break

    if fixed:
        # Write the fixed file with UTF-8 encoding
        with open(api_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("\n✅ Successfully fixed api_v2.py!")
        print("   The add_company_to_tracking endpoint should now work correctly.")
    else:
        print("\n⚠️ Could not find the bug - it may have already been fixed.")

def verify_fix():
    """Verify the fix was applied"""
    print("\n" + "="*60)
    print("VERIFYING FIX")
    print("="*60)

    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if "result = tracker.add_company_to_tracking" in content and "result.get('success')" in content:
        print("✅ Fix verified! The API should now work correctly.")
        return True
    else:
        print("⚠️ Fix not found in file.")
        return False

def main():
    print("\n" + "="*60)
    print("API BUG FIX SCRIPT")
    print("="*60)
    print("\nThis script fixes a bug in api_v2.py where:")
    print("- add_company_to_tracking returns a Dict")
    print("- But the API treats it as a boolean")
    print("- This causes employees to be added but not shown")

    show_current_issue()

    # Check if file exists
    if not api_file.exists():
        print(f"\n❌ Error: {api_file} not found!")
        return

    # Apply the fix
    response = input("\nApply the fix? (yes/no): ").lower()
    if response == 'yes':
        fix_api_file()
        verify_fix()

        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("\n1. Commit and push this fix to GitHub:")
        print("   git add api_v2.py")
        print("   git commit -m 'Fix add_company_to_tracking return value handling'")
        print("   git push")
        print("\n2. Railway will auto-deploy the fix")
        print("\n3. Your employees should now appear correctly!")
    else:
        print("\n❌ Fix not applied.")

if __name__ == "__main__":
    main()