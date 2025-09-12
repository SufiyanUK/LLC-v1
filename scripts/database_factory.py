"""
Database factory that automatically selects SQLite or PostgreSQL
based on environment. This ensures local development uses SQLite
and Railway deployment uses PostgreSQL without code changes.

IMPORTANT: This does NOT affect local functionality at all!
Local will always use SQLite (database.py)
Railway will use PostgreSQL (database_postgres.py)
"""

import os

# Check if we're on Railway (has DATABASE_URL)
if os.getenv('DATABASE_URL'):
    # Railway environment - use PostgreSQL
    # This ONLY happens when deployed to Railway
    from .database_postgres import TrackingDatabase
else:
    # Local environment - use SQLite
    # This is what YOUR LOCAL SYSTEM will ALWAYS use
    from .database import TrackingDatabase

# Export the appropriate database class
__all__ = ['TrackingDatabase']