"""
Database factory that automatically selects SQLite or PostgreSQL
based on environment. This ensures local development uses SQLite
and Railway deployment uses PostgreSQL without code changes.

IMPORTANT: This does NOT affect local functionality at all!
Local will always use SQLite (database.py)
Railway will use PostgreSQL (database_postgres.py)
"""

import os
import sys

# Check if we're on Railway (has DATABASE_URL)
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Railway environment - use PostgreSQL
    # This ONLY happens when deployed to Railway
    print(f"[DATABASE] Using PostgreSQL (Railway deployment)", file=sys.stderr)
    print(f"[DATABASE] DATABASE_URL found: {database_url[:30]}...", file=sys.stderr)
    try:
        from .database_postgres import TrackingDatabase
        print(f"[DATABASE] PostgreSQL module loaded successfully", file=sys.stderr)
    except Exception as e:
        print(f"[DATABASE] ERROR loading PostgreSQL: {e}", file=sys.stderr)
        print(f"[DATABASE] Falling back to SQLite", file=sys.stderr)
        from .database import TrackingDatabase
else:
    # Local environment - use SQLite
    # This is what YOUR LOCAL SYSTEM will ALWAYS use
    print(f"[DATABASE] Using SQLite (local environment)", file=sys.stderr)
    from .database import TrackingDatabase

# Export the appropriate database class
__all__ = ['TrackingDatabase']