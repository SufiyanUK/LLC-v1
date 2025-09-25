"""
Alert System for Employment Changes
Sends notifications via email, Slack, or webhooks
"""

import json
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSystem:
    """
    Manages alerts for employment changes and stealth signals
    """
    
    def __init__(self):
        load_dotenv()
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_from = os.getenv('ALERT_EMAIL_FROM')
        self.email_password = os.getenv('ALERT_EMAIL_PASSWORD')
        self.email_to = os.getenv('ALERT_EMAIL_TO', '').split(',')
        
        # Webhook configuration (Slack, Discord, etc.)
        self.webhook_url = os.getenv('WEBHOOK_URL')
        
        # Alert priorities and templates
        self.alert_templates = {
            'departure': {
                'priority': 'high',
                'emoji': '🚪',
                'subject': 'Employee Departure Alert',
                'template': '{name} left {company} without listing new role'
            },
            'stealth_company': {
                'priority': 'high',
                'emoji': '🚀',
                'subject': 'Stealth Startup Signal',
                'template': '{name} joined "{company}" - potential stealth startup'
            },
            'job_title_change': {
                'priority': 'medium',
                'emoji': '📝',
                'subject': 'Job Title Change',
                'template': '{name} changed title from "{old}" to "{new}"'
            },
            'building_something': {
                'priority': 'high',
                'emoji': '🔨',
                'subject': 'Building Something Signal',
                'template': '{name} profile shows: "{description}"'
            },
            'company_change': {
                'priority': 'low',
                'emoji': '🏢',
                'subject': 'Company Change',
                'template': '{name} moved from {old} to {new}'
            }
        }
    
    def send_email_alert(self, alert_type: str, data: Dict) -> bool:
        """Send email alert"""
        
        if not self.email_from or not self.email_to:
            logger.warning("Email not configured")
            return False
        
        template = self.alert_templates.get(alert_type, {})
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{template.get('emoji', '')} {template.get('subject', 'Alert')}"
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            
            # Create HTML content
            html_content = self._create_html_alert(alert_type, data, template)
            
            # Attach HTML
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_webhook_alert(self, alert_type: str, data: Dict) -> bool:
        """Send webhook alert (Slack/Discord format)"""
        
        if not self.webhook_url:
            logger.warning("Webhook not configured")
            return False
        
        template = self.alert_templates.get(alert_type, {})
        
        try:
            # Create webhook payload (Slack format)
            payload = {
                'text': f"{template.get('emoji', '')} *{template.get('subject', 'Alert')}*",
                'attachments': [{
                    'color': self._get_color_for_priority(template.get('priority', 'low')),
                    'fields': [
                        {'title': 'Person', 'value': data.get('name', 'Unknown'), 'short': True},
                        {'title': 'Type', 'value': alert_type, 'short': True},
                        {'title': 'Details', 'value': self._format_details(alert_type, data), 'short': False},
                        {'title': 'Confidence', 'value': f"{data.get('confidence', 0) * 100:.0f}%", 'short': True},
                        {'title': 'Time', 'value': datetime.now().strftime('%Y-%m-%d %H:%M'), 'short': True}
                    ]
                }]
            }
            
            # Add additional context if available
            if data.get('signals'):
                payload['attachments'][0]['fields'].append({
                    'title': 'Signals',
                    'value': '\n'.join(f"• {signal}" for signal in data.get('signals', [])),
                    'short': False
                })
            
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False
    
    def _create_html_alert(self, alert_type: str, data: Dict, template: Dict) -> str:
        """Create HTML formatted alert"""
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: {self._get_html_color_for_priority(template.get('priority', 'low'))};">
                {template.get('emoji', '')} {template.get('subject', 'Alert')}
            </h2>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Details:</h3>
                <p><strong>Person:</strong> {data.get('name', 'Unknown')}</p>
                <p><strong>PDL ID:</strong> {data.get('pdl_id', 'N/A')}</p>
                <p><strong>Alert Type:</strong> {alert_type}</p>
                <p><strong>Description:</strong> {self._format_details(alert_type, data)}</p>
                <p><strong>Confidence:</strong> {data.get('confidence', 0) * 100:.0f}%</p>
                <p><strong>Detected:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # Add signals if present
        if data.get('signals'):
            html += """
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Detected Signals:</h3>
                <ul>
            """
            for signal in data.get('signals', []):
                html += f"<li>{signal}</li>"
            html += """
                </ul>
            </div>
            """
        
        # Add action buttons
        if data.get('pdl_id'):
            html += f"""
            <div style="margin-top: 20px;">
                <a href="https://www.linkedin.com/search/results/people/?keywords={data.get('name', '').replace(' ', '%20')}" 
                   style="background: #0077b5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                   View on LinkedIn
                </a>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _format_details(self, alert_type: str, data: Dict) -> str:
        """Format alert details based on type"""
        
        if alert_type == 'departure':
            return f"Left {data.get('old_company', 'previous company')} without listing new role"
        elif alert_type == 'stealth_company':
            return f"Now at '{data.get('new_company', 'unknown')}' - potential stealth startup"
        elif alert_type == 'job_title_change':
            return f"Changed from '{data.get('old_title', 'previous')}' to '{data.get('new_title', 'new')}'"
        elif alert_type == 'building_something':
            return f"Profile indicates: {data.get('description', 'building activity')}"
        elif alert_type == 'company_change':
            return f"Moved from {data.get('old_company', 'previous')} to {data.get('new_company', 'new')}"
        else:
            return data.get('description', 'Employment change detected')
    
    def _get_color_for_priority(self, priority: str) -> str:
        """Get Slack color for priority"""
        colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'good'
        }
        return colors.get(priority, 'gray')
    
    def _get_html_color_for_priority(self, priority: str) -> str:
        """Get HTML color for priority"""
        colors = {
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        return colors.get(priority, '#6c757d')
    
    def send_batch_alerts(self, alerts: List[Dict]) -> Dict:
        """Send multiple alerts in batch"""
        
        results = {
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        # Group alerts by priority
        high_priority = [a for a in alerts if self.alert_templates.get(a['type'], {}).get('priority') == 'high']
        medium_priority = [a for a in alerts if self.alert_templates.get(a['type'], {}).get('priority') == 'medium']
        low_priority = [a for a in alerts if self.alert_templates.get(a['type'], {}).get('priority') == 'low']
        
        # Send high priority immediately
        for alert in high_priority:
            success = self.send_alert(alert['type'], alert['data'])
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
            results['details'].append({
                'type': alert['type'],
                'success': success,
                'priority': 'high'
            })
        
        # Batch medium and low priority into digest
        if medium_priority or low_priority:
            digest_success = self.send_digest(medium_priority + low_priority)
            results['sent'] += len(medium_priority + low_priority) if digest_success else 0
            results['failed'] += len(medium_priority + low_priority) if not digest_success else 0
        
        return results
    
    def send_digest(self, alerts: List[Dict]) -> bool:
        """Send a digest of multiple alerts"""
        
        if not alerts:
            return True
        
        try:
            # Create digest email
            subject = f"📊 Employment Monitoring Digest - {len(alerts)} Updates"
            
            html = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Employment Monitoring Digest</h2>
                <p>Summary of {count} employment changes detected:</p>
            """.format(count=len(alerts))
            
            # Group by type
            by_type = {}
            for alert in alerts:
                alert_type = alert.get('type', 'unknown')
                if alert_type not in by_type:
                    by_type[alert_type] = []
                by_type[alert_type].append(alert)
            
            # Add sections for each type
            for alert_type, items in by_type.items():
                template = self.alert_templates.get(alert_type, {})
                html += f"""
                <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid {self._get_html_color_for_priority(template.get('priority', 'low'))};">
                    <h3>{template.get('emoji', '')} {template.get('subject', alert_type)} ({len(items)} updates)</h3>
                    <ul>
                """
                
                for item in items[:5]:  # Limit to 5 per type
                    html += f"<li>{item['data'].get('name', 'Unknown')}: {self._format_details(alert_type, item['data'])}</li>"
                
                if len(items) > 5:
                    html += f"<li><em>...and {len(items) - 5} more</em></li>"
                
                html += """
                    </ul>
                </div>
                """
            
            html += """
            </body>
            </html>
            """
            
            # Send digest email
            if self.email_from and self.email_to:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.email_from
                msg['To'] = ', '.join(self.email_to)
                msg.attach(MIMEText(html, 'html'))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_from, self.email_password)
                    server.send_message(msg)
                
                logger.info(f"Digest sent with {len(alerts)} alerts")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send digest: {e}")
            return False
    
    def send_alert(self, alert_type: str, data: Dict) -> bool:
        """Send alert via configured channels"""
        
        success = False
        
        # Try email
        if self.email_from:
            success = self.send_email_alert(alert_type, data) or success
        
        # Try webhook
        if self.webhook_url:
            success = self.send_webhook_alert(alert_type, data) or success
        
        if not success:
            logger.warning(f"Failed to send any alert for {alert_type}")
        
        return success


def test_alerts():
    """Test alert system with sample data"""
    
    alert_system = AlertSystem()
    
    # Test different alert types
    test_alerts = [
        {
            'type': 'departure',
            'data': {
                'name': 'John Doe',
                'pdl_id': 'test123',
                'old_company': 'OpenAI',
                'confidence': 0.95,
                'signals': ['Left OpenAI last week', 'No new company listed']
            }
        },
        {
            'type': 'stealth_company',
            'data': {
                'name': 'Jane Smith',
                'pdl_id': 'test456',
                'new_company': 'Stealth Startup',
                'confidence': 0.85,
                'signals': ['Company name contains "stealth"', 'Company size 1-10']
            }
        },
        {
            'type': 'building_something',
            'data': {
                'name': 'Bob Johnson',
                'pdl_id': 'test789',
                'description': 'Building something cool in AI',
                'confidence': 0.80,
                'signals': ['Title: "Working on something new"', 'Recent Google departure']
            }
        }
    ]
    
    # Send test alerts
    for alert in test_alerts:
        print(f"Sending test alert: {alert['type']}")
        success = alert_system.send_alert(alert['type'], alert['data'])
        print(f"  Result: {'Success' if success else 'Failed'}")
    
    # Test batch/digest
    print("\nSending batch digest...")
    results = alert_system.send_batch_alerts(test_alerts)
    print(f"Batch results: {results}")


if __name__ == "__main__":
    test_alerts()