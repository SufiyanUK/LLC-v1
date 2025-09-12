# Employee Tracker - Testing Guide

## Quick Test (No Credits)

### Option 1: Use the Mock Test System
```bash
cd employee_tracker/test_system
python test_departure_system.py
```
This uses completely mock data and tests the classification logic.

### Option 2: Test with Database Manipulation
```bash
cd employee_tracker
python scripts/test_departure_check.py
```
This checks your actual tracked employees but uses database data instead of PDL API.

## How to Test Departures with Real Data (No Credits)

### Step 1: Track Some Employees
Use the web UI to track a few employees from any company.

### Step 2: Manually Simulate a Departure
Use SQLite to update an employee's company:

```sql
-- Connect to the database
sqlite3 data/tracking.db

-- View tracked employees
SELECT pdl_id, name, company, current_company FROM tracked_employees WHERE status='active';

-- Simulate a departure to a startup (Level 3 alert)
UPDATE tracked_employees 
SET 
    current_company = 'TinyStartup AI',
    job_last_changed = datetime('now'),
    full_data = json_object(
        'job_company_name', 'TinyStartup AI',
        'job_company_size', '1-10',
        'job_company_founded', '2024',
        'job_title', 'CTO & Co-Founder',
        'headline', 'CTO at TinyStartup AI | Building the future',
        'job_company_type', 'startup'
    )
WHERE pdl_id = 'YOUR_PDL_ID_HERE';
```

### Step 3: Run the Test Departure Check
```bash
python scripts/test_departure_check.py
```

This will:
- Check all employees using database data (not PDL API)
- Detect the simulated departure
- Classify it (Level 1, 2, or 3)
- Save it to the departures table
- Show what alert would be sent

### Step 4: View Results
Check the web UI:
- Go to "Departures" tab
- You'll see the departure with its classification
- Color coding: 🔴 Red (Level 3), 🟠 Orange (Level 2), 🟡 Yellow (Level 1)

## Test Different Alert Levels

### Level 1 - Standard Departure (Yellow)
```sql
UPDATE tracked_employees 
SET current_company = 'Microsoft',
    full_data = json_object('job_company_name', 'Microsoft', 'job_company_size', '10000+')
WHERE pdl_id = 'YOUR_PDL_ID';
```

### Level 2 - Building Signals (Orange)
```sql
UPDATE tracked_employees 
SET current_company = 'Stealth Mode',
    full_data = json_object(
        'job_company_name', 'Stealth Mode',
        'headline', 'Building something new in AI | Ex-OpenAI',
        'summary', 'Working on exciting project in stealth'
    )
WHERE pdl_id = 'YOUR_PDL_ID';
```

### Level 3 - Joined Startup (Red)
```sql
UPDATE tracked_employees 
SET current_company = 'NewCo AI',
    full_data = json_object(
        'job_company_name', 'NewCo AI',
        'job_company_size', '11-50',
        'job_company_founded', '2024',
        'job_title', 'Founding Engineer'
    )
WHERE pdl_id = 'YOUR_PDL_ID';
```

## Reset After Testing

To reset an employee back to their original company:
```sql
UPDATE tracked_employees 
SET current_company = company,
    job_last_changed = NULL
WHERE pdl_id = 'YOUR_PDL_ID';

-- Also clean up departures
DELETE FROM departures WHERE pdl_id = 'YOUR_PDL_ID';
```

## Understanding Alert Classifications

### Level 3 (🔴 HIGH PRIORITY)
Triggers when employee joins:
- Company size: 1-50 employees
- Company founded: 2020 or later
- Title contains: Founder, Co-Founder, CTO
- Company type: startup
- No company name (stealth mode)

### Level 2 (🟠 BUILDING SIGNALS)
Triggers when bio/headline contains:
- "building something"
- "working on something new"
- "stealth mode"
- "exploring ideas"
- "taking time off to"
- 50+ other building phrases

### Level 1 (🟡 STANDARD)
- Any other departure
- Typically big tech to big tech moves

## Important Notes

1. **The normal departure check uses PDL API** - It will NOT detect manually changed database entries
2. **Use test_departure_check.py** - This script checks database data instead of PDL API
3. **Credits are only used** when you run the normal "Check for Departures" or when tracking new employees
4. **Test data won't affect production** - You can safely test and then clean up