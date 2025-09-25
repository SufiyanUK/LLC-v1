# FastAPI Alert Pipeline API with Ngrok

Simple REST API for the Alert Pipeline system that can be exposed publicly using ngrok.

## Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r api_requirements.txt
```

### Step 2: Run the API
```bash
python api.py
```
The API will start at `http://localhost:8000`

### Step 3: Expose with Ngrok
In a new terminal:
```bash
ngrok http 8000
```

You'll get a public URL like: `https://abc123.ngrok-free.app`

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API documentation and status |
| GET | `/dashboard` | Dashboard stats and recent alerts |
| GET | `/alerts` | Get all alerts |
| GET | `/alerts/high-priority` | Get Level 2 & 3 alerts only |
| GET | `/companies` | List all qualified startups |
| POST | `/companies` | Add new company |
| DELETE | `/companies/{index}` | Delete company by index |
| POST | `/run-pipeline` | Start the alert pipeline |
| GET | `/pipeline-status` | Check pipeline status |

### Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/alerts/export/csv` | Export alerts data |
| GET | `/companies/export/csv` | Export companies data |

## Usage Examples

### 1. Check API Status
```bash
curl https://your-ngrok-url.ngrok-free.app/
```

### 2. Get Dashboard
```bash
curl https://your-ngrok-url.ngrok-free.app/dashboard
```

### 3. Add a Company
```bash
curl -X POST https://your-ngrok-url.ngrok-free.app/companies \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechStartup Inc",
    "founded_date": "2024-01-15",
    "industry": "AI/ML",
    "location": "San Francisco, CA",
    "description": "AI-powered analytics platform"
  }'
```

### 4. Run Pipeline
```bash
curl -X POST https://your-ngrok-url.ngrok-free.app/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 90,
    "max_credits": 20,
    "use_cache": true
  }'
```

### 5. Check Pipeline Status
```bash
curl https://your-ngrok-url.ngrok-free.app/pipeline-status
```

### 6. Get High Priority Alerts
```bash
curl https://your-ngrok-url.ngrok-free.app/alerts/high-priority
```

## Interactive API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

With ngrok:
- **Swagger UI**: `https://your-ngrok-url.ngrok-free.app/docs`
- **ReDoc**: `https://your-ngrok-url.ngrok-free.app/redoc`

## Testing with Python

```python
import requests

# Replace with your ngrok URL
BASE_URL = "https://abc123.ngrok-free.app"

# Get dashboard
response = requests.get(f"{BASE_URL}/dashboard")
print(response.json())

# Add a company
new_company = {
    "company_name": "AI Startup",
    "industry": "AI/ML",
    "location": "Palo Alto, CA"
}
response = requests.post(f"{BASE_URL}/companies", json=new_company)
print(response.json())

# Run pipeline
config = {
    "days_back": 30,
    "max_credits": 10,
    "use_cache": True
}
response = requests.post(f"{BASE_URL}/run-pipeline", json=config)
print(response.json())
```

## Frontend Integration

### JavaScript/React Example
```javascript
const API_URL = 'https://your-ngrok-url.ngrok-free.app';

// Get alerts
fetch(`${API_URL}/alerts`)
  .then(res => res.json())
  .then(data => console.log(data));

// Add company
fetch(`${API_URL}/companies`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    company_name: 'New Startup',
    industry: 'SaaS'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## Ngrok Configuration

### Basic Usage
```bash
ngrok http 8000
```

### With Custom Subdomain (paid feature)
```bash
ngrok http 8000 --subdomain=alert-pipeline
```

### With Basic Auth
```bash
ngrok http 8000 --auth="username:password"
```

### Save Ngrok URL
After running ngrok, save the URL:
```bash
# Windows
set NGROK_URL=https://abc123.ngrok-free.app

# Linux/Mac
export NGROK_URL=https://abc123.ngrok-free.app
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Install dependencies
```bash
pip install -r api_requirements.txt
```

### Issue: Pipeline not running
**Solution**: Check virtual environment is activated
```bash
# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Issue: Ngrok connection refused
**Solution**: Make sure API is running on port 8000
```bash
python api.py
```

### Issue: CORS errors
The API already has CORS enabled for all origins. If still facing issues, check browser console for specific errors.

## Security Notes

⚠️ **For Development Only**: This setup is for testing/development. For production:
- Add authentication/authorization
- Use HTTPS certificates
- Implement rate limiting
- Add input validation
- Use environment variables for secrets
- Consider using a proper hosting service

## Features

✅ **Simple Setup** - Single file API, no complex configuration
✅ **Real-time Updates** - Pipeline status updates live
✅ **CORS Enabled** - Works with any frontend
✅ **Auto Documentation** - Swagger UI included
✅ **Background Tasks** - Pipeline runs asynchronously
✅ **JSON Responses** - Easy to parse in any language
✅ **Export Support** - CSV export endpoints
✅ **Error Handling** - Proper HTTP status codes

## API Response Examples

### Dashboard Response
```json
{
  "statistics": {
    "total_companies": 8,
    "total_alerts": 5,
    "level_3_count": 0,
    "level_2_count": 1,
    "level_1_count": 4
  },
  "recent_alerts": [...],
  "pipeline_status": {
    "is_running": false,
    "progress": 100,
    "message": "Pipeline completed successfully"
  }
}
```

### Alert Response
```json
{
  "pdl_id": "abc123",
  "full_name": "John Doe",
  "level": "LEVEL_2",
  "alert_reasons": ["Building signals: consultant"],
  "priority_score": 85.0,
  "departure_info": {
    "company": "openai",
    "days_ago": 45
  }
}
```

## Next Steps

1. **Add Authentication**: Implement API keys or OAuth
2. **Database Integration**: Replace JSON files with PostgreSQL/MongoDB
3. **WebSocket Support**: Real-time pipeline updates
4. **Rate Limiting**: Prevent API abuse
5. **Deployment**: Deploy to cloud (AWS, GCP, Azure)

## Support

For issues with:
- **API**: Check the error messages in console
- **Ngrok**: Visit https://ngrok.com/docs
- **Pipeline**: Ensure all dependencies are installed