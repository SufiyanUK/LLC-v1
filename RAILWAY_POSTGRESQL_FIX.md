# Railway PostgreSQL Database Fix Guide

## Problem
When deployed on Railway with PostgreSQL, the database has 0 tables and shows no companies or employees. This is because the tables aren't being created properly during initialization.

## Root Cause
The PostgreSQL database initialization may fail silently on Railway due to:
1. Connection issues during first deployment
2. Permission problems creating tables
3. Timing issues with database availability

## Solution Steps

### Step 1: Initialize Database Tables (One-Time Setup)

After deploying to Railway, you need to initialize the database tables. There are two ways to do this:

#### Option A: Using Railway CLI (Recommended)

1. Install Railway CLI if you haven't:
```bash
npm i -g @railway/cli
```

2. Link to your project:
```bash
railway link
```

3. Run the initialization script:
```bash
railway run python init_railway_db.py
```

#### Option B: Using Railway Shell

1. Go to your Railway project dashboard
2. Click on your service
3. Go to the "Settings" tab
4. Click "Generate Domain" if you haven't already
5. Click on "Run Command" or open Railway Shell
6. Run:
```bash
python init_railway_db.py
```

### Step 2: Migrate Existing Data (Optional)

If you have existing data in your local SQLite database that you want to transfer to Railway:

#### From Local Machine:

1. Get your Railway PostgreSQL connection string:
   - Go to Railway Dashboard
   - Click on PostgreSQL plugin
   - Copy the DATABASE_URL

2. Set the environment variable locally:
```bash
# Windows
set DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Mac/Linux
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

3. Run the migration:
```bash
python migrate_to_postgresql.py
```

### Step 3: Verify Database Setup

Check if everything is working:

1. Visit your Railway app URL
2. Check the `/health` endpoint: `https://your-app.railway.app/health`
3. Check the `/companies` endpoint: `https://your-app.railway.app/companies`

## Automated Fix (Add to railway.json)

To ensure tables are always created, update your `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python init_railway_db.py && python -m uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "NEVER",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "numReplicas": 1
  }
}
```

## Environment Variables Required

Make sure these are set in Railway:

```
DATABASE_URL=<automatically set by PostgreSQL plugin>
API_KEY=<your PDL API key>
BREVO_API_KEY=<your email API key>
BREVO_SENDER_EMAIL=<your sender email>
BREVO_SENDER_NAME=<your sender name>
PORT=<automatically set by Railway>
```

## Files Created for Fix

1. **init_railway_db.py** - Initializes PostgreSQL tables
2. **migrate_to_postgresql.py** - Migrates data from SQLite to PostgreSQL
3. **database_postgres.py** - PostgreSQL database adapter (already exists)
4. **database_factory.py** - Auto-selects database based on environment

## Testing Database Connection

To test if PostgreSQL is working on Railway:

```python
# Quick test script (save as test_railway_db.py)
import os
import psycopg2
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    result = urlparse(database_url)
    db_config = {
        'database': result.path[1:],
        'user': result.username,
        'password': result.password,
        'host': result.hostname,
        'port': result.port or 5432
    }

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        count = cursor.fetchone()[0]
        print(f"✅ Connected! Found {count} tables")

        cursor.execute("SELECT COUNT(*) FROM tracked_employees")
        emp_count = cursor.fetchone()[0]
        print(f"✅ Found {emp_count} employees")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ DATABASE_URL not found")
```

## Common Issues and Solutions

### Issue 1: "No tables found"
**Solution:** Run `python init_railway_db.py` on Railway

### Issue 2: "psycopg2 not installed"
**Solution:** Make sure `psycopg2-binary==2.9.9` is in requirements.txt

### Issue 3: "Connection refused"
**Solution:** Wait a few minutes for PostgreSQL to fully initialize, then redeploy

### Issue 4: "Permission denied"
**Solution:** The PostgreSQL plugin should have full permissions. Contact Railway support if this persists.

## Deployment Checklist

- [ ] PostgreSQL plugin added to Railway project
- [ ] DATABASE_URL is automatically configured
- [ ] API_KEY environment variable set
- [ ] requirements.txt includes psycopg2-binary
- [ ] Pushed latest code to GitHub
- [ ] Railway deployment successful
- [ ] Run init_railway_db.py to create tables
- [ ] Verify at /health endpoint
- [ ] Check companies at /companies endpoint
- [ ] (Optional) Migrate existing data

## Support

If issues persist after following this guide:

1. Check Railway logs for specific error messages
2. Verify PostgreSQL plugin is running (green status)
3. Try redeploying the service
4. Run `python init_railway_db.py` manually via Railway CLI

The initialization script will show detailed output about what's happening with the database connection and table creation.