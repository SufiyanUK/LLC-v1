# Railway Deployment Guide for Employee Tracker

## ✅ Your Local System is 100% Safe!
- **Local still uses SQLite** - No changes to your local database
- **All your data is intact** - 16 employees tracked, including Uber
- **Factory pattern ensures** - Local = SQLite, Railway = PostgreSQL

## Files Added (Don't affect local):
1. `scripts/database_postgres.py` - PostgreSQL version (only for Railway)
2. `scripts/database_factory.py` - Smart selector (chooses SQLite locally)
3. `Procfile` - Railway process definition
4. `railway.json` - Railway configuration
5. `psycopg2-binary` in requirements.txt

## Minimal Changes Made:
- Only 2 import lines changed (from `database` to `database_factory`)
- This allows automatic database selection based on environment

## Railway Deployment Steps:

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway PostgreSQL support"
git push origin main
```

### 2. Create Railway Project
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect Python app

### 3. Add PostgreSQL Database
In Railway dashboard:
1. Click "New" → "Database" 
2. Select "Add PostgreSQL"
3. Railway automatically sets `DATABASE_URL`

### 4. Set Environment Variables
In Railway dashboard → Variables tab:

```env
# CRITICAL - Must be exactly "API_KEY"
API_KEY=your_peopledatalabs_api_key_here

# Email Configuration (if using alerts)
EMAIL_SENDER=your.email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_RECIPIENTS=recipient@email.com
ALERT_LEVELS=2,3

# Optional
ENVIRONMENT=production
```

⚠️ **IMPORTANT**: The variable MUST be named `API_KEY` (not PDL_API_KEY)

### 5. Deploy
Railway will automatically:
- Detect Python from `requirements.txt`
- Install all dependencies including PostgreSQL
- Use `Procfile` to start your app
- Provide a URL like: `https://your-app.railway.app`

## How It Works:

### Locally (your machine):
```python
# No DATABASE_URL environment variable
# database_factory.py imports from database.py
# Uses SQLite at data/tracking.db
```

### On Railway:
```python
# DATABASE_URL is set by Railway
# database_factory.py imports from database_postgres.py  
# Uses PostgreSQL database
```

## Testing After Deployment:

1. **Check health**:
   ```
   https://your-app.railway.app/health
   ```

2. **View API**:
   ```
   https://your-app.railway.app/api
   ```

3. **Access UI**:
   ```
   https://your-app.railway.app/
   ```

## Data Migration (Optional):

If you want to copy your local data to Railway:

1. Export from local SQLite:
```python
# Run locally
from scripts.database import TrackingDatabase
db = TrackingDatabase()
employees = db.get_all_employees()
# Save to JSON file
```

2. Import to Railway PostgreSQL:
```python
# Run on Railway (via console or script)
from scripts.database_postgres import TrackingDatabase
db = TrackingDatabase()
# Load JSON and add employees
```

## Troubleshooting:

### Issue: "Invalid API key"
- **Solution**: Ensure environment variable is named `API_KEY` (not PDL_API_KEY)

### Issue: Database connection error
- **Solution**: Check DATABASE_URL is set in Railway (automatic with PostgreSQL addon)

### Issue: No employees showing
- **Solution**: PostgreSQL starts empty - you need to add employees again or migrate data

### Issue: Import errors
- **Solution**: Ensure all files are committed to Git, including the new database files

## Monthly Automation on Railway:

Railway doesn't have built-in cron, so use:

1. **External service** like [cron-job.org](https://cron-job.org) (free)
2. Set it to call: `https://your-app.railway.app/check/monthly`
3. Schedule: Monthly on the 1st at 9 AM

## Your Local Development:

**Nothing changes!** Continue using:
```bash
cd employee_tracker
python api_v2.py
```

- Still uses SQLite
- Still has all your data (16 employees)
- No PostgreSQL needed locally
- No configuration changes needed

## Summary:

✅ **Local**: SQLite (unchanged, working perfectly)
✅ **Railway**: PostgreSQL (automatic via DATABASE_URL)
✅ **Code**: Smart enough to use the right database
✅ **Safety**: Your local system is 100% unaffected

The beauty is that the same code works in both environments!