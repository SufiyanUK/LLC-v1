# Cron Job Setup Guide for Monthly Departure Checks

## What's Been Implemented

✅ **Security Token**: Added to `.env` for authentication
✅ **Database Schema**: Added scheduler tracking tables
✅ **API Endpoints**: Added security and auto-scheduling logic
✅ **Scheduler Status**: New endpoints to track scheduling
✅ **UI Updates**: Shows next scheduled check and status

## Your Railway App URL

First, get your Railway app URL:
1. Go to Railway dashboard
2. Click on your app
3. Find the domain (e.g., `your-app-name.up.railway.app`)

## Setting Up Cron-job.org (Recommended - FREE)

### Step 1: Sign Up
1. Go to https://cron-job.org
2. Click "Sign Up" (free, no credit card)
3. Verify your email

### Step 2: Create New Cron Job

Click "Create cronjob" and enter these EXACT settings:

**Title:** 
```
Employee Departure Check
```

**URL:** 
```
https://YOUR-RAILWAY-APP.up.railway.app/check/monthly
```
(Replace YOUR-RAILWAY-APP with your actual Railway domain)

**Schedule:**
- **Execution schedule:** Every month
- **Days:** 1 (first day of month)
- **Time:** 09:00 (or your preferred time)
- **Timezone:** Your timezone

**Request Settings:**
- **Request method:** POST

**Advanced Settings - Headers:**
Click "Show Advanced Settings" and add these headers:
```
Content-Type: application/json
X-Cron-Token: vr-tracker-secret-2024-x7k9m3
```

**Request Body:**
```json
{
  "send_alerts": true,
  "alert_email": "venrocksourcing@gmail.com"
}
```

**Save Settings:**
- Enable: ✅ (checked)
- Save cronjob

### Step 3: Test It

1. Click "Test run" to verify it works
2. Check the execution log for success

## How It Works

### First Time:
1. You manually click "Run Departure Check" in the UI
2. System runs the check and automatically sets `next_check_date = now + 30 days`
3. Scheduler is now enabled

### Every Month After:
1. Cron-job.org calls your endpoint on the 1st at 9 AM
2. System runs departure check
3. Sends email alerts to venrocksourcing@gmail.com via Brevo
4. Automatically schedules next check for 30 days later
5. Updates UI with next check date

### If Cron Fails:
- UI shows "OVERDUE" status
- Alert appears: "Manual check needed!"
- You can run manually from UI

## Security Features

✅ **Token Protection**: Only requests with correct `X-Cron-Token` are accepted from external sources
✅ **Manual Override**: UI can still trigger checks without token
✅ **Rate Limiting**: Can't run multiple checks simultaneously
✅ **Email Alerts**: Uses Brevo (not your personal email)

## Monitoring

### In Your UI:
- Shows last check date
- Shows next scheduled date
- Shows if check is overdue
- Shows total checks run

### In Cron-job.org:
- View execution history
- Get email if job fails
- See response codes

## Alternative: GitHub Actions (If your code is on GitHub)

Create `.github/workflows/monthly-check.yml`:

```yaml
name: Monthly Departure Check

on:
  schedule:
    - cron: '0 9 1 * *'  # 1st of month at 9 AM UTC
  workflow_dispatch:     # Allow manual trigger

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Departure Check
        run: |
          curl -X POST https://YOUR-RAILWAY-APP.up.railway.app/check/monthly \
            -H "Content-Type: application/json" \
            -H "X-Cron-Token: vr-tracker-secret-2024-x7k9m3" \
            -d '{"send_alerts": true, "alert_email": "venrocksourcing@gmail.com"}'
```

## Testing Your Setup

1. **Check Scheduler Status:**
   ```
   GET https://YOUR-RAILWAY-APP.up.railway.app/scheduler/status
   ```

2. **Manually Enable Scheduler:**
   ```
   POST https://YOUR-RAILWAY-APP.up.railway.app/scheduler/enable?days_interval=30
   ```

3. **View in UI:**
   - Open your app
   - Go to "Check Departures" tab
   - See "Auto-Scheduler Status" section

## Important Notes

- First departure check must be run manually to enable scheduler
- All subsequent checks happen automatically every 30 days
- Emails go to venrocksourcing@gmail.com via Brevo
- No personal email exposure
- Works perfectly with Railway's infrastructure

## Troubleshooting

**"Invalid cron token" error:**
- Check the X-Cron-Token header matches exactly
- Token: `vr-tracker-secret-2024-x7k9m3`

**Check not running:**
- Verify Railway app is running
- Check cron-job.org execution logs
- Ensure URL is correct (https, not http)

**Email not received:**
- Check spam folder
- Verify Brevo API key is correct
- Check venrocksourcing@gmail.com inbox

## Support

If you need help:
1. Check cron-job.org execution logs
2. Check Railway deployment logs
3. Test manually from UI first