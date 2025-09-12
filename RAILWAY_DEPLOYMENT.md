# Railway Deployment Guide

## Quick Deployment Steps

Your app is now **Railway-ready** without breaking local functionality!

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment support"
git push origin main
```

### 2. Deploy on Railway

1. Go to [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the configuration

### 3. Add PostgreSQL Database

In Railway dashboard:
1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway will automatically set `DATABASE_URL`

### 4. Set Environment Variables

In Railway dashboard → Variables tab, add:

```env
# PDL API (Required)
PDL_API_KEY=your_pdl_api_key_here

# Email Configuration (Required for alerts)
EMAIL_SENDER=your.email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_RECIPIENTS=recipient@email.com
ALERT_LEVELS=2,3

# Optional
ENVIRONMENT=production
```

### 5. Deploy

Railway will automatically:
- Install dependencies from `requirements.txt`
- Use PostgreSQL (via DATABASE_URL)
- Start the FastAPI server
- Provide you with a URL like: `https://your-app.railway.app`

## What Changed (Minimal Impact)

### Files Added (Won't affect local):
- `scripts/database_postgres.py` - PostgreSQL version
- `scripts/database_factory.py` - Auto-selector
- `Procfile` - Railway process file
- `railway.json` - Railway configuration
- Added `psycopg2-binary` to requirements.txt

### Files Modified (2 lines changed):
- `scripts/employee_tracker.py` - Import from database_factory
- `scripts/test_departure_check.py` - Import from database_factory

## How It Works

- **Locally**: Uses SQLite (no DATABASE_URL = SQLite)
- **Railway**: Uses PostgreSQL (DATABASE_URL present = PostgreSQL)
- **Automatic**: No code changes needed between environments

## Testing Your Deployment

After deployment, test your endpoints:

1. **Health Check**:
   ```
   https://your-app.railway.app/health
   ```

2. **View Tracked Employees**:
   ```
   https://your-app.railway.app/
   ```

3. **API Docs**:
   ```
   https://your-app.railway.app/docs
   ```

## Monthly Checks on Railway

For automated monthly checks, you have two options:

### Option 1: Railway Cron (Recommended)
Add a cron job in Railway that calls:
```
https://your-app.railway.app/api/check-departures
```

### Option 2: External Cron Service
Use [cron-job.org](https://cron-job.org) (free) to call your endpoint monthly.

## Troubleshooting

1. **Database Connection Error**:
   - Check DATABASE_URL is set in Railway
   - PostgreSQL addon is attached

2. **Import Errors**:
   - Ensure all files are committed to Git
   - Check `requirements.txt` has all dependencies

3. **Email Not Sending**:
   - Verify EMAIL_* environment variables
   - Use app-specific password for Gmail

## Your Demo Is Safe!

- **Local development continues using SQLite**
- **No configuration needed locally**
- **All test scripts work unchanged**
- **Railway automatically uses PostgreSQL**

## Next Steps

1. Commit and push these changes
2. Deploy to Railway
3. Your app will be live in ~2 minutes!

The system intelligently uses SQLite locally and PostgreSQL on Railway - best of both worlds!