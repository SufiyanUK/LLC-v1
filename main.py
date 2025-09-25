"""
Main entry point for Railway deployment
This file imports and runs the actual API from the root directory
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the FastAPI app from api_v2.py in root directory
from api_v2 import app

# The app is now available for uvicorn to run
# Railway will run: uvicorn main:app --host 0.0.0.0 --port $PORT

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)