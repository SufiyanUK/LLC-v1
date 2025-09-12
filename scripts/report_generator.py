"""
Generate detailed reports for employee departures
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class ReportGenerator:
    """Generate departure reports in various formats"""
    
    def __init__(self):
        self.reports_dir = Path(__file__).parent.parent / 'data' / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_departure_report(
        self,
        company_name: str,
        departures: List[Dict],
        days_back: int
    ) -> Optional[Path]:
        """
        Generate a comprehensive departure report
        
        Returns:
            Path to the generated report file
        """
        
        if not departures:
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create report structure
        report = {
            'company': company_name,
            'report_date': datetime.now().isoformat(),
            'days_tracked': days_back,
            'total_departures': len(departures),
            'summary': self._generate_summary(departures),
            'by_seniority': self._group_by_seniority(departures),
            'by_destination': self._group_by_destination(departures),
            'ai_ml_departures': [d for d in departures if d.get('is_ai_ml')],
            'recent_departures': departures[:10],  # Top 10 most recent
            'all_departures': departures
        }
        
        # Save JSON report
        json_file = self.reports_dir / f"{company_name.lower()}_departures_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html_file = self._generate_html_report(report, timestamp)
        
        # Generate CSV export
        csv_file = self._generate_csv_export(departures, company_name, timestamp)
        
        print(f"\n[REPORTS GENERATED]")
        print(f"  JSON: {json_file.name}")
        print(f"  HTML: {html_file.name}")
        print(f"  CSV: {csv_file.name}")
        
        return json_file
    
    def _generate_summary(self, departures: List[Dict]) -> Dict:
        """Generate summary statistics"""
        
        total = len(departures)
        ai_ml_count = sum(1 for d in departures if d.get('is_ai_ml'))
        
        # Top destination companies
        destinations = {}
        for dep in departures:
            dest = dep.get('new_company', 'Unknown')
            destinations[dest] = destinations.get(dest, 0) + 1
        
        top_destinations = sorted(destinations.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Average days since departure
        days_list = [d.get('days_since_departure', 0) for d in departures]
        avg_days = sum(days_list) / len(days_list) if days_list else 0
        
        return {
            'total_departures': total,
            'ai_ml_departures': ai_ml_count,
            'ai_ml_percentage': round(ai_ml_count / total * 100, 1) if total > 0 else 0,
            'top_destinations': dict(top_destinations),
            'average_days_since_departure': round(avg_days, 1),
            'most_recent_departure': min(days_list) if days_list else None,
            'oldest_departure': max(days_list) if days_list else None
        }
    
    def _group_by_seniority(self, departures: List[Dict]) -> Dict:
        """Group departures by seniority level"""
        
        by_seniority = {}
        for dep in departures:
            level = dep.get('seniority_level', 'Other')
            if level not in by_seniority:
                by_seniority[level] = []
            by_seniority[level].append({
                'name': dep.get('name'),
                'new_company': dep.get('new_company'),
                'days_ago': dep.get('days_since_departure')
            })
        
        return by_seniority
    
    def _group_by_destination(self, departures: List[Dict]) -> Dict:
        """Group departures by destination company"""
        
        by_destination = {}
        for dep in departures:
            dest = dep.get('new_company', 'Unknown')
            if dest not in by_destination:
                by_destination[dest] = []
            by_destination[dest].append({
                'name': dep.get('name'),
                'old_title': dep.get('old_title'),
                'new_title': dep.get('new_title'),
                'days_ago': dep.get('days_since_departure')
            })
        
        # Sort by company with most hires
        by_destination = dict(sorted(by_destination.items(), 
                                   key=lambda x: len(x[1]), 
                                   reverse=True))
        
        return by_destination
    
    def _generate_html_report(self, report: Dict, timestamp: str) -> Path:
        """Generate HTML version of the report"""
        
        company = report['company']
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{company} Departure Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ background: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1; margin: 0 10px; }}
        .stat-number {{ font-size: 2em; color: #3498db; font-weight: bold; }}
        table {{ width: 100%; background: white; border-collapse: collapse; }}
        th {{ background: #34495e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .ai-badge {{ background: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }}
        .seniority-badge {{ background: #9b59b6; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{company} Departure Report</h1>
        <p>Generated: {report['report_date']}</p>
        <p>Tracking Period: Last {report['days_tracked']} days</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{report['total_departures']}</div>
            <div>Total Departures</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{report['summary']['ai_ml_departures']}</div>
            <div>AI/ML Professionals</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{report['summary']['ai_ml_percentage']}%</div>
            <div>AI/ML Percentage</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{report['summary']['average_days_since_departure']:.0f}</div>
            <div>Avg Days Since Departure</div>
        </div>
    </div>
    
    <div class="summary">
        <h2>Recent Departures</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Previous Role</th>
                <th>New Company</th>
                <th>New Role</th>
                <th>Days Ago</th>
                <th>Tags</th>
            </tr>
"""
        
        # Add recent departures to table
        for dep in report['recent_departures'][:20]:
            tags = []
            if dep.get('is_ai_ml'):
                tags.append('<span class="ai-badge">AI/ML</span>')
            if dep.get('seniority_level') in ['C-Level', 'VP/Head', 'Director']:
                tags.append(f'<span class="seniority-badge">{dep.get("seniority_level")}</span>')
            
            html_content += f"""
            <tr>
                <td><strong>{dep.get('name', 'Unknown')}</strong></td>
                <td>{dep.get('old_title', 'Unknown')}</td>
                <td>{dep.get('new_company', 'Unknown')}</td>
                <td>{dep.get('new_title', 'Unknown')}</td>
                <td>{dep.get('days_since_departure', 'Unknown')}</td>
                <td>{' '.join(tags)}</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
    
    <div class="summary">
        <h2>Top Destination Companies</h2>
        <table>
            <tr>
                <th>Company</th>
                <th>Employees Joined</th>
            </tr>
"""
        
        # Add top destinations
        for company, count in report['summary']['top_destinations'].items():
            html_content += f"""
            <tr>
                <td>{company}</td>
                <td>{count}</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
</body>
</html>
"""
        
        html_file = self.reports_dir / f"{company.lower()}_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def _generate_csv_export(self, departures: List[Dict], company_name: str, timestamp: str) -> Path:
        """Generate CSV export of departures"""
        
        import csv
        
        csv_file = self.reports_dir / f"{company_name.lower()}_export_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if departures:
                fieldnames = [
                    'name', 'old_company', 'old_title', 'new_company', 'new_title',
                    'departure_date', 'days_since_departure', 'seniority_level',
                    'is_ai_ml', 'location', 'linkedin_url'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for dep in departures:
                    writer.writerow({
                        'name': dep.get('name', ''),
                        'old_company': dep.get('old_company', ''),
                        'old_title': dep.get('old_title', ''),
                        'new_company': dep.get('new_company', ''),
                        'new_title': dep.get('new_title', ''),
                        'departure_date': dep.get('departure_date', ''),
                        'days_since_departure': dep.get('days_since_departure', ''),
                        'seniority_level': dep.get('seniority_level', ''),
                        'is_ai_ml': 'Yes' if dep.get('is_ai_ml') else 'No',
                        'location': dep.get('location', ''),
                        'linkedin_url': dep.get('linkedin_url', '')
                    })
        
        return csv_file