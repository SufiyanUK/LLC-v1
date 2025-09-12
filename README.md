# Employee Departure Tracking System

A comprehensive system to track senior AI/ML talent movement from major tech companies with real-time search, reports, and email alerts.

## Target Companies

- OpenAI
- Anthropic  
- Cohere
- Mistral AI
- Meta
- Google DeepMind
- Google
- Microsoft
- Uber
- Airbnb
- Scale AI
- LinkedIn
- Palantir

## Key Features

### 🔍 Real-Time Departure Search
- Search for employees who left any of the 13 target companies
- Filter by time period (30-365 days)
- Focus on AI/ML professionals or all tech roles
- Get instant results with detailed departure information

### 📊 Comprehensive Reports
- **JSON Reports**: Detailed data for integration
- **HTML Reports**: Beautiful visual reports for stakeholders  
- **CSV Exports**: Data exports for further analysis
- **Summary Statistics**: Top destinations, seniority breakdown, AI/ML percentage

### 📧 Automatic Email Alerts
- Configurable email notifications for departures
- High-priority alerts for senior positions
- HTML-formatted emails with departure details
- Test mode for verification

### ⚙️ Flexible Configuration
- Adjustable employees per company (5-100)
- Customizable tracking period
- Toggle between AI/ML focus or all tech roles
- Web-based configuration interface

## Directory Structure

```
employee_tracker/
├── config/
│   └── target_companies.py      # Company list and filtering criteria
├── data/
│   ├── snapshots/               # Employee snapshots by date
│   ├── departures/              # Detected departures
│   └── alerts/                  # Generated alerts
├── scripts/
│   ├── fetch_senior_employees.py   # Initial/refresh employee fetch
│   └── monthly_tracker.py          # Departure detection
├── logs/                        # System logs
└── test_small_batch.py          # Test with minimal credits
```

## Setup

1. Ensure you have a `.env` file in the parent directory with:
```
API_KEY=your_pdl_api_key
```

2. Install dependencies:
```bash
pip install requests python-dotenv
```

## Quick Start

### 1. Start the API Server

```bash
cd employee_tracker
python api.py
```

The API will be available at `http://localhost:8001`

### 2. Open the Web Interface

Open `index.html` in your browser or serve it:
```bash
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

### 3. Use the Web Interface

#### Search for Departures:
1. Select a company from the dropdown (e.g., "OpenAI", "Meta")
2. Set the number of days to look back (default: 90)
3. Click "Search Departures"
4. View results instantly with departure details

#### Configure Tracking:
1. Set employees per company (5-100 credits)
2. Enable/disable email alerts
3. Add alert email address
4. Save configuration

### 4. API Endpoints (Alternative Access)

```bash
# Search for departures
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"company_name": "openai", "days_back": 90}'

# Get latest report
curl http://localhost:8001/report/openai

# Update configuration
curl -X PUT http://localhost:8001/config \
  -H "Content-Type: application/json" \
  -d '{"employees_per_company": 50, "auto_alert": true}'
```

## Alert Format

Alerts include:
- Employee name
- Previous company and role
- New company and role
- LinkedIn URL (if available)
- Alert priority level

## Credit Usage

- **Departure Search**: ~100-300 credits per search (fetches candidates then filters)
- **Initial Employee Fetch**: Configurable 5-100 credits per company
- **Test Mode**: 10 credits total

## Email Configuration (Optional)

To enable email alerts, add to your `.env` file:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

## Filtering Criteria

### Seniority Levels
- Senior, Lead, Principal, Staff
- Director, VP, Head, Chief

### AI/ML Keywords
- Machine Learning, Artificial Intelligence, Deep Learning
- NLP, Computer Vision, LLM, Transformers
- Research Scientist, ML Engineer, AI Product

### Technical Skills
- PyTorch, TensorFlow, JAX
- Transformers, Hugging Face
- MLOps, Model Training/Deployment

## Example Workflow

1. **Month 1**: Run initial fetch
   ```bash
   python scripts/fetch_senior_employees.py
   # Fetches ~400 employees (30 per company × 13 companies)
   ```

2. **Month 2**: Check for departures
   ```bash
   python scripts/monthly_tracker.py
   # Check sample of 50 employees
   # Detect any departures
   # Generate alerts
   ```

3. **Review**: Check `data/alerts/` for high-priority departures

## Tips

- Start with `test_small_batch.py` to verify everything works
- Use sampling in monthly tracker to save credits
- Focus on high-priority alerts from key companies
- Run tracker monthly or quarterly depending on needs

## Customization

Edit `config/target_companies.py` to:
- Add/remove companies
- Modify role filters
- Update AI/ML keywords
- Change seniority levels