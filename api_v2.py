"""
Employee Tracker API v2
Supports per-company employee tracking with monthly checks
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
import uvicorn
from datetime import timedelta

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.employee_tracker import EmployeeTracker
from scripts.email_alerts import EmailAlertSender
from config.target_companies import TARGET_COMPANIES

app = FastAPI(
    title="Employee Tracker API v2",
    description="Track specific employees and monitor for departures",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
tracker_state = {
    'is_checking': False,
    'last_check': None,
    'check_progress': 0,
    'check_message': 'Ready'
}

# Pydantic models
class TrackingConfig(BaseModel):
    company_configs: Dict[str, int] = Field(..., description="Dict of company: employee_count")
    
class CompanyTracking(BaseModel):
    company: str = Field(..., description="Company name")
    employee_count: int = Field(5, ge=1, le=100, description="Number of employees to track")

class MonthlyCheckConfig(BaseModel):
    send_alerts: bool = Field(True, description="Send email alerts for departures")
    alert_email: Optional[str] = Field(None, description="Email for alerts")

class CustomCompanyTracking(BaseModel):
    company_name: str = Field(..., description="Name of the new company to track")
    employee_count: int = Field(5, ge=1, le=100, description="Number of employees to track")

class IndividualEmployeeSearch(BaseModel):
    name: Optional[str] = Field(None, description="Employee name to search")
    title: Optional[str] = Field(None, description="Job title keywords")
    company: Optional[str] = Field(None, description="Current or past company")
    location: Optional[str] = Field(None, description="Location (city, state, or country)")
    skills: Optional[List[str]] = Field(None, description="List of skills to search for")
    seniority_level: Optional[str] = Field(None, description="Seniority level (senior, staff, principal, director, vp)")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results to return")

class TrackIndividualEmployee(BaseModel):
    pdl_id: str = Field(..., description="PDL ID of the employee to track")
    name: str = Field(..., description="Employee name")
    title: str = Field(..., description="Employee title")
    company: str = Field(..., description="Employee company")

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web interface"""
    # Try v3 first
    html_file = Path(__file__).parent / 'index_v3.html'
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to v2
    html_file = Path(__file__).parent / 'index_v2.html'
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to original
    html_file = Path(__file__).parent / 'index.html'
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="<h1>Web interface not found</h1>")

@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity test"""
    import os
    
    health_status = {
        "status": "healthy",
        "environment": "railway" if os.getenv('DATABASE_URL') else "local",
        "database": {
            "type": "unknown",
            "connected": False,
            "error": None
        }
    }
    
    try:
        # Try to initialize database connection
        from scripts.database_factory import TrackingDatabase
        db = TrackingDatabase()
        
        # Check database type
        if os.getenv('DATABASE_URL'):
            health_status["database"]["type"] = "postgresql"
            # Try to get stats to verify connection
            stats = db.get_statistics()
            health_status["database"]["connected"] = True
            health_status["database"]["stats"] = stats
        else:
            health_status["database"]["type"] = "sqlite"
            stats = db.get_statistics()
            health_status["database"]["connected"] = True
            health_status["database"]["stats"] = stats
            
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"]["error"] = str(e)
    
    return health_status

@app.get("/api")
async def api_docs():
    """API documentation"""
    return {
        "name": "Employee Tracker v2",
        "endpoints": {
            "System": {
                "GET /health": "Health check with database connectivity test"
            },
            "Tracking": {
                "POST /track/initialize": "Initialize tracking with company configs",
                "POST /track/add-company": "Add or update company tracking",
                "GET /track/status": "Get current tracking status",
                "GET /track/employees": "List all tracked employees"
            },
            "Monitoring": {
                "POST /check/monthly": "Run departure check (uses credits)",
                "POST /check/test": "Test departure check (no credits used)",
                "GET /check/status": "Get check operation status",
                "GET /check/history": "Get departure history"
            },
            "Configuration": {
                "GET /companies": "List available companies with default counts",
                "GET /company-suggestions": "Get suggested employee counts",
                "POST /company/{company_name}/set-default": "Set default employee count for a company",
                "GET /company/{company_name}/default": "Get default employee count for a company"
            },
            "Employee Management": {
                "DELETE /track/employee/{pdl_id}": "Soft delete an employee",
                "POST /track/employee/{pdl_id}/restore": "Restore a deleted employee",
                "GET /track/deleted": "Get all deleted employees",
                "POST /track/custom-company": "Add employees from a new company not in the list",
                "DELETE /track/company/{company_name}": "Delete company and all its employees"
            }
        }
    }

@app.post("/track/initialize")
async def initialize_tracking(config: TrackingConfig):
    """
    Initialize tracking for multiple companies
    
    Example body:
    {
        "company_configs": {
            "openai": 5,
            "anthropic": 10,
            "meta": 20
        }
    }
    """
    tracker = EmployeeTracker()
    
    total_credits = sum(config.company_configs.values())
    
    print(f"\n[INITIALIZE] Starting tracking for {len(config.company_configs)} companies")
    print(f"Total credits to use: {total_credits}")
    
    # Check for existing employees first
    warnings = []
    for company, count in config.company_configs.items():
        existing = len(tracker.get_existing_employee_ids(company))
        if existing > 0:
            warnings.append(f"{company}: Already tracking {existing} employees")
    
    if warnings:
        print(f"  ⚠️ Warning: {'; '.join(warnings)}")
    
    # Initialize tracking
    tracking_data = tracker.initialize_tracking(config.company_configs)
    
    return {
        "success": True,
        "message": f"Initialized tracking for {len(config.company_configs)} companies",
        "total_employees_tracked": tracking_data['total_tracked'],
        "credits_used": total_credits,
        "companies": tracking_data['companies']
    }

@app.post("/track/add-company")
async def add_company_tracking(config: CompanyTracking):
    """Add or update tracking for a specific company"""
    
    tracker = EmployeeTracker()
    
    print(f"\n[ADD] Adding {config.employee_count} employees from {config.company}")
    
    # Check existing first
    existing = len(tracker.get_existing_employee_ids(config.company))
    if existing > 0:
        print(f"  ⚠️ Already tracking {existing} employees from {config.company}")
    
    result = tracker.add_company_to_tracking(config.company, config.employee_count)

    if result and result.get('success'):
        status = tracker.get_tracking_status()
        return {
            "success": True,
            "message": f"Added {result.get('added', 0)} employees from {config.company} to tracking",
            "total_tracked": status['total_tracked'],
            "credits_used": config.employee_count
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to add company to tracking")

@app.get("/track/company/{company}/status")
async def get_company_tracking_status(company: str):
    """Get tracking status for a specific company"""
    
    tracker = EmployeeTracker()
    existing_ids = tracker.get_existing_employee_ids(company)
    
    employees = tracker.db.get_all_employees()
    company_employees = [e for e in employees if e['company'].lower() == company.lower() and e['status'] != 'deleted']
    
    return {
        "company": company,
        "currently_tracking": len(company_employees),
        "active": sum(1 for e in company_employees if e['status'] == 'active'),
        "departed": sum(1 for e in company_employees if e['status'] == 'departed'),
        "employee_ids": list(existing_ids)
    }

@app.get("/track/status")
async def get_tracking_status():
    """Get current tracking status and statistics"""
    
    tracker = EmployeeTracker()
    status = tracker.get_tracking_status()
    
    # Load existing tracking data if available
    tracking_data = tracker.load_tracking_data()
    if tracking_data:
        status['existing_data'] = True
        status['companies_configured'] = {}
        for company, data in tracking_data.get('companies', {}).items():
            status['companies_configured'][company] = data.get('count', 0)
    else:
        status['existing_data'] = False
        status['companies_configured'] = {}
    
    return status

@app.get("/track/employees")
async def get_tracked_employees():
    """Get list of all tracked employees"""
    
    tracker = EmployeeTracker()
    employees = tracker.db.get_all_employees()
    
    # Filter out deleted employees from main list
    active_employees = [e for e in employees if e['status'] != 'deleted']
    
    return {
        "employees": active_employees,
        "total": len(active_employees),
        "active": sum(1 for e in active_employees if e['status'] == 'active'),
        "departed": sum(1 for e in active_employees if e['status'] == 'departed')
    }

@app.get("/track/history")
async def get_fetch_history():
    """Get history of all employee fetches"""
    
    tracker = EmployeeTracker()
    history = tracker.db.get_fetch_history(limit=50)
    
    return {
        "history": history,
        "total": len(history)
    }

@app.post("/check/monthly")
async def run_departure_check(
    config: MonthlyCheckConfig, 
    background_tasks: BackgroundTasks,
    x_cron_token: str = Header(None)
):
    """Run departure check for all tracked employees (uses 1 credit per employee)"""
    
    # Security check for cron job
    expected_token = os.getenv("CRON_SECRET_TOKEN")
    if expected_token and x_cron_token:
        # If a token is provided in the header, validate it
        if x_cron_token != expected_token:
            raise HTTPException(403, "Invalid cron token")
    # Allow manual triggers from UI without token
    
    if tracker_state['is_checking']:
        raise HTTPException(status_code=400, detail="Check already in progress")
    
    # Run check in background
    background_tasks.add_task(
        monthly_check_background,
        config.send_alerts,
        config.alert_email
    )
    
    return {
        "success": True,
        "message": "Departure check started",
        "send_alerts": config.send_alerts,
        "alert_email": config.alert_email,
        "triggered_by": "cron" if x_cron_token else "manual"
    }

@app.post("/check/test")
async def test_departure_check():
    """Test departure check without using credits"""
    
    tracker = EmployeeTracker()
    
    # Get all active employees
    employees = tracker.db.get_all_employees('active')
    
    # Simulate a departure for testing
    simulated_departure = None
    if employees:
        # Pick first employee and simulate they left
        test_emp = employees[0]
        simulated_departure = {
            'name': test_emp['name'],
            'old_company': test_emp['company'],
            'new_company': 'Test Company Inc',
            'old_title': test_emp['title'],
            'new_title': 'Senior Test Engineer'
        }
    
    return {
        "success": True,
        "message": f"Test check would process {len(employees)} employees",
        "would_check": len(employees),
        "credits_would_use": len(employees),
        "simulated_departure": simulated_departure,
        "note": "This is a test - no credits were used and no data was changed"
    }

@app.get("/check/status")
async def get_check_status():
    """Get status of current check operation"""
    
    return tracker_state

@app.get("/check/history")
async def get_departure_history():
    """Get history of all detected departures with alert levels"""
    
    tracker = EmployeeTracker()
    departures = tracker.db.get_departures(limit=100)
    
    # Group by alert level
    by_level = {1: [], 2: [], 3: []}
    for dep in departures:
        level = dep.get('alert_level', 1)
        if level in by_level:
            by_level[level].append(dep)
    
    return {
        "departures": departures,
        "total": len(departures),
        "by_level": {
            "level_3": by_level[3],
            "level_2": by_level[2],
            "level_1": by_level[1]
        },
        "counts": {
            "level_3": len(by_level[3]),
            "level_2": len(by_level[2]),
            "level_1": len(by_level[1])
        }
    }

@app.get("/api/credits")
async def get_credits():
    """Get remaining PDL API credits - FREE method using HEAD request"""
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv('API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        # Use HEAD request to get credit info WITHOUT consuming credits
        # This returns 400 status but includes all credit headers for free!
        url = "https://api.peopledatalabs.com/v5/person/search"
        headers = {
            'X-Api-Key': api_key
        }

        # HEAD request - returns 400 but includes credit headers with 0 cost
        response = requests.head(url, headers=headers)

        # Even though status is 400, we still get credit headers
        # Check if we have the credit headers we need
        if 'X-TotalLimit-Remaining' in response.headers:
            # Extract credit information from headers
            credits_info = {
                'remaining': int(response.headers.get('X-TotalLimit-Remaining', 0)),
                'purchased_remaining': int(response.headers.get('X-TotalLimit-Purchased-Remaining', 0)),
                'overages_remaining': int(response.headers.get('X-TotalLimit-Overages-Remaining', 0)),
                'lifetime_used': int(response.headers.get('X-Lifetime-Used', 0)),
                'last_call_spent': int(response.headers.get('X-Call-Credits-Spent', 0))  # Should be 0
            }
            return JSONResponse(content=credits_info)
        else:
            # Fallback error if headers are missing
            raise HTTPException(status_code=500, detail="Credit information not available in response")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies")
async def get_companies():
    """Get list of available companies including custom ones"""

    # Get custom companies from database (companies not in TARGET_COMPANIES)
    tracker = EmployeeTracker()
    db_companies = tracker.db.get_all_companies()  # This should return company names from company_config

    # Get employee counts for all companies
    employee_counts = tracker.db.get_company_employee_counts()

    # Get default counts for all companies
    default_counts = tracker.db.get_all_company_defaults()

    # Find custom companies (companies in database but not in TARGET_COMPANIES)
    target_companies_lower = [c.lower() for c in TARGET_COMPANIES]
    custom_companies = []

    for company_info in db_companies:
        company_name = company_info.get('company', '')
        if company_name.lower() not in target_companies_lower:
            custom_companies.append(company_name)

    # Combine predefined and custom companies
    all_companies = TARGET_COMPANIES + custom_companies

    return {
        "companies": all_companies,
        "total": len(all_companies),
        "predefined": TARGET_COMPANIES,
        "custom": custom_companies,
        "employee_counts": employee_counts,
        "default_counts": default_counts,
        "categories": {
            "ai_leaders": ["openai", "anthropic", "deepmind", "cohere", "mistral"],
            "tech_giants": ["meta", "google", "microsoft"],
            "platforms": ["uber", "airbnb", "linkedin"],
            "enterprise": ["palantir", "scale ai"],
            "custom": custom_companies
        }
    }

@app.delete("/track/employee/{pdl_id}")
async def delete_employee(pdl_id: str, auto_refetch: bool = True):
    """Soft delete an employee from tracking with auto-refetch based on default count"""

    tracker = EmployeeTracker()

    # Get employee info before deletion
    all_employees = tracker.db.get_all_employees()
    employee_to_delete = None
    for emp in all_employees:
        if emp['pdl_id'] == pdl_id:
            employee_to_delete = emp
            break

    if not employee_to_delete:
        raise HTTPException(status_code=404, detail="Employee not found")

    company = employee_to_delete['company']

    # Count active employees for this company
    active_count = sum(1 for e in all_employees
                      if e['company'] == company and e['status'] == 'active')

    # Get default count for this company
    default_count = tracker.db.get_company_default_count(company)

    # Perform the soft delete
    success = tracker.db.soft_delete_employee(pdl_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete employee")

    refetch_result = None
    new_active_count = active_count - 1

    # Auto-refetch logic: if default is set and we're now below it
    if auto_refetch and default_count is not None and new_active_count < default_count:
        employees_to_fetch = default_count - new_active_count
        print(f"\n[AUTO-REFETCH] Company {company} is below default ({new_active_count}/{default_count}), fetching {employees_to_fetch} replacement(s)...")

        try:
            # Fetch employees to reach the default count
            new_employees = tracker.fetch_senior_employees(company, count=employees_to_fetch, exclude_existing=True)

            if new_employees:
                # Add to database
                added, updated = tracker.db.add_employees(new_employees, company)

                if added > 0:
                    refetch_result = {
                        "success": True,
                        "message": f"Auto-fetched {added} replacement employee(s) to maintain default of {default_count}",
                        "employees_added": added,
                        "new_employees": [
                            {
                                "name": emp.get('name') or emp.get('full_name'),
                                "title": emp.get('title') or emp.get('job_title'),
                                "pdl_id": emp.get('pdl_id') or emp.get('id')
                            } for emp in new_employees[:added]
                        ]
                    }
                    print(f"  [SUCCESS] Added {added} replacement employee(s)")
                else:
                    refetch_result = {
                        "success": False,
                        "message": "No new employees found to replace"
                    }
            else:
                refetch_result = {
                    "success": False,
                    "message": "Could not fetch replacement employee(s)"
                }

        except Exception as e:
            print(f"  [ERROR] Auto-refetch failed: {e}")
            refetch_result = {
                "success": False,
                "message": f"Auto-refetch failed: {str(e)}"
            }

    return {
        "success": True,
        "message": f"Employee {pdl_id} has been removed from tracking",
        "pdl_id": pdl_id,
        "company": company,
        "remaining_count": new_active_count,
        "default_count": default_count,
        "auto_refetch": refetch_result
    }

@app.post("/track/employee/{pdl_id}/restore")
async def restore_employee(pdl_id: str):
    """Restore a soft-deleted employee back to tracking"""
    
    tracker = EmployeeTracker()
    success = tracker.db.restore_employee(pdl_id)
    
    if success:
        return {
            "success": True,
            "message": f"Employee {pdl_id} has been restored to tracking",
            "pdl_id": pdl_id
        }
    else:
        raise HTTPException(status_code=404, detail="Employee not found or not deleted")

@app.delete("/track/company/{company_name}")
async def delete_company(company_name: str):
    """Delete a company and all its tracked employees"""

    tracker = EmployeeTracker()

    try:
        # Get employee count first for response message
        existing_employees = tracker.get_existing_employee_ids(company_name)
        employee_count = len(existing_employees)

        if employee_count == 0:
            # Check if company exists in config
            db_companies = tracker.db.get_all_companies()
            company_exists = any(c['company'].lower() == company_name.lower() for c in db_companies)

            if not company_exists:
                raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")

        # Delete company and all its employees
        success = tracker.db.delete_company(company_name)

        if success:
            return {
                "success": True,
                "message": f"Successfully deleted company '{company_name}' and {employee_count} employees",
                "company": company_name,
                "employees_deleted": employee_count
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete company")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")

@app.get("/track/deleted")
async def get_deleted_employees():
    """Get all soft-deleted employees for backup/restore"""
    
    tracker = EmployeeTracker()
    deleted = tracker.db.get_deleted_employees()
    
    return {
        "deleted_employees": deleted,
        "total": len(deleted)
    }

@app.post("/track/custom-company")
async def track_custom_company(config: CustomCompanyTracking):
    """Add employees from a custom company not in the predefined list"""
    
    tracker = EmployeeTracker()
    
    print(f"\n[CUSTOM] Adding {config.employee_count} employees from {config.company_name}")
    
    # Check existing first
    existing = len(tracker.get_existing_employee_ids(config.company_name))
    if existing > 0:
        print(f"  ⚠️ Already tracking {existing} employees from {config.company_name}")
    
    # Use the same fetch method but with custom company name
    employees = tracker.fetch_senior_employees(config.company_name, config.employee_count)
    
    if employees:
        added, updated = tracker.db.add_employees(employees, config.company_name)
        
        stats = tracker.db.get_statistics()
        
        return {
            "success": True,
            "message": f"Added {added} employees from {config.company_name}",
            "company": config.company_name,
            "employees_added": added,
            "employees_updated": updated,
            "total_tracked": stats['total_tracked'],
            "credits_used": config.employee_count
        }
    else:
        return {
            "success": False,
            "message": f"No employees found for company: {config.company_name}",
            "company": config.company_name,
            "employees_added": 0
        }

@app.post("/search/employees")
async def search_employees(search_params: IndividualEmployeeSearch):
    """Search for employees using individual criteria instead of company-based search"""

    tracker = EmployeeTracker()

    # Build SQL query based on provided parameters
    conditions = []

    if search_params.name:
        conditions.append(f"full_name LIKE '%{search_params.name}%'")

    if search_params.title:
        conditions.append(f"job_title LIKE '%{search_params.title}%'")

    if search_params.company:
        conditions.append(f"job_company_name LIKE '%{search_params.company}%'")

    if search_params.location:
        conditions.append(f"(job_company_location_locality LIKE '%{search_params.location}%' OR job_company_location_region LIKE '%{search_params.location}%' OR job_company_location_country LIKE '%{search_params.location}%')")

    if search_params.seniority_level:
        conditions.append(f"job_title_levels = '{search_params.seniority_level}'")

    if search_params.skills and len(search_params.skills) > 0:
        skill_conditions = " OR ".join([f"skills LIKE '%{skill}%'" for skill in search_params.skills])
        conditions.append(f"({skill_conditions})")

    if not conditions:
        raise HTTPException(status_code=400, detail="At least one search parameter is required")

    # Construct the SQL query
    where_clause = " AND ".join(conditions)
    sql_query = f"SELECT * FROM person WHERE {where_clause}"

    print(f"\n[SEARCH] Searching for employees with custom criteria")
    print(f"  Query: {sql_query}")

    # Use PDL API to search
    import requests

    params = {
        'sql': sql_query,
        'size': search_params.max_results
    }

    try:
        response = requests.post(
            tracker.base_url,
            headers=tracker.headers,
            json=params,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 200:
                employees = []

                for person in data.get('data', []):
                    # Extract relevant employee data
                    employee = {
                        'pdl_id': person.get('id'),
                        'name': person.get('full_name', 'Unknown'),
                        'title': person.get('job_title', 'N/A'),
                        'company': person.get('job_company_name', 'N/A'),
                        'location': f"{person.get('job_company_location_locality', '')}, {person.get('job_company_location_region', '')}",
                        'linkedin_url': person.get('linkedin_url', ''),
                        'skills': person.get('skills', [])[:5]  # Top 5 skills
                    }
                    employees.append(employee)

                print(f"  Found {len(employees)} employees matching criteria")

                return {
                    "success": True,
                    "count": len(employees),
                    "employees": employees,
                    "credits_used": search_params.max_results
                }
            else:
                return {
                    "success": False,
                    "message": f"Search failed: {data.get('error', 'Unknown error')}",
                    "employees": []
                }

        elif response.status_code == 402:
            raise HTTPException(status_code=402, detail="PDL API credits exhausted")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"PDL API error: {response.text}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Search request timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Search request failed: {str(e)}")

@app.post("/track/individual")
async def track_individual_employee(employee: TrackIndividualEmployee):
    """Add a specific individual employee to tracking"""

    tracker = EmployeeTracker()

    # Check if employee already exists
    existing_employees = tracker.db.get_all_employees()
    for emp in existing_employees:
        if emp['pdl_id'] == employee.pdl_id and emp['status'] != 'deleted':
            return {
                "success": False,
                "message": f"Employee {employee.name} is already being tracked",
                "pdl_id": employee.pdl_id
            }

    # Create employee record
    employee_data = [{
        'pdl_id': employee.pdl_id,
        'name': employee.name,
        'title': employee.title,
        'company': employee.company,
        'current_company': employee.company,
        'linkedin_url': '',  # Can be updated later
        'status': 'active',
        'last_checked': datetime.now().isoformat()
    }]

    # Add to database
    added, updated = tracker.db.add_employees(employee_data, employee.company)

    if added > 0:
        stats = tracker.db.get_statistics()

        return {
            "success": True,
            "message": f"Successfully added {employee.name} to tracking",
            "pdl_id": employee.pdl_id,
            "total_tracked": stats['total_tracked']
        }
    else:
        return {
            "success": False,
            "message": "Failed to add employee to tracking",
            "pdl_id": employee.pdl_id
        }

@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get current scheduler state and next run time"""
    
    tracker = EmployeeTracker()
    state = tracker.get_scheduler_state()
    
    # Check if overdue
    is_overdue = False
    days_until_next = None
    
    if state['next_check_date']:
        next_check = datetime.fromisoformat(state['next_check_date'])
        now = datetime.now()
        
        if now > next_check:
            is_overdue = True
            days_overdue = (now - next_check).days
        else:
            days_until_next = (next_check - now).days
    
    return {
        "last_check": state['last_check_date'],
        "next_check": state['next_check_date'],
        "scheduler_enabled": state['scheduler_enabled'],
        "check_count": state['check_count'],
        "is_overdue": is_overdue,
        "days_until_next": days_until_next,
        "status": "overdue" if is_overdue else "scheduled" if state['scheduler_enabled'] else "disabled"
    }

@app.post("/scheduler/enable")
async def enable_scheduler(days_interval: int = 30):
    """Enable automatic scheduling with specified interval"""
    
    tracker = EmployeeTracker()
    next_check = datetime.now() + timedelta(days=days_interval)
    
    tracker.update_scheduler_state(
        next_check=next_check,
        enabled=True
    )
    
    return {
        "success": True,
        "message": f"Scheduler enabled with {days_interval} day interval",
        "next_check": next_check.isoformat()
    }

@app.post("/scheduler/disable")
async def disable_scheduler():
    """Disable automatic scheduling"""
    
    tracker = EmployeeTracker()
    tracker.update_scheduler_state(enabled=False)
    
    return {
        "success": True,
        "message": "Scheduler disabled"
    }

@app.get("/company-suggestions")
async def get_company_suggestions():
    """Get suggested employee counts for each company including custom ones"""

    # Predefined suggestions based on company size and importance
    predefined_suggestions = {
        "openai": {"min": 5, "recommended": 15, "max": 30},
        "anthropic": {"min": 5, "recommended": 15, "max": 30},
        "meta": {"min": 10, "recommended": 25, "max": 50},
        "google": {"min": 10, "recommended": 25, "max": 50},
        "google deepmind": {"min": 5, "recommended": 15, "max": 30},
        "microsoft": {"min": 10, "recommended": 20, "max": 40},
        "cohere": {"min": 3, "recommended": 10, "max": 20},
        "mistral": {"min": 3, "recommended": 10, "max": 20},
        "uber": {"min": 5, "recommended": 15, "max": 30},
        "airbnb": {"min": 5, "recommended": 15, "max": 30},
        "scale ai": {"min": 3, "recommended": 10, "max": 20},
        "linkedin": {"min": 5, "recommended": 15, "max": 30},
        "palantir": {"min": 5, "recommended": 15, "max": 30}
    }

    # Get custom companies and add default suggestions
    tracker = EmployeeTracker()
    db_companies = tracker.db.get_all_companies()

    suggestions = predefined_suggestions.copy()
    target_companies_lower = [c.lower() for c in TARGET_COMPANIES]

    # Add suggestions for custom companies
    for company_info in db_companies:
        company_name = company_info.get('company', '')
        if company_name.lower() not in target_companies_lower:
            # Default suggestion for custom companies
            suggestions[company_name] = {"min": 3, "recommended": 8, "max": 20}

    total_recommended = sum(s['recommended'] for s in suggestions.values())

    return {
        "suggestions": suggestions,
        "total_recommended_credits": total_recommended,
        "predefined_count": len(predefined_suggestions),
        "custom_count": len(suggestions) - len(predefined_suggestions),
        "note": "Adjust based on your budget and priority companies"
    }

@app.post("/company/{company_name}/set-default")
async def set_company_default(company_name: str, default_count: int = Query(..., ge=0, le=100)):
    """Set the default employee tracking count for a company (0 = no auto-refetch)"""

    tracker = EmployeeTracker()
    success = tracker.db.set_company_default_count(company_name, default_count)

    if success:
        return {
            "success": True,
            "message": f"Set default count for {company_name} to {default_count}",
            "company": company_name,
            "default_count": default_count
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to set default count")

@app.get("/company/{company_name}/default")
async def get_company_default(company_name: str):
    """Get the default employee tracking count for a company"""

    tracker = EmployeeTracker()
    default_count = tracker.db.get_company_default_count(company_name)

    if default_count is not None:
        return {
            "company": company_name,
            "default_count": default_count
        }
    else:
        return {
            "company": company_name,
            "default_count": None,
            "message": "No default set for this company"
        }

# Background tasks

async def monthly_check_background(send_alerts: bool, alert_email: Optional[str]):
    """Background task for departure check"""
    
    tracker_state['is_checking'] = True
    tracker_state['check_progress'] = 0
    tracker_state['check_message'] = 'Starting departure check...'
    
    try:
        tracker = EmployeeTracker()
        
        # Run the check
        departures = tracker.monthly_check()
        
        tracker_state['check_progress'] = 100
        tracker_state['last_check'] = datetime.now().isoformat()
        
        if departures:
            tracker_state['check_message'] = f'Found {len(departures)} departures'
            
            # Send email alerts if configured
            if send_alerts and alert_email:
                alert_sender = EmailAlertSender()
                for dep in departures:
                    await alert_sender.send_alert(
                        recipient_email=alert_email,
                        company=dep['old_company'],
                        departures=[dep]
                    )
        else:
            tracker_state['check_message'] = 'No departures detected'
        
        # Update scheduler state - schedule next check for 1st of next month
        from datetime import datetime
        import calendar

        now = datetime.now()
        # Calculate first day of next month
        if now.month == 12:
            next_check = datetime(now.year + 1, 1, 1, 9, 0, 0)  # Jan 1st next year at 9 AM
        else:
            next_check = datetime(now.year, now.month + 1, 1, 9, 0, 0)  # 1st of next month at 9 AM

        tracker.update_scheduler_state(
            last_check=now,
            next_check=next_check,
            enabled=True,
            increment_count=True
        )
        print(f"[SCHEDULER] Next check scheduled for: {next_check.strftime('%Y-%m-%d %H:%M')}")
            
    except Exception as e:
        tracker_state['check_message'] = f'Error: {str(e)}'
        tracker_state['check_progress'] = 0
    finally:
        tracker_state['is_checking'] = False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("EMPLOYEE TRACKER API v2")
    print("="*60)
    print("\nStarting server at: http://localhost:8002")
    print("API docs at: http://localhost:8002/api")
    print("\nKey Features:")
    print("- Track specific number of employees per company")
    print("- Departure checks (can run anytime)")
    print("- Email alerts for departures")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run("api_v2:app", host="0.0.0.0", port=8002, reload=True)