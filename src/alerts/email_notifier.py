"""
Email Notification System for High Priority Alerts
Sends email notifications for Level 2 and Level 3 alerts
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """
    Handles email notifications for alert system
    """
    
    def __init__(self, sender_email: str = None, sender_password: str = None, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        """
        Initialize email notifier
        
        Args:
            sender_email: Gmail address to send from
            sender_password: Gmail app password (not regular password!)
            smtp_server: SMTP server address
            smtp_port: SMTP port
        """
        # Get from environment variables if not provided
        self.sender_email = sender_email or os.getenv('GMAIL_SENDER_EMAIL')
        self.sender_password = sender_password or os.getenv('GMAIL_APP_PASSWORD')
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured. Please set GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD in .env file")
    
    def create_alert_html(self, alerts: Dict[str, List], level_filter: List[str] = ['LEVEL_2', 'LEVEL_3']) -> str:
        """
        Create HTML content for alert email
        
        Args:
            alerts: Dictionary containing alert levels and data
            level_filter: Which levels to include in email
            
        Returns:
            HTML string for email body
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 25px; }
                .alert-summary { 
                    background: #ecf0f1; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }
                .level-3 { 
                    background: #ff6b6b; 
                    color: white; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 10px 0;
                }
                .level-2 { 
                    background: #ffa500; 
                    color: white; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 10px 0;
                }
                .employee-card {
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 10px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .highlight { 
                    background: #fff3cd; 
                    padding: 2px 5px; 
                    border-radius: 3px;
                }
                .score-badge {
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    margin: 0 5px;
                    font-weight: bold;
                }
                .high-score { background: #d4edda; color: #155724; }
                .medium-score { background: #fff3cd; color: #856404; }
                .building-signal {
                    display: inline-block;
                    background: #e3f2fd;
                    color: #1565c0;
                    padding: 3px 8px;
                    border-radius: 3px;
                    margin: 2px;
                    font-size: 0.9em;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                th, td {
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background: #3498db;
                    color: white;
                }
                .urgent { color: #e74c3c; font-weight: bold; }
                .footer {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #7f8c8d;
                }
            </style>
        </head>
        <body>
        """
        
        # Header
        html += f"""
        <h1>🚨 AI Talent Alert System - High Priority Notifications</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # Summary statistics
        level_3_count = len(alerts.get('LEVEL_3', []))
        level_2_count = len(alerts.get('LEVEL_2', []))
        
        html += f"""
        <div class="alert-summary">
            <h2>📊 Alert Summary</h2>
            <table>
                <tr>
                    <th>Alert Level</th>
                    <th>Count</th>
                    <th>Action Required</th>
                </tr>
                <tr>
                    <td><span class="urgent">LEVEL 3 - Immediate Action</span></td>
                    <td><strong>{level_3_count}</strong></td>
                    <td>Contact within 24 hours</td>
                </tr>
                <tr>
                    <td>LEVEL 2 - High Priority</td>
                    <td><strong>{level_2_count}</strong></td>
                    <td>Contact within 48-72 hours</td>
                </tr>
            </table>
        </div>
        """
        
        # Level 3 Alerts - IMMEDIATE ACTION
        if 'LEVEL_3' in level_filter and level_3_count > 0:
            html += """
            <div class="level-3">
                <h2>🔴 LEVEL 3 - IMMEDIATE ACTION REQUIRED</h2>
                <p><strong>These individuals show the strongest founder signals and should be contacted immediately.</strong></p>
            </div>
            """
            
            for alert in alerts.get('LEVEL_3', [])[:10]:  # Top 10 Level 3 alerts
                if alert:
                    html += self._create_employee_card(alert, 'LEVEL_3')
        
        # Level 2 Alerts - HIGH PRIORITY
        if 'LEVEL_2' in level_filter and level_2_count > 0:
            html += """
            <div class="level-2">
                <h2>🟠 LEVEL 2 - HIGH PRIORITY</h2>
                <p><strong>Strong founder indicators. Schedule outreach within 48-72 hours.</strong></p>
            </div>
            """
            
            for alert in alerts.get('LEVEL_2', [])[:15]:  # Top 15 Level 2 alerts
                if alert:
                    html += self._create_employee_card(alert, 'LEVEL_2')
        
        # Footer
        html += """
        <div class="footer">
            <p><strong>Alert System Information:</strong></p>
            <ul>
                <li>This is an automated alert from the AI Talent Detection System</li>
                <li>Scores are based on: departure timing, role seniority, stealth indicators, and founder patterns</li>
                <li>For full details, check the dashboard or CSV export</li>
            </ul>
            <p><em>Generated by Alert Pipeline v3 - LLC Talent Detection System</em></p>
        </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_employee_card(self, alert: Dict, level: str) -> str:
        """Create HTML card for individual employee alert"""
        
        name = alert.get('full_name', 'Unknown')
        departure_info = alert.get('departure_info', {})
        departure_company = departure_info.get('company', 'Unknown') if departure_info else 'Unknown'
        days_ago = departure_info.get('days_ago', 'Unknown') if departure_info else 'Unknown'
        
        current_company = alert.get('job_company_name', 'Not specified')
        current_title = alert.get('job_title', 'Not specified')
        
        founder_score = alert.get('founder_score', 0)
        stealth_score = alert.get('stealth_score', 0)
        priority_score = alert.get('priority_score', 0)
        
        building_phrases = alert.get('building_phrases', [])
        linkedin_url = alert.get('linkedin_url', '')
        
        # Score badges
        founder_badge = "high-score" if founder_score >= 7 else "medium-score"
        stealth_badge = "high-score" if stealth_score >= 70 else "medium-score"
        
        card = f"""
        <div class="employee-card">
            <h3>{name}</h3>
            <table>
                <tr>
                    <td><strong>Previous:</strong></td>
                    <td>{departure_company} (left {days_ago} days ago)</td>
                </tr>
                <tr>
                    <td><strong>Current:</strong></td>
                    <td>{current_title} @ {current_company}</td>
                </tr>
                <tr>
                    <td><strong>Scores:</strong></td>
                    <td>
                        <span class="score-badge {founder_badge}">Founder: {founder_score:.1f}/10</span>
                        <span class="score-badge {stealth_badge}">Stealth: {stealth_score}/100</span>
                        <span class="score-badge high-score">Priority: {priority_score:.1f}</span>
                    </td>
                </tr>
        """
        
        if building_phrases:
            card += f"""
                <tr>
                    <td><strong>Signals:</strong></td>
                    <td>
                        {''.join([f'<span class="building-signal">{phrase}</span>' for phrase in building_phrases[:5]])}
                    </td>
                </tr>
            """
        
        if linkedin_url:
            card += f"""
                <tr>
                    <td><strong>LinkedIn:</strong></td>
                    <td><a href="{linkedin_url}">View Profile</a></td>
                </tr>
            """
        
        card += """
            </table>
        </div>
        """
        
        return card
    
    def send_alert_email(
        self, 
        recipient_email: str,
        alerts: Dict,
        subject: str = None,
        attach_csv: bool = True,
        csv_filepath: str = None
    ) -> bool:
        """
        Send alert email with Level 2 and Level 3 alerts
        
        Args:
            recipient_email: Email address to send alerts to
            alerts: Dictionary containing alert data
            subject: Email subject (optional)
            attach_csv: Whether to attach CSV file
            csv_filepath: Path to CSV file to attach
            
        Returns:
            True if email sent successfully, False otherwise
        """
        
        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            
            # Set subject with alert counts
            level_3_count = len(alerts.get('LEVEL_3', []))
            level_2_count = len(alerts.get('LEVEL_2', []))
            
            if not subject:
                subject = f"🚨 URGENT: {level_3_count} Immediate + {level_2_count} High Priority Founder Alerts"
            
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Create HTML content
            html_content = self.create_alert_html(alerts)
            
            # Create plain text fallback
            text_content = self._create_plain_text_summary(alerts)
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Attach CSV if requested
            if attach_csv and csv_filepath and os.path.exists(csv_filepath):
                self._attach_file(msg, csv_filepath)
            
            # Send email
            logger.info(f"Sending alert email to {recipient_email}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _create_plain_text_summary(self, alerts: Dict) -> str:
        """Create plain text summary for email fallback"""
        
        text = f"""
AI TALENT ALERT SYSTEM - HIGH PRIORITY NOTIFICATIONS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ALERT SUMMARY:
- LEVEL 3 (Immediate Action): {len(alerts.get('LEVEL_3', []))} alerts
- LEVEL 2 (High Priority): {len(alerts.get('LEVEL_2', []))} alerts

LEVEL 3 - IMMEDIATE ACTION REQUIRED:
"""
        
        for i, alert in enumerate(alerts.get('LEVEL_3', [])[:10], 1):
            if alert:
                text += f"""
{i}. {alert.get('full_name', 'Unknown')}
   Previous: {alert.get('departure_info', {}).get('company', 'Unknown') if alert.get('departure_info') else 'Unknown'}
   Current: {alert.get('job_company_name', 'Not specified')}
   Founder Score: {alert.get('founder_score', 0):.1f}/10
   Priority: {alert.get('priority_score', 0):.1f}
"""
        
        text += "\n\nLEVEL 2 - HIGH PRIORITY:\n"
        
        for i, alert in enumerate(alerts.get('LEVEL_2', [])[:10], 1):
            if alert:
                text += f"""
{i}. {alert.get('full_name', 'Unknown')}
   Previous: {alert.get('departure_info', {}).get('company', 'Unknown') if alert.get('departure_info') else 'Unknown'}
   Current: {alert.get('job_company_name', 'Not specified')}
   Founder Score: {alert.get('founder_score', 0):.1f}/10
"""
        
        return text
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        """Attach a file to the email"""
        try:
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(filepath)}'
                )
                msg.attach(part)
                logger.info(f"Attached file: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Failed to attach file {filepath}: {e}")


def send_high_priority_alerts(
    alerts_file_path: str,
    recipient_email: str,
    sender_email: str = None,
    sender_password: str = None
) -> bool:
    """
    Convenience function to send alerts from a file
    
    Args:
        alerts_file_path: Path to JSON file containing alerts
        recipient_email: Email to send alerts to
        sender_email: Gmail sender (optional, uses env var)
        sender_password: Gmail app password (optional, uses env var)
        
    Returns:
        True if sent successfully
    """
    
    try:
        # Load alerts from file
        with open(alerts_file_path, 'r', encoding='utf-8') as f:
            alerts_data = json.load(f)
        
        # Initialize notifier
        notifier = EmailNotifier(sender_email, sender_password)
        
        # Find corresponding CSV file
        csv_path = alerts_file_path.replace('_full_', '_summary_').replace('.json', '.csv')
        if not os.path.exists(csv_path):
            csv_path = None
        
        # Send email
        return notifier.send_alert_email(
            recipient_email=recipient_email,
            alerts=alerts_data,
            attach_csv=True,
            csv_filepath=csv_path
        )
        
    except Exception as e:
        logger.error(f"Failed to send alerts: {e}")
        return False


if __name__ == "__main__":
    # Test the email notifier
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("Email Notifier Test")
    print("="*50)
    
    if len(sys.argv) > 1:
        alerts_file = sys.argv[1]
        recipient = sys.argv[2] if len(sys.argv) > 2 else input("Enter recipient email: ")
        
        success = send_high_priority_alerts(alerts_file, recipient)
        if success:
            print(f"✅ Alert email sent to {recipient}")
        else:
            print(f"❌ Failed to send email")
    else:
        print("Usage: python email_notifier.py <alerts_json_file> <recipient_email>")
        print("\nTo configure Gmail:")
        print("1. Enable 2-factor authentication on your Gmail")
        print("2. Generate an app password: https://myaccount.google.com/apppasswords")
        print("3. Add to .env file:")
        print("   GMAIL_SENDER_EMAIL=your-email@gmail.com")
        print("   GMAIL_APP_PASSWORD=your-app-password")