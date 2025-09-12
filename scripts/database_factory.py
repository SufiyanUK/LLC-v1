"""
Database factory that automatically selects SQLite or PostgreSQL
based on environment. This ensures local development uses SQLite
and Railway deployment uses PostgreSQL without code changes.
"""

import os

# Check if we're on Railway (has DATABASE_URL)
if os.getenv('DATABASE_URL'):
    # Railway environment - use PostgreSQL
    from .database_postgres import TrackingDatabase
else:
    # Local environment - use SQLite
    from .database import TrackingDatabase

# Export the appropriate database class
__all__ = ['TrackingDatabase']