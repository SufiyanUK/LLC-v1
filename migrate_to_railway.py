"""
Migrate employees from local SQLite to Railway PostgreSQL
This will copy all your local employees to Railway
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def migrate_employees():
    """Migrate all employees from local SQLite to Railway PostgreSQL"""

    print("\n" + "="*60)
    print("MIGRATING LOCAL EMPLOYEES TO RAILWAY")
    print("="*60)

    # Step 1: Load from LOCAL SQLite (temporarily disable DATABASE_URL)
    database_url = os.environ.pop('DATABASE_URL', None)

    if not database_url:
        print("❌ No DATABASE_URL found in environment")
        print("   Please set DATABASE_URL to your Railway PostgreSQL URL")
        return

    print("\n1. Loading from LOCAL SQLite database...")

    try:
        # Import WITHOUT DATABASE_URL to force SQLite
        from scripts.database import TrackingDatabase as LocalDB
        local_db = LocalDB()

        # Get all employees from local
        local_employees = local_db.get_all_employees()
        print(f"   ✓ Found {len(local_employees)} employees in local SQLite")

        if not local_employees:
            print("   ⚠️ No employees found in local database!")
            return

        # Show sample
        print("\n   Sample of employees to migrate:")
        for emp in local_employees[:5]:
            print(f"   - {emp.get('name')} ({emp.get('company')})")

        if len(local_employees) > 5:
            print(f"   ... and {len(local_employees) - 5} more")

    except Exception as e:
        print(f"   ❌ Error loading local database: {e}")
        return

    # Step 2: Connect to Railway PostgreSQL
    print("\n2. Connecting to Railway PostgreSQL...")

    # Restore DATABASE_URL
    os.environ['DATABASE_URL'] = database_url

    try:
        # Force reimport with DATABASE_URL set
        import importlib
        import scripts.database_factory
        importlib.reload(scripts.database_factory)

        from scripts.database_factory import TrackingDatabase as RemoteDB
        remote_db = RemoteDB()

        # Check current state
        remote_stats = remote_db.get_statistics()
        print(f"   ✓ Connected to Railway PostgreSQL")
        print(f"   Current employees in Railway: {remote_stats.get('total_tracked', 0)}")

    except Exception as e:
        print(f"   ❌ Error connecting to Railway: {e}")
        return

    # Step 3: Migrate employees
    print("\n3. Migrating employees...")

    successful = 0
    failed = 0
    updated = 0

    for i, emp in enumerate(local_employees, 1):
        try:
            # Prepare employee data in the format add_employees expects
            emp_data = [{
                'id': emp.get('pdl_id'),
                'full_name': emp.get('name'),
                'job_title': emp.get('title', ''),
                'job_company_name': emp.get('current_company') or emp.get('company', ''),
                'linkedin_url': emp.get('linkedin_url', ''),
                'job_last_changed': emp.get('job_last_changed', ''),
                # Include full data if available
                'full_data': emp.get('full_data', {})
            }]

            # Add to Railway database
            added, updated_count = remote_db.add_employees(
                emp_data,
                emp.get('company', 'unknown')
            )

            if added > 0:
                successful += 1
                print(f"   [{i}/{len(local_employees)}] ✓ Migrated: {emp.get('name')}")
            elif updated_count > 0:
                updated += 1
                print(f"   [{i}/{len(local_employees)}] ⟳ Updated: {emp.get('name')}")
            else:
                failed += 1
                print(f"   [{i}/{len(local_employees)}] ⚠️ Skipped: {emp.get('name')} (may already exist)")

        except Exception as e:
            failed += 1
            print(f"   [{i}/{len(local_employees)}] ❌ Failed: {emp.get('name')} - {e}")

    # Step 4: Verify migration
    print("\n4. Verifying migration...")

    final_stats = remote_db.get_statistics()
    print(f"   Total employees in Railway now: {final_stats.get('total_tracked', 0)}")

    # Summary
    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print(f"\n✓ Successfully migrated: {successful} employees")
    print(f"⟳ Updated existing: {updated} employees")

    if failed > 0:
        print(f"⚠️ Failed/Skipped: {failed} employees")

    print(f"\nTotal employees in Railway PostgreSQL: {final_stats.get('total_tracked', 0)}")
    print("\n🎉 Your Railway app should now show all employees!")
    print("\nNext steps:")
    print("1. Check your Railway app to see the migrated employees")
    print("2. If employees still don't show, check their 'status' field")
    print("3. Deploy any local changes to Railway")

if __name__ == "__main__":
    # Check if we have DATABASE_URL
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not found in .env")
        print("\nTo migrate to Railway:")
        print("1. Get the PUBLIC database URL from Railway")
        print("2. Add to .env: DATABASE_URL=postgresql://...")
        print("3. Run this script again")
    else:
        migrate_employees()