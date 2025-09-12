"""
Email alert system for employee departures
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime

class EmailAlertSender:
    """Send email alerts for employee departures"""
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.alert_email = os.getenv('ALERT_EMAIL', 'bailie@venrock.com')
    
    async def send_alert(
        self,
        recipient_email: str,
        company: str,
        departures: List[Dict],
        is_test: bool = False
    ) -> bool:
        """
        Send departure alert email with priority levels
        
        Returns:
            True if sent successfully, False otherwise
        """
        
        if not self.sender_email or not self.sender_password:
            print("[EMAIL] Sender credentials not configured")
            return False
        
        try:
            # Determine priority based on alert levels
            max_level = max((d.get('alert_level', 1) for d in departures), default=1)
            priority_prefix = {
                3: "🚨 HIGH PRIORITY - Startup Departure",
                2: "⚠️ IMPORTANT - Building Signals",
                1: "📢 Departure Alert"
            }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{'[TEST] ' if is_test else ''}{priority_prefix.get(max_level, 'Departure Alert')}: {len(departures)} from {company}"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Set email priority headers for Level 3
            if max_level == 3:
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'
            
            # Create HTML email body
            html_body = self._create_html_email(company, departures, is_test)
            
            # Attach HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"[EMAIL] Alert sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] Failed to send: {str(e)}")
            return False
    
    def _create_html_email(self, company: str, departures: List[Dict], is_test: bool) -> str:
        """Create HTML email content"""
        
        # Count AI/ML departures
        ai_ml_count = sum(1 for d in departures if d.get('is_ai_ml'))
        
        # Group by seniority
        senior_departures = [d for d in departures if d.get('seniority_level') in ['C-Level', 'VP/Head', 'Director']]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        h1 {{ margin: 0; font-size: 28px; }}
        .alert-badge {{ background: #ff6b6b; color: white; padding: 5px 10px; border-radius: 5px; display: inline-block; margin-top: 10px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .stat {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; flex: 1; margin: 0 10px; }}
        .stat-number {{ font-size: 36px; font-weight: bold; color: #5e72e4; }}
        .stat-label {{ color: #8898aa; margin-top: 5px; }}
        .departure-list {{ margin: 30px 0; }}
        .departure-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #5e72e4; }}
        .name {{ font-weight: bold; color: #32325d; font-size: 16px; }}
        .details {{ color: #525f7f; margin: 5px 0; }}
        .ai-ml-badge {{ background: #00d4ff; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; display: inline-block; }}
        .senior-badge {{ background: #ff9500; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; display: inline-block; }}
        .footer {{ text-align: center; color: #8898aa; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e6ecf1; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{'🔔 TEST ALERT' if is_test else '🚨 Departure Alert'}</h1>
            <div class="alert-badge">{len(departures)} employees left {company}</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(departures)}</div>
                <div class="stat-label">Total Departures</div>
            </div>
            <div class="stat">
                <div class="stat-number">{ai_ml_count}</div>
                <div class="stat-label">AI/ML Professionals</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(senior_departures)}</div>
                <div class="stat-label">Senior Positions</div>
            </div>
        </div>
        
        <div class="departure-list">
            <h2>Recent Departures</h2>
"""
        
        # Sort by alert level (highest first)
        sorted_deps = sorted(departures[:10], key=lambda x: x.get('alert_level', 1), reverse=True)
        
        # Add top departures
        for dep in sorted_deps:
            badges = []
            alert_level = dep.get('alert_level', 1)
            
            # Alert level badge
            if alert_level == 3:
                badges.append('<span style="background: #ff4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">🔴 STARTUP</span>')
            elif alert_level == 2:
                badges.append('<span style="background: #ff9500; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">🟠 BUILDING</span>')
            
            # Additional badges
            if dep.get('is_ai_ml'):
                badges.append('<span class="ai-ml-badge">AI/ML</span>')
            if dep.get('seniority_level') in ['C-Level', 'VP/Head', 'Director']:
                badges.append(f'<span class="senior-badge">{dep.get("seniority_level")}</span>')
            
            # Signals
            signals_html = ''
            if dep.get('alert_signals') and len(dep.get('alert_signals', [])) > 0:
                signals_html = f'<br><strong>Signals:</strong> {", ".join(dep["alert_signals"][:2])}'
            
            html += f"""
            <div class="departure-item" style="border-left-color: {'#ff4444' if alert_level == 3 else '#ff9500' if alert_level == 2 else '#5e72e4'};">
                <div class="name">{dep.get('name', 'Unknown')} {' '.join(badges)}</div>
                <div class="details">
                    <strong>From:</strong> {dep.get('old_title', 'Unknown')} at {dep.get('old_company', company)}<br>
                    <strong>To:</strong> {dep.get('new_title', 'Unknown')} at {dep.get('new_company', 'Unknown')}<br>
                    {f'<strong>Headline:</strong> <em>{dep.get("headline", "")}</em><br>' if dep.get('headline') else ''}
                    {signals_html}
                </div>
            </div>
"""
        
        if len(departures) > 10:
            html += f"""
            <div style="text-align: center; margin: 20px 0; color: #8898aa;">
                ... and {len(departures) - 10} more departures
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <p>Generated by Employee Departure Tracker</p>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html