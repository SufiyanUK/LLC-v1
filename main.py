"""
Main entry point for Railway deployment
This file imports and runs the actual API from employee_tracker directory
"""

import sys
import os
from pathlib import Path

# Add employee_tracker to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'employee_tracker'))

# Import the FastAPI app from employee_tracker
from employee_tracker.api_v2 import app

# The app is now available for uvicorn to run
# Railway will run: uvicorn main:app --host 0.0.0.0 --port $PORT

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)