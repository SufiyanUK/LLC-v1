"""
Test script to send email using Brevo API to venrocksourcing@gmail.com
"""

import os
import sys
from dotenv import load_dotenv
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import email module
from employee_tracker.scripts.email_alerts import EmailAlertSender

async def send_test_email():
    """Send a test email to venrocksourcing@gmail.com using Brevo"""
    
    print("=" * 60)
    print("BREVO EMAIL TEST")
    print("=" * 60)
    
    # Initialize email sender
    sender = EmailAlertSender()
    
    # Check configuration
    if sender.use_brevo:
        print(f"[OK] Brevo configured")
        print(f"   - From: {sender.brevo_sender_email} ({sender.brevo_sender_name})")
        print(f"   - To: venrocksourcing@gmail.com")
        print(f"   - Using Brevo API (no personal email needed!)")
    else:
        print(f"[ERROR] Brevo not configured properly")
        print(f"   - API Key Set: {bool(os.getenv('BREVO_API_KEY'))}")
        print(f"   - Falling back to: {'Resend' if sender.use_resend else 'SMTP'}")
    
    # Create test departure data with LinkedIn URLs
    test_departures = [
        {
            'name': 'John Smith',
            'old_title': 'Senior ML Engineer',
            'old_company': 'OpenAI',
            'new_title': 'Co-Founder & CTO',
            'new_company': 'AI Startup Inc',
            'headline': 'Building something new in AI',
            'linkedin_url': 'https://www.linkedin.com/in/johnsmith-example',
            'seniority_level': 'C-Level',
            'is_ai_ml': True,
            'alert_level': 3,
            'alert_signals': ['Joined startup', 'C-Level position', 'AI/ML role']
        },
        {
            'name': 'Sarah Johnson',
            'old_title': 'Principal Engineer',
            'old_company': 'OpenAI',
            'new_title': 'VP of Engineering',
            'new_company': 'TechCorp',
            'linkedin_url': 'https://www.linkedin.com/in/sarahjohnson-example',
            'seniority_level': 'VP/Head',
            'is_ai_ml': False,
            'alert_level': 2,
            'alert_signals': ['Senior departure', 'VP position']
        },
        {
            'name': 'Mike Wilson',
            'old_title': 'Research Scientist',
            'old_company': 'OpenAI',
            'new_title': 'ML Researcher',
            'new_company': 'Google DeepMind',
            'linkedin_url': 'https://www.linkedin.com/in/mikewilson-example',
            'seniority_level': 'Senior IC',
            'is_ai_ml': True,
            'alert_level': 1,
            'alert_signals': ['AI/ML professional']
        }
    ]
    
    print("\n[EMAIL] Sending test email with 3 sample departures...")
    print("   - Level 3 (Red): John Smith -> Startup Co-Founder")
    print("   - Level 2 (Orange): Sarah Johnson -> VP Role")
    print("   - Level 1 (Yellow): Mike Wilson -> DeepMind")
    print("   - All include LinkedIn profile links")
    
    # Send the test email
    success = await sender.send_alert(
        recipient_email='venrocksourcing@gmail.com',
        company='OpenAI',
        departures=test_departures,
        is_test=True
    )
    
    if success:
        print("\n[SUCCESS] TEST EMAIL SENT SUCCESSFULLY VIA BREVO!")
        print("   Please check venrocksourcing@gmail.com inbox")
        print("   Subject: [TEST] HIGH PRIORITY - Startup Departure: 3 from OpenAI")
        print("   Sent using Brevo - NO personal email used!")
        return True
    else:
        print("\n[FAILED] Failed to send test email")
        print("   Please check Brevo configuration")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(send_test_email())
    
    print("\n" + "=" * 60)
    if success:
        print("BREVO TEST COMPLETED - Email sent to venrocksourcing@gmail.com")
        print("Using Brevo means your personal email is NOT exposed!")
    else:
        print("TEST FAILED - Please check configuration")
    print("=" * 60)