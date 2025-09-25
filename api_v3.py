"""
FastAPI v3 - Enhanced API with comprehensive error logging and debugging
Fixes issues with pipeline execution and provides better visibility
"""

import os
import sys
import json
import subprocess
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Alert Pipeline API v3",
    description="Enhanced API with comprehensive error logging and debugging",
    version="3.0.0"
)

# Enable CORS for all origins (for ngrok)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration paths
QUALIFIED_STARTUPS_FILE = 'data/processed/qualified_startups.json'
ALERTS_DIR = 'data/alerts'
CACHE_DIR = 'data/raw/updated_test'
PIPELINE_V2_SCRIPT = 'run_alert_pipeline_v2.py'
FETCH_EMPLOYEES_SCRIPT = 'fetch_company_employees_fixed.py'  # USING FIXED VERSION!

# Global status tracking with enhanced error info
pipeline_status = {
    'is_running': False,
    'progress': 0,
    'message': 'Ready',
    'last_run': None,
    'last_error': None,
    'last_stdout': None,
    'last_stderr': None,
    'current_task': None,
    'files_created': [],
    'execution_time': None
}

fetch_status = {
    'is_fetching': False,
    'company': None,
    'progress': 0,
    'message': 'Ready',
    'last_fetch': None,
    'last_error': None,
    'last_stdout': None,
    'last_stderr': None
}

# Pydantic models
class Company(BaseModel):
    company_name: str
    founded_date: Optional[str] = None
    industry: Optional[str] = "Technology"
    location: Optional[str] = None
    description: Optional[str] = None

class FetchConfig(BaseModel):
    company_name: str = Field(..., description="Company name to fetch employees from")
    max_credits: int = Field(10, ge=1, le=100, description="Maximum API credits to use (1 credit = 1 employee record, NOT 100!)")
    days_back: int = Field(90, ge=1, le=365, description="Days to look back for departures")

class PipelineConfig(BaseModel):
    specific_file: Optional[str] = Field(None, description="Process specific file only")
    
class Alert(BaseModel):
    pdl_id: str
    full_name: str
    alert_level: str
    priority_score: float
    departure_info: Optional[Dict] = None
    building_phrases: Optional[List[str]] = None
    founder_score: Optional[float] = None
    stealth_score: Optional[float] = None

# Helper functions
def load_qualified_startups() -> List[Dict]:
    """Load qualified startups from JSON file"""
    try:
        with open(QUALIFIED_STARTUPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load qualified startups: {e}")
        return []

def save_qualified_startups(companies: List[Dict]):
    """Save qualified startups to JSON file"""
    try:
        os.makedirs(os.path.dirname(QUALIFIED_STARTUPS_FILE), exist_ok=True)
        with open(QUALIFIED_STARTUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(companies, f, indent=2)
        logger.info(f"Saved {len(companies)} companies to {QUALIFIED_STARTUPS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save qualified startups: {e}")
        raise

def get_latest_v2_alerts() -> Dict:
    """Get the latest v2 alerts from the alerts directory"""
    try:
        # Look for v2 alert files
        alerts_files = sorted(Path(ALERTS_DIR).glob('alerts_v2_full_*.json'), reverse=True)
        if alerts_files:
            logger.info(f"Loading alerts from {alerts_files[0]}")
            with open(alerts_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("No alert files found")
    except Exception as e:
        logger.error(f"Failed to load alerts: {e}")
    return {'LEVEL_3': [], 'LEVEL_2': [], 'LEVEL_1': [], 'stats': {}, 'by_company': {}}

def get_cached_files() -> List[Dict]:
    """Get list of cached employee files"""
    files = []
    try:
        if not Path(CACHE_DIR).exists():
            logger.warning(f"Cache directory does not exist: {CACHE_DIR}")
            return files
            
        for filepath in Path(CACHE_DIR).glob('*.jsonl'):
            # Extract company from filename
            filename = filepath.name
            parts = filename.split('_')
            company = parts[0] if parts else 'unknown'
            
            # Get file stats
            stat = filepath.stat()
            files.append({
                'filename': filename,
                'company': company,
                'size_kb': round(stat.st_size / 1024, 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'path': str(filepath)
            })
        logger.info(f"Found {len(files)} cached files")
    except Exception as e:
        logger.error(f"Failed to get cached files: {e}")
    
    return sorted(files, key=lambda x: x['modified'], reverse=True)

def check_new_alert_files(before_timestamp: datetime) -> List[str]:
    """Check for new alert files created after a given timestamp"""
    new_files = []
    try:
        for filepath in Path(ALERTS_DIR).glob('alerts_v2_*.json'):
            if filepath.stat().st_mtime > before_timestamp.timestamp():
                new_files.append(filepath.name)
        if new_files:
            logger.info(f"New alert files created: {new_files}")
    except Exception as e:
        logger.error(f"Failed to check for new alert files: {e}")
    return new_files

async def fetch_company_employees_background(company: str, credits: int, days: int):
    """Fetch employees from a company in background"""
    global fetch_status
    
    start_time = datetime.now()
    fetch_status['is_fetching'] = True
    fetch_status['company'] = company
    fetch_status['progress'] = 10
    fetch_status['message'] = f'Starting fetch for {company}...'
    fetch_status['last_error'] = None
    fetch_status['last_stdout'] = None
    fetch_status['last_stderr'] = None
    
    logger.info(f"Starting employee fetch for {company}")
    logger.info(f"IMPORTANT: Will fetch UP TO {credits} employees (costs {credits} credits)")
    logger.info(f"Looking for departures in last {days} days")
    
    try:
        # Check for virtual environment Python
        venv_python = os.path.join('.venv', 'Scripts', 'python.exe')
        python_exe = venv_python if os.path.exists(venv_python) else 'python'
        
        logger.info(f"Using Python executable: {python_exe}")
        
        fetch_status['progress'] = 30
        fetch_status['message'] = f'Fetching {company} employees...'
        
        # Run the fetch script
        cmd = [python_exe, FETCH_EMPLOYEES_SCRIPT, company, str(credits), str(days)]
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Use subprocess.run for Windows compatibility
        import subprocess as sp
        
        # Run in a thread executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sp.run(
                cmd,
                capture_output=True,
                text=False,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        )
        
        fetch_status['progress'] = 60
        fetch_status['message'] = 'Processing employee data...'
        
        # Get output from subprocess.run result
        stdout_text = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ''
        stderr_text = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
        
        fetch_status['last_stdout'] = stdout_text[-1000:] if stdout_text else None
        fetch_status['last_stderr'] = stderr_text[-1000:] if stderr_text else None
        
        if result.returncode == 0:
            fetch_status['progress'] = 100
            fetch_status['message'] = f'Successfully fetched {company} employees'
            fetch_status['last_fetch'] = datetime.now().isoformat()
            
            logger.info(f"Successfully fetched employees for {company}")
            logger.debug(f"Stdout: {stdout_text[-500:]}")
            
            # Parse output to get filename
            if 'SAVED' in stdout_text and '.jsonl' in stdout_text:
                lines = stdout_text.split('\n')
                for line in lines:
                    if 'SAVED' in line and '.jsonl' in line:
                        fetch_status['message'] = f'Saved {company} employees to cache'
                        logger.info(f"File saved: {line}")
                        break
        else:
            fetch_status['message'] = f'Fetch failed for {company}'
            fetch_status['last_error'] = stderr_text[:500] if stderr_text else 'Unknown error'
            fetch_status['progress'] = 0
            
            logger.error(f"Fetch failed for {company} with return code: {result.returncode}")
            logger.error(f"Stderr: {stderr_text}")
            logger.error(f"Stdout: {stdout_text}")
    
    except Exception as e:
        fetch_status['message'] = 'Fetch error'
        fetch_status['last_error'] = str(e)
        fetch_status['progress'] = 0
        logger.exception(f"Exception during fetch for {company}: {e}")
    
    finally:
        execution_time = (datetime.now() - start_time).total_seconds()
        fetch_status['is_fetching'] = False
        fetch_status['company'] = None
        logger.info(f"Fetch operation completed in {execution_time:.2f} seconds")

async def run_pipeline_v2_background(specific_file: Optional[str] = None):
    """Run the v2 pipeline in background with enhanced error logging"""
    global pipeline_status
    
    start_time = datetime.now()
    before_files_timestamp = datetime.now()
    
    pipeline_status['is_running'] = True
    pipeline_status['progress'] = 10
    pipeline_status['message'] = 'Starting pipeline v2...'
    pipeline_status['last_error'] = None
    pipeline_status['last_stdout'] = None
    pipeline_status['last_stderr'] = None
    pipeline_status['current_task'] = 'initialization'
    pipeline_status['files_created'] = []
    
    logger.info(f"Starting pipeline v2 with specific_file: {specific_file}")
    
    try:
        # Check for virtual environment Python
        venv_python = os.path.join('.venv', 'Scripts', 'python.exe')
        python_exe = venv_python if os.path.exists(venv_python) else 'python'
        
        logger.info(f"Using Python executable: {python_exe}")
        
        # Verify the pipeline script exists
        if not os.path.exists(PIPELINE_V2_SCRIPT):
            raise FileNotFoundError(f"Pipeline script not found: {PIPELINE_V2_SCRIPT}")
        
        pipeline_status['progress'] = 30
        pipeline_status['message'] = 'Running alert analysis...'
        pipeline_status['current_task'] = 'processing'
        
        # Build command
        cmd = [python_exe, PIPELINE_V2_SCRIPT]
        if specific_file:
            cmd.append(specific_file)
            logger.info(f"Processing specific file: {specific_file}")
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Run the pipeline script with proper working directory
        # Use subprocess.run for Windows compatibility
        import subprocess as sp
        
        # Run in a thread executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sp.run(
                cmd,
                capture_output=True,
                text=False,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        )
        
        pipeline_status['progress'] = 60
        pipeline_status['message'] = 'Generating alerts...'
        pipeline_status['current_task'] = 'alert_generation'
        
        # Get output from subprocess.run result
        stdout_text = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ''
        stderr_text = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
        
        # Store output for debugging
        pipeline_status['last_stdout'] = stdout_text[-2000:] if stdout_text else None
        pipeline_status['last_stderr'] = stderr_text[-2000:] if stderr_text else None
        
        logger.info(f"Pipeline completed with return code: {result.returncode}")
        
        if result.returncode == 0:
            pipeline_status['progress'] = 100
            pipeline_status['message'] = 'Pipeline completed successfully'
            pipeline_status['last_run'] = datetime.now().isoformat()
            pipeline_status['current_task'] = 'completed'
            
            # Check for new alert files
            new_files = check_new_alert_files(before_files_timestamp)
            pipeline_status['files_created'] = new_files
            
            # Parse output for saved file paths from the pipeline output
            saved_files = []
            if '[SAVED]' in stdout_text:
                for line in stdout_text.split('\n'):
                    if '[SAVED]' in line:
                        logger.info(f"Files saved: {line}")
                        # Extract file paths from the line
                        if 'alerts_v2_full_' in line:
                            import re
                            # Extract filename from path
                            match = re.search(r'(alerts_v2_\w+_\d{8}_\d{6}\.\w+)', line)
                            if match:
                                saved_files.append(match.group(1))
                        elif 'data/alerts/' in line or 'data\\alerts\\' in line:
                            # Extract the full path
                            parts = line.split(':')
                            if len(parts) > 1:
                                filepath = ':'.join(parts[1:]).strip()
                                if filepath:
                                    saved_files.append(os.path.basename(filepath))
            
            # Also check filesystem for new files if not found in output
            if not saved_files and new_files:
                saved_files = new_files
            
            if saved_files:
                pipeline_status['files_created'] = saved_files
                files_msg = ', '.join(saved_files[:3])  # Show first 3 files
                if len(saved_files) > 3:
                    files_msg += f' and {len(saved_files)-3} more'
                pipeline_status['message'] = f'Completed - Created: {files_msg}'
                logger.info(f"Alert files created: {saved_files}")
            
            # Parse output for statistics
            elif 'Total Alerts:' in stdout_text:
                lines = stdout_text.split('\n')
                for line in lines:
                    if 'Total Alerts:' in line:
                        count = line.split(':')[-1].strip()
                        pipeline_status['message'] = f'Completed - Generated {count} alerts'
                        logger.info(f"Generated {count} alerts")
                        break
            
            logger.info("Pipeline completed successfully")
            logger.debug(f"Output (last 500 chars): {stdout_text[-500:]}")
            
        else:
            pipeline_status['message'] = 'Pipeline failed'
            pipeline_status['last_error'] = stderr_text[:1000] if stderr_text else 'Unknown error'
            pipeline_status['progress'] = 0
            pipeline_status['current_task'] = 'failed'
            
            logger.error(f"Pipeline failed with return code: {result.returncode}")
            logger.error(f"Stderr: {stderr_text}")
            logger.error(f"Stdout: {stdout_text}")
            
            # Try to extract specific error messages
            if 'ModuleNotFoundError' in stderr_text:
                logger.error("Module import error detected - check dependencies")
            elif 'FileNotFoundError' in stderr_text:
                logger.error("File not found error - check file paths")
            elif 'PermissionError' in stderr_text:
                logger.error("Permission error - check file/directory permissions")
    
    except FileNotFoundError as e:
        error_msg = f"Pipeline script not found: {e}"
        pipeline_status['message'] = 'Pipeline script missing'
        pipeline_status['last_error'] = error_msg
        pipeline_status['progress'] = 0
        pipeline_status['current_task'] = 'error'
        logger.error(error_msg)
        
    except Exception as e:
        error_msg = f"Pipeline exception: {str(e)}"
        pipeline_status['message'] = 'Pipeline error'
        pipeline_status['last_error'] = error_msg
        pipeline_status['progress'] = 0
        pipeline_status['current_task'] = 'error'
        logger.exception(f"Unexpected exception in pipeline: {e}")
    
    finally:
        execution_time = (datetime.now() - start_time).total_seconds()
        pipeline_status['execution_time'] = execution_time
        pipeline_status['is_running'] = False
        logger.info(f"Pipeline execution completed in {execution_time:.2f} seconds")

# API Endpoints

@app.get("/")
async def root():
    """API documentation and status"""
    return {
        "name": "Alert Pipeline API v3",
        "version": "3.0.0",
        "status": "online",
        "improvements": [
            "Comprehensive error logging",
            "Better debugging information",
            "Execution time tracking",
            "File creation monitoring",
            "Enhanced error messages"
        ],
        "endpoints": {
            "Core": {
                "GET /": "This documentation",
                "GET /health": "Health check",
                "GET /dashboard": "Dashboard with stats",
                "GET /logs": "View recent logs"
            },
            "Employee Fetching": {
                "POST /fetch-employees": "Fetch employees (⚠️ FIXED: 1 credit = 1 employee)",
                "POST /fetch-employees-test": "SAFE TEST - Fetch 5 employees only (5 credits)",
                "GET /fetch-status": "Check fetch operation status with detailed logs",
                "GET /cached-files": "List all cached employee files",
                "DELETE /cached-files/{filename}": "Delete a cached file"
            },
            "Pipeline": {
                "POST /run-pipeline": "Run v2 pipeline on all files",
                "POST /run-pipeline-file": "Run pipeline on specific file",
                "GET /pipeline-status": "Check pipeline status with detailed logs",
                "GET /pipeline-debug": "Get full debug information"
            },
            "Alerts": {
                "GET /alerts": "Get all alerts",
                "GET /alerts/by-company": "Alerts grouped by company",
                "GET /alerts/high-priority": "Level 2 & 3 alerts only",
                "GET /alerts/export": "Export alerts data"
            },
            "Companies": {
                "GET /companies": "List qualified startups",
                "POST /companies": "Add new company",
                "DELETE /companies/{index}": "Delete company"
            }
        },
        "logging": "Check api_v3.log for detailed logs",
        "ngrok_tip": "Run 'ngrok http 8000' to get public URL"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pipeline_ready": not pipeline_status['is_running'],
        "fetch_ready": not fetch_status['is_fetching'],
        "alerts_dir_exists": os.path.exists(ALERTS_DIR),
        "cache_dir_exists": os.path.exists(CACHE_DIR),
        "log_file_exists": os.path.exists('api_v3.log')
    }

@app.get("/logs")
async def get_recent_logs(lines: int = Query(50, ge=1, le=500)):
    """Get recent log lines"""
    try:
        if os.path.exists('api_v3.log'):
            with open('api_v3.log', 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:]
                return {
                    "logs": recent_lines,
                    "total_lines": len(all_lines),
                    "showing": len(recent_lines)
                }
        else:
            return {"logs": [], "message": "Log file not found"}
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def get_dashboard():
    """Enhanced dashboard with v3 statistics and debugging info"""
    alerts = get_latest_v2_alerts()
    stats = alerts.get('stats', {})
    by_company = alerts.get('by_company', {})
    
    # Get cached files info
    cached_files = get_cached_files()
    
    return {
        "statistics": {
            "total_companies": len(load_qualified_startups()),
            "cached_files": len(cached_files),
            "total_alerts": stats.get('total_alerts', 0),
            "level_3_count": stats.get('level_3_count', 0),
            "level_2_count": stats.get('level_2_count', 0),
            "level_1_count": stats.get('level_1_count', 0),
            "files_processed": stats.get('files_processed', 0),
            "employees_processed": stats.get('employees_processed', 0),
            "companies_analyzed": list(by_company.keys()),
            "timestamp": alerts.get('timestamp')
        },
        "by_company": by_company,
        "pipeline_status": pipeline_status,
        "fetch_status": fetch_status,
        "recent_files": cached_files[:5],
        "system_info": {
            "alerts_dir_exists": os.path.exists(ALERTS_DIR),
            "cache_dir_exists": os.path.exists(CACHE_DIR),
            "pipeline_script_exists": os.path.exists(PIPELINE_V2_SCRIPT),
            "fetch_script_exists": os.path.exists(FETCH_EMPLOYEES_SCRIPT)
        }
    }

@app.post("/fetch-employees")
async def fetch_employees(config: FetchConfig, background_tasks: BackgroundTasks):
    """
    Fetch employees from a specific company
    
    IMPORTANT: Credit Usage
    - 1 credit = 1 employee record (NOT 100 employees!)
    - max_credits=10 means you get UP TO 10 employees
    - Use small values for testing (5-10 credits)
    """
    if fetch_status['is_fetching']:
        raise HTTPException(status_code=400, detail="Another fetch operation is in progress")
    
    logger.info(f"Starting fetch request for {config.company_name}")
    logger.info(f"CREDIT WARNING: Will use up to {config.max_credits} credits for {config.max_credits} employee records")
    
    # Add warning to response if high credit usage
    warning = None
    if config.max_credits > 20:
        warning = f"⚠️ HIGH CREDIT USAGE: This will use up to {config.max_credits} PDL credits!"
    
    # Start fetch in background
    background_tasks.add_task(
        fetch_company_employees_background,
        config.company_name,
        config.max_credits,
        config.days_back
    )
    
    response = {
        "success": True,
        "message": f"Started fetching {config.company_name} employees",
        "max_employees_to_fetch": config.max_credits,
        "estimated_credit_cost": config.max_credits,
        "config": config.dict(),
        "check_status_at": "/fetch-status"
    }
    
    if warning:
        response["warning"] = warning
    
    return response

@app.post("/fetch-employees-test")
async def fetch_employees_test(company_name: str = "openai", background_tasks: BackgroundTasks = None):
    """
    SAFE TEST endpoint - Fetches only 5 employees (uses only 5 credits)
    
    This is a safe way to test the fetch functionality without using many credits.
    """
    if fetch_status['is_fetching']:
        raise HTTPException(status_code=400, detail="Another fetch operation is in progress")
    
    logger.info(f"SAFE TEST MODE: Fetching 5 employees from {company_name}")
    
    # Fixed safe parameters
    SAFE_CREDITS = 5
    SAFE_DAYS = 30
    
    # Start fetch in background
    background_tasks.add_task(
        fetch_company_employees_background,
        company_name,
        SAFE_CREDITS,
        SAFE_DAYS
    )
    
    return {
        "success": True,
        "message": f"SAFE TEST: Fetching 5 {company_name} employees",
        "test_mode": True,
        "max_employees": SAFE_CREDITS,
        "max_credit_cost": SAFE_CREDITS,
        "days_back": SAFE_DAYS,
        "note": "This test mode uses only 5 credits for safety",
        "check_status_at": "/fetch-status"
    }

@app.get("/fetch-status")
async def get_fetch_status():
    """Get current fetch operation status with detailed logs"""
    return fetch_status

@app.get("/cached-files")
async def get_cached_files_list():
    """List all cached employee files"""
    files = get_cached_files()
    return {
        "files": files,
        "total": len(files),
        "total_size_mb": round(sum(f['size_kb'] for f in files) / 1024, 2) if files else 0,
        "cache_directory": CACHE_DIR
    }

@app.delete("/cached-files/{filename}")
async def delete_cached_file(filename: str):
    """Delete a specific cached file"""
    filepath = Path(CACHE_DIR) / filename
    if not filepath.exists():
        logger.warning(f"File not found for deletion: {filename}")
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        filepath.unlink()
        logger.info(f"Deleted cached file: {filename}")
        return {
            "success": True,
            "message": f"Deleted {filename}"
        }
    except Exception as e:
        logger.error(f"Failed to delete file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-pipeline")
async def run_pipeline(background_tasks: BackgroundTasks):
    """Run the v2 pipeline on all cached files"""
    if pipeline_status['is_running']:
        raise HTTPException(status_code=400, detail="Pipeline is already running")
    
    logger.info("Starting pipeline on all files")
    
    # Start pipeline in background
    background_tasks.add_task(run_pipeline_v2_background, None)
    
    return {
        "success": True,
        "message": "Started pipeline v2 on all files",
        "check_status_at": "/pipeline-status"
    }

@app.post("/run-pipeline-file")
async def run_pipeline_on_file(filename: str, background_tasks: BackgroundTasks):
    """Run the pipeline on a specific file"""
    if pipeline_status['is_running']:
        raise HTTPException(status_code=400, detail="Pipeline is already running")
    
    # Check if file exists
    filepath = Path(CACHE_DIR) / filename
    if not filepath.exists():
        logger.warning(f"File not found for pipeline: {filename}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    logger.info(f"Starting pipeline on file: {filename}")
    
    # Clear previous results
    pipeline_status['files_created'] = []
    pipeline_status['last_stdout'] = None
    pipeline_status['last_stderr'] = None
    
    # Start pipeline in background
    background_tasks.add_task(run_pipeline_v2_background, filename)
    
    return {
        "success": True,
        "message": f"Started pipeline on {filename}",
        "input_file": filename,
        "check_status_at": "/pipeline-status",
        "note": "Check /pipeline-status to see which alert files are created"
    }

@app.get("/pipeline-status")
async def get_pipeline_status():
    """Get current pipeline status with detailed logs"""
    status = pipeline_status.copy()
    
    # Add helpful interpretation
    if status.get('files_created'):
        status['alert_files'] = {
            'count': len(status['files_created']),
            'files': status['files_created'],
            'location': ALERTS_DIR
        }
    
    # Add summary based on current state
    if status['is_running']:
        status['summary'] = f"Pipeline is currently {status.get('current_task', 'running')}..."
    elif status.get('last_error'):
        status['summary'] = "Pipeline failed - check 'last_error' for details"
    elif status.get('files_created'):
        status['summary'] = f"Pipeline completed successfully - Created {len(status['files_created'])} alert files"
    elif status.get('last_run'):
        status['summary'] = "Pipeline completed but no new files were created"
    else:
        status['summary'] = "Pipeline has not been run yet"
    
    return status

@app.get("/pipeline-debug")
async def get_pipeline_debug():
    """Get full debug information for pipeline"""
    return {
        "status": pipeline_status,
        "environment": {
            "python_path": sys.executable,
            "working_directory": os.getcwd(),
            "alerts_dir": ALERTS_DIR,
            "cache_dir": CACHE_DIR,
            "pipeline_script": PIPELINE_V2_SCRIPT
        },
        "recent_alerts": get_latest_v2_alerts().get('stats', {}),
        "cached_files": len(get_cached_files())
    }

@app.get("/alerts/latest-files")
async def get_latest_alert_files():
    """Get list of most recent alert files created"""
    try:
        alert_files = []
        if os.path.exists(ALERTS_DIR):
            for filepath in Path(ALERTS_DIR).glob('alerts_v2_*.json'):
                stat = filepath.stat()
                alert_files.append({
                    'filename': filepath.name,
                    'path': str(filepath),
                    'size_kb': round(stat.st_size / 1024, 2),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'type': 'full' if 'full' in filepath.name else 'high_priority' if 'high_priority' in filepath.name else 'summary'
                })
        
        # Sort by creation time, newest first
        alert_files.sort(key=lambda x: x['created'], reverse=True)
        
        return {
            'total_files': len(alert_files),
            'latest_files': alert_files[:10],  # Show last 10 files
            'alerts_directory': ALERTS_DIR
        }
    except Exception as e:
        logger.error(f"Failed to get alert files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts(
    level: Optional[str] = Query(None, description="Filter by level: LEVEL_1, LEVEL_2, LEVEL_3"),
    company: Optional[str] = Query(None, description="Filter by company"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get alerts with optional filters"""
    alerts = get_latest_v2_alerts()
    
    # Flatten alerts
    all_alerts = []
    for alert_level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
        if level and alert_level != level:
            continue
        
        for alert in alerts.get(alert_level, []):
            if alert:
                alert['level'] = alert_level
                all_alerts.append(alert)
    
    # Filter by company if specified
    if company and 'by_company' in alerts:
        company_alerts = []
        company_data = alerts.get('by_company', {}).get(company.lower(), {})
        for alert_level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
            for alert in company_data.get(alert_level, []):
                if alert:
                    alert['level'] = alert_level
                    company_alerts.append(alert)
        all_alerts = company_alerts
    
    # Apply limit
    all_alerts = all_alerts[:limit]
    
    logger.info(f"Retrieved {len(all_alerts)} alerts with filters: level={level}, company={company}")
    
    return {
        "alerts": all_alerts,
        "total": len(all_alerts),
        "filters": {
            "level": level,
            "company": company,
            "limit": limit
        },
        "stats": alerts.get('stats', {})
    }

@app.get("/alerts/by-company")
async def get_alerts_by_company():
    """Get alerts grouped by company"""
    alerts = get_latest_v2_alerts()
    by_company = alerts.get('by_company', {})
    
    # Calculate stats per company
    company_stats = {}
    for company, levels in by_company.items():
        company_stats[company] = {
            'total': sum(len(levels.get(l, [])) for l in ['LEVEL_1', 'LEVEL_2', 'LEVEL_3']),
            'level_3': len(levels.get('LEVEL_3', [])),
            'level_2': len(levels.get('LEVEL_2', [])),
            'level_1': len(levels.get('LEVEL_1', [])),
            'alerts': levels
        }
    
    return {
        "by_company": company_stats,
        "companies": list(company_stats.keys()),
        "total_companies": len(company_stats)
    }

@app.get("/alerts/high-priority")
async def get_high_priority_alerts():
    """Get only Level 2 and Level 3 alerts"""
    alerts = get_latest_v2_alerts()
    
    high_priority = []
    
    # Add all Level 3 alerts
    for alert in alerts.get('LEVEL_3', []):
        if alert:
            alert['level'] = 'LEVEL_3'
            alert['urgency'] = 'IMMEDIATE'
            high_priority.append(alert)
    
    # Add all Level 2 alerts
    for alert in alerts.get('LEVEL_2', []):
        if alert:
            alert['level'] = 'LEVEL_2'
            alert['urgency'] = 'HIGH'
            high_priority.append(alert)
    
    # Sort by priority score
    high_priority.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    
    logger.info(f"Retrieved {len(high_priority)} high-priority alerts")
    
    return {
        "alerts": high_priority,
        "total": len(high_priority),
        "level_3_count": len(alerts.get('LEVEL_3', [])),
        "level_2_count": len(alerts.get('LEVEL_2', [])),
        "top_building_signals": list(set(
            signal 
            for alert in high_priority[:20]
            for signal in alert.get('building_phrases', [])
        ))
    }

@app.get("/alerts/export")
async def export_alerts():
    """Export alerts data in CSV format"""
    alerts = get_latest_v2_alerts()
    
    csv_rows = []
    headers = ["Level", "Name", "Company", "Priority Score", "Founder Score", 
               "Stealth Score", "Building Signals", "Days Since Departure"]
    csv_rows.append(headers)
    
    for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
        for alert in alerts.get(level, []):
            if alert:
                departure = alert.get('departure_info', {})
                csv_rows.append([
                    level,
                    alert.get('full_name', ''),
                    departure.get('company', '') if departure else '',
                    alert.get('priority_score', 0),
                    alert.get('founder_score', 0),
                    alert.get('stealth_score', 0),
                    '|'.join(alert.get('building_phrases', [])),
                    departure.get('days_ago', '') if departure else ''
                ])
    
    logger.info(f"Exported {len(csv_rows) - 1} alerts to CSV format")
    
    return {
        "csv_data": csv_rows,
        "filename": f"alerts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "total_rows": len(csv_rows) - 1
    }

@app.get("/companies")
async def get_companies():
    """Get all qualified startups"""
    companies = load_qualified_startups()
    return {
        "companies": companies,
        "total": len(companies)
    }

@app.post("/companies")
async def add_company(company: Company):
    """Add a new qualified startup"""
    companies = load_qualified_startups()
    
    # Check for duplicates
    for existing in companies:
        if existing.get('company_name', '').lower() == company.company_name.lower():
            logger.warning(f"Attempted to add duplicate company: {company.company_name}")
            raise HTTPException(status_code=400, detail="Company already exists")
    
    # Add new company
    new_company = company.dict()
    new_company['added_date'] = datetime.now().isoformat()
    companies.append(new_company)
    
    save_qualified_startups(companies)
    logger.info(f"Added new company: {company.company_name}")
    
    return {
        "success": True,
        "message": f"Added {company.company_name}",
        "company": new_company,
        "total_companies": len(companies)
    }

@app.delete("/companies/{index}")
async def delete_company(index: int):
    """Delete a company by index"""
    companies = load_qualified_startups()
    
    if index < 0 or index >= len(companies):
        logger.warning(f"Invalid company index for deletion: {index}")
        raise HTTPException(status_code=404, detail="Company not found")
    
    deleted = companies.pop(index)
    save_qualified_startups(companies)
    logger.info(f"Deleted company: {deleted.get('company_name', 'Unknown')}")
    
    return {
        "success": True,
        "message": f"Deleted {deleted.get('company_name', 'Unknown')}",
        "deleted": deleted,
        "remaining_companies": len(companies)
    }

# Error handlers
@app.exception_handler(404)
async def not_found(request, exc):
    logger.warning(f"404 error: {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error(request, exc):
    logger.error(f"500 error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ALERT PIPELINE API v3 - ENHANCED WITH LOGGING")
    print("="*60)
    print("\nStarting FastAPI server with enhanced logging...")
    print("API will be available at: http://localhost:8000")
    print("Log file: api_v3.log")
    print("\nKey Improvements:")
    print("✓ Comprehensive error logging")
    print("✓ Pipeline execution tracking")
    print("✓ File creation monitoring")
    print("✓ Debug endpoints for troubleshooting")
    print("✓ Real-time log viewing")
    print("\nEndpoints:")
    print("- GET /logs - View recent log entries")
    print("- GET /pipeline-debug - Full pipeline debug info")
    print("- GET /pipeline-status - Detailed pipeline status")
    print("\nTo expose via ngrok:")
    print("1. Open new terminal")
    print("2. Run: ngrok http 8000")
    print("3. Use the https URL provided by ngrok")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    logger.info("Starting API v3 server")
    
    # Run the FastAPI app
    uvicorn.run("api_v3:app", host="0.0.0.0", port=8000, reload=True)