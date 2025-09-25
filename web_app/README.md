# Alert Pipeline Web Application

A Flask-based web interface for the Alert Pipeline system that tracks potential founders leaving tech companies.

## Features

- **Dashboard**: Real-time statistics and high-priority alerts
- **Alert Management**: View, filter, and export all generated alerts
- **Company Management**: Add, edit, delete, and import qualified startups
- **Pipeline Control**: Run the alert pipeline with custom parameters
- **CSV Import/Export**: Bulk manage companies via CSV files

## Local Development

### Setup

1. Navigate to the web_app directory:
```bash
cd web_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
python app.py
```

5. Open your browser to `http://localhost:5000`

## Deployment to Railway

### Prerequisites

1. Railway account (https://railway.app)
2. GitHub repository with your code
3. PeopleDataLabs API key

### Deployment Steps

1. **Push to GitHub**:
```bash
git add .
git commit -m "Add web application"
git push origin main
```

2. **Create Railway Project**:
   - Log in to Railway
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Select your repository

3. **Configure Environment Variables**:
   In Railway dashboard, add these variables:
   - `SECRET_KEY`: Generate a secure random key
   - `API_KEY`: Your PeopleDataLabs API key
   - `PORT`: Railway will set this automatically

4. **Deploy**:
   - Railway will automatically deploy from your main branch
   - Monitor deployment logs in Railway dashboard
   - Your app will be available at: `https://your-app.railway.app`

### Important Notes for Railway

- **Data Persistence**: Railway's filesystem is ephemeral. You'll need to:
  - Use Railway's PostgreSQL addon for persistent storage
  - Or integrate with external storage (AWS S3, Google Cloud Storage)
  
- **File Structure**: The app expects the parent directory structure. Ensure:
  - Deploy from the root directory (not web_app)
  - Or adjust paths in `app.py` accordingly

- **Background Tasks**: For production, consider using:
  - Redis + Celery for background job processing
  - Railway's Redis addon for task queue

## API Endpoints

- `GET /` - Dashboard
- `GET /alerts` - View all alerts
- `GET /companies` - Manage companies
- `POST /api/companies` - Add new company
- `DELETE /api/companies/<id>` - Delete company
- `POST /api/companies/import` - Import CSV
- `POST /api/run-pipeline` - Start pipeline
- `GET /api/pipeline-status` - Check pipeline status
- `GET /api/stats` - Get dashboard statistics

## Usage

### Adding Companies

1. Click "Companies" in navigation
2. Click "Add Company" button
3. Fill in company details:
   - Company Name (required)
   - Founded Date
   - Industry
   - Location
   - Description
4. Click "Save Company"

### Importing Companies via CSV

1. Prepare CSV with columns: `company_name`, `founded_date`, `industry`, `location`, `description`
2. Click "Import CSV" in Companies page
3. Select your CSV file
4. Click "Import"

### Running the Pipeline

1. Click "Run Pipeline" button (green button in nav)
2. Configure parameters:
   - Days Back: How far to search for departures
   - Max Credits: API credit limit
   - Use Cache: Use cached data if available
3. Click "Start Pipeline"
4. Monitor progress in real-time

### Viewing Alerts

1. Click "Alerts" in navigation
2. Use DataTable features:
   - Search by name, company
   - Sort by priority, level, date
   - Filter by alert level
3. Click eye icon to view full details
4. Click "Export CSV" for spreadsheet

## Troubleshooting

### Pipeline Not Running
- Check virtual environment is activated
- Verify API key in .env file
- Check `run_alert_pipeline.py` exists in parent directory

### No Alerts Showing
- Run the pipeline first
- Check `data/alerts/` directory for JSON files
- Verify qualified startups are loaded

### Import Errors
- Ensure CSV has correct column names
- Check file encoding (UTF-8 required)
- Verify company_name column is not empty

## Development

### File Structure
```
web_app/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Procfile           # Railway deployment config
├── railway.json       # Railway configuration
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── dashboard.html # Dashboard page
│   ├── alerts.html   # Alerts page
│   └── companies.html # Companies page
├── static/           # Static assets
│   ├── css/
│   │   └── style.css # Custom styles
│   └── js/
│       └── main.js   # JavaScript functionality
└── data/            # Local data directory
```

### Adding New Features

1. Add route in `app.py`
2. Create template in `templates/`
3. Add JavaScript in `static/js/main.js`
4. Update navigation in `base.html`

## License

Proprietary - All rights reserved