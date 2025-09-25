#!/usr/bin/env python3
"""Run migration with Railway PostgreSQL URL"""
import os
import sys

# Set the DATABASE_URL
os.environ['DATABASE_URL'] = "postgresql://postgres:nIQohizFkyhIJrZZFNTnbSSrIITShtmz@shuttle.proxy.rlwy.net:47970/railway"

# Import and run the migration
from migrate_to_postgresql import main

if __name__ == "__main__":
    # Override input to automatically say yes
    import builtins
    old_input = builtins.input

    def auto_yes_input(prompt):
        print(prompt, end='')
        print('yes')
        return 'yes'

    builtins.input = auto_yes_input

    try:
        main()
    except Exception as e:
        print(f"Migration error: {e}")
        import traceback
        traceback.print_exc()