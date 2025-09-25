# Quick Railway PostgreSQL Import Guide

## Fastest Method: Use Railway Dashboard

1. **Open Railway Dashboard**
   - Go to https://railway.app/dashboard
   - Select your project
   - Click on PostgreSQL service

2. **Go to Query Tab**
   - Click "Query" in the PostgreSQL service
   - This opens the SQL query interface

3. **Import Your Data**
   - Open `employee_inserts.sql` in a text editor
   - Copy ALL content (Ctrl+A, Ctrl+C)
   - Paste into Railway Query interface
   - Click "Run Query"
   - You should see "Query executed successfully"

4. **Import Company Configs**
   - Open `company_config_inserts.sql`
   - Copy ALL content
   - Paste into Railway Query interface
   - Click "Run Query"

5. **Verify Import**
   Run this query to check:
   ```sql
   SELECT COUNT(*) as employee_count FROM tracked_employees;
   SELECT COUNT(*) as company_count FROM company_config;
   ```

## Alternative: Use Railway CLI

```bash
# 1. Install CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Link to project
railway link

# 4. Run SQL directly
railway connect postgres

# In another terminal, while proxy is running:
psql "postgresql://postgres:password@localhost:PORT/railway" < employee_inserts.sql
psql "postgresql://postgres:password@localhost:PORT/railway" < company_config_inserts.sql
```

## Verify Your App Connection

Your Railway app should automatically connect to PostgreSQL if both services are in the same project. Check:

1. Go to your **App Service** in Railway
2. Click **Variables** tab
3. Ensure `DATABASE_URL` is listed (Railway auto-adds this)
4. Redeploy your app if needed: Click **"Redeploy"**

## Test the Connection

Visit your deployed app:
```
https://your-app.railway.app/health
```

Should show:
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