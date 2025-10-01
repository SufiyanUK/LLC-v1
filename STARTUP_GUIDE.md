# Quick Startup Guide

## Issue Fixed

The HTML was pointing to port **8001** but the API runs on **8002**. This has been fixed.

## Step-by-Step Startup

### 1. Start the API Server

Open a terminal in the project directory and run:

```bash
python api_v2.py
```

You should see:
```
============================================================
EMPLOYEE TRACKER API v2
============================================================

Starting server at: http://localhost:8002
API docs at: http://localhost:8002/api

Key Features:
- Track specific number of employees per company
- Departure checks (can run anytime)
- Email alerts for departures

Press Ctrl+C to stop
============================================================

INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

**Important:** Keep this terminal window open! The server needs to keep running.

### 2. Open the Web Interface

Once the server is running, open your web browser and go to:

```
http://localhost:8002
```

You should now see:
- **Companies tab**: All 15 companies with their tracked employee counts
- **Default counts** showing on each company card (🎯 Default: 5)
- **Manage Employees tab**: List of all 37 active employees

### 3. Test the Default Count Feature

1. Find a company (e.g., "openai" which has 3 employees)
2. Set the **Default** field to `5`
3. It will auto-save and show "🎯 Default: 5"
4. Go to **Manage Employees** tab
5. Delete one OpenAI employee
6. Watch the system auto-fetch 1 replacement to maintain the default!

## Troubleshooting

### Problem: "Cannot connect" or empty page

**Solution:** Make sure the API server is running in a terminal window

```bash
python api_v2.py
```

### Problem: Port 8002 already in use

**Solution:** Kill any existing process on that port:

**Windows:**
```bash
netstat -ano | findstr :8002
taskkill /PID <PID_NUMBER> /F
```

**Alternative:** Change the port in both files:
- `api_v2.py` line 1044: Change `port=8002`
- `index_v3.html` line 760: Change `http://localhost:8002`

### Problem: Still see empty data

**Solution:**
1. Press `F12` in browser to open DevTools
2. Go to **Console** tab
3. Look for any red error messages
4. Check **Network** tab - are the API calls returning 200 or errors?

## Verify Database Has Data

Run this quick check:

```bash
python diagnose_db.py
```

You should see:
```
Total employees: 39
Active employees: 37
```

## Your Current Data

Based on diagnostics:
- ✅ 37 active employees being tracked
- ✅ 15 companies configured
- ✅ Companies include: OpenAI (3), Anthropic (5), Microsoft (4), Meta (3), etc.
- ✅ Default counts set to 5 for all companies

Everything is ready to go! Just start the server and open the browser.
