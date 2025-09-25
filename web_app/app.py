"""
Flask Web Application for Alert Pipeline
Provides web interface for running pipeline and managing companies
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add parent directory to path to import existing modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
CORS(app)

# Configuration
QUALIFIED_STARTUPS_FILE = os.path.join(parent_dir, 'data', 'processed', 'qualified_startups.json')
ALERTS_DIR = os.path.join(parent_dir, 'data', 'alerts')
CACHE_DIR = os.path.join(parent_dir, 'data', 'raw', 'updated_test')
PIPELINE_SCRIPT = os.path.join(parent_dir, 'run_alert_pipeline.py')

# Pipeline status tracking
pipeline_status = {
    'is_running': False,
    'progress': 0,
    'message': 'Ready',
    'last_run': None,
    'last_results': None
}

@app.route('/')
def dashboard():
    """Main dashboard showing statistics and recent alerts"""
    stats = get_dashboard_stats()
    recent_alerts = get_recent_alerts(limit=5)
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_alerts=recent_alerts,
                         pipeline_status=pipeline_status)

@app.route('/alerts')
def alerts_view():
    """View all alerts with filtering and sorting"""
    # Get latest alerts file
    alerts_files = sorted(Path(ALERTS_DIR).glob('alerts_full_*.json'), reverse=True)
    alerts = []
    
    if alerts_files:
        with open(alerts_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Combine all alert levels
            for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
                for alert in data.get(level, []):
                    if alert:
                        alert['level'] = level
                        alerts.append(alert)
    
    return render_template('alerts.html', alerts=alerts)

@app.route('/companies')
def companies_view():
    """Manage qualified startups"""
    companies = load_qualified_startups()
    return render_template('companies.html', companies=companies)

@app.route('/api/companies', methods=['GET', 'POST'])
def api_companies():
    """API endpoint for company management"""
    if request.method == 'GET':
        companies = load_qualified_startups()
        return jsonify(companies)
    
    elif request.method == 'POST':
        data = request.json
        companies = load_qualified_startups()
        
        # Add new company
        new_company = {
            'company_name': data.get('company_name'),
            'founded_date': data.get('founded_date'),
            'industry': data.get('industry', 'Technology'),
            'location': data.get('location', ''),
            'description': data.get('description', ''),
            'added_date': datetime.now().isoformat()
        }
        
        companies.append(new_company)
        save_qualified_startups(companies)
        
        return jsonify({'success': True, 'company': new_company})

@app.route('/api/companies/<int:index>', methods=['DELETE'])
def delete_company(index):
    """Delete a company by index"""
    companies = load_qualified_startups()
    
    if 0 <= index < len(companies):
        deleted = companies.pop(index)
        save_qualified_startups(companies)
        return jsonify({'success': True, 'deleted': deleted})
    
    return jsonify({'success': False, 'error': 'Invalid index'}), 400

@app.route('/api/run-pipeline', methods=['POST'])
def run_pipeline():
    """Run the alert pipeline"""
    global pipeline_status
    
    if pipeline_status['is_running']:
        return jsonify({'success': False, 'error': 'Pipeline is already running'}), 400
    
    data = request.json
    days_back = data.get('days_back', 90)
    max_credits = data.get('max_credits', 20)
    use_cache = data.get('use_cache', True)
    
    # Run pipeline in background thread
    thread = threading.Thread(target=run_pipeline_background, 
                            args=(days_back, max_credits, use_cache))
    thread.start()
    
    return jsonify({'success': True, 'message': 'Pipeline started'})

@app.route('/api/pipeline-status')
def get_pipeline_status():
    """Get current pipeline status"""
    return jsonify(pipeline_status)

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    return jsonify(get_dashboard_stats())

@app.route('/api/alerts/recent')
def get_recent_alerts_api():
    """Get recent high-priority alerts"""
    limit = request.args.get('limit', 10, type=int)
    alerts = get_recent_alerts(limit)
    return jsonify(alerts)

@app.route('/api/companies/import', methods=['POST'])
def import_companies():
    """Import companies from CSV file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.csv'):
        import csv
        import io
        
        companies = load_qualified_startups()
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        new_companies = 0
        for row in csv_reader:
            company = {
                'company_name': row.get('company_name', row.get('name', '')),
                'founded_date': row.get('founded_date', ''),
                'industry': row.get('industry', 'Technology'),
                'location': row.get('location', ''),
                'description': row.get('description', ''),
                'added_date': datetime.now().isoformat()
            }
            if company['company_name']:
                companies.append(company)
                new_companies += 1
        
        save_qualified_startups(companies)
        return jsonify({'success': True, 'imported': new_companies})
    
    return jsonify({'success': False, 'error': 'Invalid file format'}), 400

def run_pipeline_background(days_back, max_credits, use_cache):
    """Run the pipeline in background"""
    global pipeline_status
    
    pipeline_status['is_running'] = True
    pipeline_status['progress'] = 10
    pipeline_status['message'] = 'Starting pipeline...'
    
    try:
        # Prepare environment with virtual environment
        env = os.environ.copy()
        venv_python = os.path.join(parent_dir, '.venv', 'Scripts', 'python.exe')
        
        # Use venv Python if it exists, otherwise system Python
        python_exe = venv_python if os.path.exists(venv_python) else 'python'
        
        # Modify the pipeline script to accept parameters
        cmd = [
            python_exe,
            PIPELINE_SCRIPT
        ]
        
        pipeline_status['progress'] = 30
        pipeline_status['message'] = 'Fetching employee data...'
        
        # Run the pipeline
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              cwd=parent_dir,
                              env=env)
        
        pipeline_status['progress'] = 80
        pipeline_status['message'] = 'Processing alerts...'
        
        if result.returncode == 0:
            pipeline_status['progress'] = 100
            pipeline_status['message'] = 'Pipeline completed successfully'
            pipeline_status['last_run'] = datetime.now().isoformat()
            
            # Load latest results
            alerts_files = sorted(Path(ALERTS_DIR).glob('alerts_full_*.json'), reverse=True)
            if alerts_files:
                with open(alerts_files[0], 'r', encoding='utf-8') as f:
                    pipeline_status['last_results'] = json.load(f).get('stats', {})
        else:
            pipeline_status['message'] = f'Pipeline failed: {result.stderr[:200]}'
            pipeline_status['progress'] = 0
    
    except Exception as e:
        pipeline_status['message'] = f'Error: {str(e)}'
        pipeline_status['progress'] = 0
    
    finally:
        pipeline_status['is_running'] = False

def load_qualified_startups():
    """Load qualified startups from JSON file"""
    try:
        with open(QUALIFIED_STARTUPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_qualified_startups(companies):
    """Save qualified startups to JSON file"""
    with open(QUALIFIED_STARTUPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2)

def get_dashboard_stats():
    """Get statistics for dashboard"""
    stats = {
        'total_companies': len(load_qualified_startups()),
        'total_alerts': 0,
        'level_3_alerts': 0,
        'level_2_alerts': 0,
        'level_1_alerts': 0,
        'last_run': None
    }
    
    # Get latest alerts file
    alerts_files = sorted(Path(ALERTS_DIR).glob('alerts_full_*.json'), reverse=True)
    if alerts_files:
        with open(alerts_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            alert_stats = data.get('stats', {})
            stats['total_alerts'] = alert_stats.get('level_1_count', 0) + \
                                   alert_stats.get('level_2_count', 0) + \
                                   alert_stats.get('level_3_count', 0)
            stats['level_3_alerts'] = alert_stats.get('level_3_count', 0)
            stats['level_2_alerts'] = alert_stats.get('level_2_count', 0)
            stats['level_1_alerts'] = alert_stats.get('level_1_count', 0)
            stats['last_run'] = data.get('timestamp', '')
    
    return stats

def get_recent_alerts(limit=5):
    """Get recent high-priority alerts"""
    alerts = []
    
    # Get latest alerts file
    alerts_files = sorted(Path(ALERTS_DIR).glob('alerts_high_priority_*.json'), reverse=True)
    if alerts_files:
        with open(alerts_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Get Level 3 and Level 2 alerts
            for alert in data.get('LEVEL_3', [])[:limit]:
                if alert:
                    alert['level'] = 'LEVEL_3'
                    alerts.append(alert)
            
            remaining = limit - len(alerts)
            for alert in data.get('LEVEL_2', [])[:remaining]:
                if alert:
                    alert['level'] = 'LEVEL_2'
                    alerts.append(alert)
    
    return alerts

if __name__ == '__main__':
    os.makedirs(ALERTS_DIR, exist_ok=True)
    os.makedirs(os.path.join('web_app', 'data'), exist_ok=True)
    app.run(debug=True, port=5000)