# Default Employee Tracking Feature

## Overview

This feature allows you to set a default number of employees to track for each company. When you delete an employee and the active count falls below the default, the system will automatically fetch new employees to maintain the default count.

## Key Features

### 1. Set Default Counts Per Company

- Each company can have a configurable default employee count (0-100)
- Default counts are displayed on company cards in the UI
- Defaults are stored in the database and persist across sessions

### 2. Automatic Refetch on Delete

When you delete an employee:
- The system checks if the company has a default count set
- If the active employee count falls below the default, it automatically fetches replacement employees
- This ensures you always maintain your desired tracking level

### 3. Visual Indicators

In the web UI, each company card shows:
- **Tracked**: Current number of active employees being tracked
- **Default**: The target number of employees to maintain (if set)
- **Add**: Input to add more employees immediately
- **Default**: Input to set/change the default count

## How to Use

### Setting a Default Count

1. Open the web interface (index_v3.html)
2. Find the company card you want to configure
3. Locate the "Default:" input field at the bottom of the card
4. Enter your desired default count (e.g., 5 for OpenAI)
5. The default is saved automatically when you change the value

### Example Workflow

**Initial Setup:**
```
OpenAI:
  Tracked: 0 employees
  Default: 5 (you set this)
  Action: Click "Add" and add 5 employees
```

**After Adding:**
```
OpenAI:
  Tracked: 5 employees
  Default: 5
```

**When You Delete an Employee:**
```
Before Delete:
  OpenAI - Tracked: 5 employees

Action: Delete 1 employee

After Delete (Automatic):
  OpenAI - Tracked: 5 employees (1 deleted, 1 auto-fetched as replacement)
```

## API Endpoints

### Set Default Count
```bash
POST /company/{company_name}/set-default?default_count=5
```

### Get Default Count
```bash
GET /company/{company_name}/default
```

### Delete Employee (with auto-refetch)
```bash
DELETE /track/employee/{pdl_id}?auto_refetch=true
```

Response includes:
```json
{
  "success": true,
  "message": "Employee {id} has been removed from tracking",
  "company": "openai",
  "remaining_count": 4,
  "default_count": 5,
  "auto_refetch": {
    "success": true,
    "message": "Auto-fetched 1 replacement employee(s)",
    "employees_added": 1,
    "new_employees": [...]
  }
}
```

## Database Schema

The `company_config` table now includes:
```sql
CREATE TABLE company_config (
    company TEXT PRIMARY KEY,
    employee_count INTEGER,
    default_employee_count INTEGER DEFAULT 5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Migration

If you have an existing database, run the migration script:
```bash
python migrate_add_default_count.py
```

This adds the `default_employee_count` column to existing databases without losing data.

## Benefits

1. **Consistency**: Maintain consistent tracking levels across all companies
2. **Automation**: No manual intervention needed when removing employees
3. **Flexibility**: Different defaults for different companies based on importance
4. **Visibility**: Clear indication of targets vs actual tracking on the UI

## Example Use Cases

### Scenario 1: High-Priority Companies
```
OpenAI:     Default = 15 (critical to track closely)
Anthropic:  Default = 15
Meta:       Default = 10
```

### Scenario 2: Budget-Conscious Tracking
```
OpenAI:     Default = 5 (focused tracking)
Anthropic:  Default = 5
Others:     Default = 3
```

### Scenario 3: No Auto-Refetch
```
Company X:  Default = 0 (manual management only)
```

## Technical Notes

- Auto-refetch is enabled by default but can be disabled by passing `auto_refetch=false` to the delete endpoint
- Only active (non-deleted) employees count toward the default threshold
- The system excludes already-tracked employees when fetching replacements
- Each fetch operation uses PDL API credits (1 credit per employee)

## Testing

Run the test script to verify functionality:
```bash
python test_default_count.py
```

This tests:
- Database schema
- Setting default counts
- Getting default counts
- Retrieving all company defaults
