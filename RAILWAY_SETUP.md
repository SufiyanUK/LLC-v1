# Railway Deployment Setup Guide

## Steps to Create New Railway Services

### 1. Create New Railway Project
1. Go to [Railway](https://railway.app)
2. Click "New Project"
3. Choose "Empty Project"

### 2. Add PostgreSQL Database
1. Click "+ New" in your project
2. Select "Database" → "PostgreSQL"
3. Railway will automatically provision a PostgreSQL database
4. Click on the PostgreSQL service to see the connection details
5. Copy the `DATABASE_URL` from the Variables tab

### 3. Deploy Your App
1. Click "+ New" → "GitHub Repo" or "Deploy from CLI"
2. If using GitHub:
   - Connect your GitHub account
   - Select your repository
   - Railway will auto-deploy

3. If using CLI:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login to Railway
   railway login

   # Initialize project
   railway link [project-id]

   # Deploy
   railway up
   ```

### 4. Set Environment Variables
In your Railway app service, go to Variables tab and add:

```env
# PDL API Key
API_KEY=e6419b40326f0d2a7848b04c2be9ad0b46b868963cb8f4cb4b6764f58c8427ac

# Email Configuration (Brevo)
BREVO_API_KEY=<YOUR_BREVO_API_KEY_HERE>-hv8po24OgD5n4ajw
BREVO_SENDER_EMAIL=alerts@venrock.com
BREVO_SENDER_NAME=Venrock Alerts

# SMTP Fallback
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=muazzainmuhammad07@gmail.com
SENDER_PASSWORD=kkja cuwd kohh voix

# Alert Settings
ALERT_EMAIL=venrocksourcing@gmail.com
MIN_ALERT_LEVEL=1

# Cron Security
CRON_SECRET_TOKEN=vr-tracker-secret-2024-x7k9m3

# Note: DATABASE_URL will be automatically added by Railway
```

### 5. Import Your Data
Once deployed, you can import the SQLite data using the Railway dashboard:

1. Go to your PostgreSQL service in Railway
2. Click "Query" tab
3. Copy and paste the content from `employee_inserts.sql`
4. Click "Run Query"
5. Repeat for `company_config_inserts.sql`

### Alternative: Import via API Endpoint
Add this endpoint to your `api_v2.py`:

```python
@app.post("/admin/import-data")
async def import_data(token: str = Header(...)):
    """Import data from SQL files (admin only)"""
    if token != os.getenv('CRON_SECRET_TOKEN'):
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Your import logic here
    return {"status": "Data imported"}
```

## File Structure for Deployment

Your repository should have:
```
├── api_v2.py              # Main API file
├── requirements.txt       # Python dependencies
├── railway.toml          # Railway configuration
├── Procfile             # Process file for Railway
├── runtime.txt          # Python version
├── .env                 # Local environment variables (don't commit!)
├── scripts/             # Your scripts folder
├── config/              # Your config folder
├── data/                # Data folder (will be created)
└── employee_inserts.sql # SQL data to import
```

## Testing Connection

Once deployed, test your Railway PostgreSQL from the deployed app:

1. Access your app: `https://your-app.railway.app/health`
2. Check database status in the response
3. The connection should work because both services are in the same Railway project

## Local Development vs Railway

- **Local**: Uses SQLite (`data/tracking.db`)
- **Railway**: Uses PostgreSQL (auto-detected via `DATABASE_URL`)

The app automatically switches between them based on the `DATABASE_URL` environment variable presence.

## Troubleshooting

### If PostgreSQL still times out:
1. **Check Railway Dashboard**: Ensure PostgreSQL service is running (green status)
2. **Redeploy Database**: Click "Redeploy" on the PostgreSQL service
3. **Check Variables**: Ensure `DATABASE_URL` is in your app's environment variables
4. **Network Settings**: Railway databases only accept connections from within the same project

### If deployment fails:
1. Check build logs in Railway dashboard
2. Ensure all dependencies are in `requirements.txt`
3. Verify Python version compatibility
4. Check for missing environment variables

## Next Steps

1. Push your code to GitHub (if using GitHub deployment)
2. Or use `railway up` to deploy via CLI
3. Import your data using the Railway Query interface
4. Test the API endpoints
5. Set up monitoring/alerts

Your app will be available at: `https://[your-project].railway.app`