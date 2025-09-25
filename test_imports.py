"""
Test script to verify all imports work before Railway deployment
Run this locally to catch import errors early
"""

def test_imports():
    """Test all imports that api_v2.py uses"""

    print("Testing imports...")

    try:
        # Test basic Python imports
        import os
        import sys
        import json
        import asyncio
        from datetime import datetime, timedelta
        from pathlib import Path
        from typing import List, Dict, Optional
        print("[OK] Basic Python imports: OK")
    except ImportError as e:
        print(f"[ERROR] Basic Python imports failed: {e}")
        return False

    try:
        # Test FastAPI imports
        from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Header
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse, HTMLResponse
        from pydantic import BaseModel, Field
        import uvicorn
        print("[OK] FastAPI imports: OK")
    except ImportError as e:
        print(f"[ERROR] FastAPI imports failed: {e}")
        return False

    try:
        # Test project-specific imports
        from scripts.employee_tracker import EmployeeTracker
        print("[OK] Employee tracker import: OK")
    except ImportError as e:
        print(f"[ERROR] Employee tracker import failed: {e}")
        return False

    try:
        from scripts.email_alerts import EmailAlertSender
        print("[OK] Email alerts import: OK")
    except ImportError as e:
        print(f"[ERROR] Email alerts import failed: {e}")
        return False

    try:
        from config.target_companies import TARGET_COMPANIES
        print("[OK] Target companies import: OK")
        print(f"   Found {len(TARGET_COMPANIES)} companies configured")
    except ImportError as e:
        print(f"[ERROR] Target companies import failed: {e}")
        return False

    try:
        # Test database imports
        from scripts.database_factory import TrackingDatabase
        print("[OK] Database factory import: OK")
    except ImportError as e:
        print(f"[ERROR] Database factory import failed: {e}")
        return False

    print("\n[SUCCESS] All imports successful! Ready for Railway deployment.")
    return True

def test_api_creation():
    """Test that the FastAPI app can be created"""
    try:
        from api_v2 import app
        print("[OK] FastAPI app creation: OK")
        print(f"   App title: {app.title}")
        print(f"   App version: {app.version}")
        return True
    except Exception as e:
        print(f"[ERROR] FastAPI app creation failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    from pathlib import Path

    print("="*60)
    print("RAILWAY DEPLOYMENT READINESS TEST")
    print("="*60)

    # Add current directory to path (same as api_v2.py does)
    sys.path.insert(0, str(Path(__file__).parent))

    imports_ok = test_imports()
    app_ok = test_api_creation()

    print("\n" + "="*60)
    if imports_ok and app_ok:
        print("[SUCCESS] READY FOR DEPLOYMENT!")
        print("Run: git add . && git commit -m 'Fix deployment' && git push")
    else:
        print("[ERROR] DEPLOYMENT NOT READY - Fix errors above first")
    print("="*60)