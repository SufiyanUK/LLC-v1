# Railway Deployment Debug Guide

## Issues Fixed:
1. ✅ Fixed `main.py` import path (was looking for non-existent `employee_tracker.api_v2`)
2. ✅ Removed problematic `pathlib==1.0.1` from requirements.txt
3. ✅ Added missing `__init__.py` files to `scripts/` and `config/` directories
4. ✅ Updated uvicorn to `uvicorn[standard]` for better Railway compatibility

## To Deploy/Redeploy:

### Option 1: Git Push (If connected to GitHub)
```bash
git add .
git commit -m "Fix Railway deployment issues - import paths and dependencies"
git push origin main
```

### Option 2: Railway CLI Deploy
```bash
# Install Railway CLI if not already done
npm install -g @railway/cli

# Login and link
railway login
railway link

# Deploy
railway up
```

## Debug Steps if Still Not Working:

### 1. Check Railway Logs
- Go to Railway Dashboard
- Click on your App service
- Click "Deployments" tab
- Click on the latest deployment
- Check "Build Logs" and "Deploy Logs"

### 2. Common Error Messages and Solutions:

**Error: "ModuleNotFoundError: No module named 'scripts'"**
- Solution: Added `__init__.py` files ✅

**Error: "ModuleNotFoundError: No module named 'employee_tracker.api_v2'"**
- Solution: Fixed import path in main.py ✅

**Error: "Could not find a version that satisfies the requirement pathlib"**
- Solution: Removed pathlib from requirements.txt ✅

**Error: "Application startup failed"**
- Check DATABASE_URL is set in Railway variables
- Ensure PostgreSQL service is running

**Error: "Port binding failed"**
- Railway automatically sets PORT environment variable
- Our code uses `int(os.environ.get("PORT", 8000))`

### 3. Environment Variables Check
Ensure these are set in Railway App service → Variables:
```
API_KEY=<YOUR_PDL_API_KEY_HERE>
BREVO_API_KEY=<YOUR_BREVO_API_KEY_HERE>
BREVO_SENDER_EMAIL=<YOUR_SENDER_EMAIL>
BREVO_SENDER_NAME=<YOUR_SENDER_NAME>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=<YOUR_EMAIL_HERE>
SENDER_PASSWORD=<YOUR_APP_PASSWORD_HERE>
ALERT_EMAIL=<YOUR_ALERT_EMAIL_HERE>
MIN_ALERT_LEVEL=1
CRON_SECRET_TOKEN=<YOUR_SECRET_TOKEN_HERE>
```

Note: `DATABASE_URL` should be automatically added by Railway when PostgreSQL is connected.

### 4. Health Check
Once deployed, test:
```
https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "railway",
  "database": {
    "type": "postgresql",
    "connected": true
  }
}
```

### 5. API Documentation
```
https://your-app.railway.app/docs
```

## File Structure Summary:
```
├── main.py                 # ✅ Fixed - imports from api_v2
├── api_v2.py              # ✅ Main API file
├── requirements.txt       # ✅ Fixed - removed pathlib
├── railway.toml          # ✅ Railway config
├── Procfile              # ✅ Process definition
├── runtime.txt           # ✅ Python version
├── scripts/
│   ├── __init__.py       # ✅ Added for module import
│   ├── employee_tracker.py
│   ├── email_alerts.py
│   └── database_factory.py
└── config/
    ├── __init__.py       # ✅ Added for module import
    └── target_companies.py
```

## Next Steps:
1. Commit and push the fixes
2. Check Railway deployment logs
3. Test the /health endpoint
4. Import employee data using Railway PostgreSQL Query interface