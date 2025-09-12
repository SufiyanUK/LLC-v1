"""
Quick script to fix existing LinkedIn URLs in the database
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from scripts.database import TrackingDatabase

def main():
    print("Fixing LinkedIn URLs in database...")
    
    db = TrackingDatabase()
    fixed = db.fix_existing_linkedin_urls()
    
    print(f"Fixed {fixed} LinkedIn URLs")
    print("Done!")

if __name__ == "__main__":
    main()