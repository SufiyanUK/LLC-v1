"""
Email Configuration Setup for Employee Tracker
Configure email alerts for Level 2 and Level 3 departures
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key
import smtplib
from email.mime.text import MIMEText

def test_email_connection(smtp_server, smtp_port, sender_email, sender_password):
    """Test if email credentials work"""
    try:
        print(f"\n[TEST] Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        print("[SUCCESS] Email connection successful!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect: {str(e)}")
        return False

def send_test_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email):
    """Send a test email"""
    try:
        msg = MIMEText("This is a test email from Employee Tracker. Your email alerts are configured correctly!")
        msg['Subject'] = "[TEST] Employee Tracker Alert System"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[SUCCESS] Test email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send test email: {str(e)}")
        return False

def setup_gmail():
    """Guide for Gmail setup"""
    print("\n" + "="*60)
    print("GMAIL SETUP INSTRUCTIONS")
    print("="*60)
    print("\n1. Enable 2-Step Verification:")
    print("   - Go to: https://myaccount.google.com/security")
    print("   - Click on '2-Step Verification' and enable it")
    print("\n2. Generate App Password:")
    print("   - Go to: https://myaccount.google.com/apppasswords")
    print("   - Select 'Mail' as the app")
    print("   - Select 'Other' as device and name it 'Employee Tracker'")
    print("   - Copy the 16-character password (no spaces)")
    print("\n3. Use these settings:")
    print("   - SMTP Server: smtp.gmail.com")
    print("   - SMTP Port: 587")
    print("   - Email: your-email@gmail.com")
    print("   - Password: [16-character app password]")
    print("="*60)

def setup_outlook():
    """Guide for Outlook/Hotmail setup"""
    print("\n" + "="*60)
    print("OUTLOOK/HOTMAIL SETUP INSTRUCTIONS")
    print("="*60)
    print("\n1. Enable 2-Step Verification (if not enabled):")
    print("   - Go to: https://account.microsoft.com/security")
    print("   - Enable two-step verification")
    print("\n2. Use these settings:")
    print("   - SMTP Server: smtp-mail.outlook.com")
    print("   - SMTP Port: 587")
    print("   - Email: your-email@outlook.com")
    print("   - Password: Your regular password (or app password if 2FA enabled)")
    print("="*60)

def configure_email():
    """Interactive email configuration"""
    print("\n" + "="*60)
    print("EMAIL ALERT CONFIGURATION")
    print("="*60)
    print("\nThis will configure email alerts for Level 2 and Level 3 departures.")
    print("Level 2: Building signals (orange alerts)")
    print("Level 3: Joined startup/founder (red alerts)")
    
    # Check for existing .env file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"\n[INFO] Found existing .env file at {env_path}")
    else:
        print(f"\n[INFO] Creating new .env file at {env_path}")
        env_path.touch()
    
    # Email provider selection
    print("\n" + "-"*40)
    print("SELECT EMAIL PROVIDER:")
    print("-"*40)
    print("1. Gmail")
    print("2. Outlook/Hotmail")
    print("3. Custom SMTP")
    print("4. Skip (configure later)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '4':
        print("\n[INFO] Skipping email configuration.")
        print("You can run this script again later to configure email alerts.")
        return
    
    # Show setup instructions
    if choice == '1':
        setup_gmail()
        smtp_server = 'smtp.gmail.com'
        smtp_port = '587'
    elif choice == '2':
        setup_outlook()
        smtp_server = 'smtp-mail.outlook.com'
        smtp_port = '587'
    else:
        smtp_server = input("\nEnter SMTP server (e.g., smtp.gmail.com): ").strip()
        smtp_port = input("Enter SMTP port (e.g., 587): ").strip()
    
    # Get credentials
    print("\n" + "-"*40)
    print("ENTER CREDENTIALS:")
    print("-"*40)
    sender_email = input("Enter sender email address: ").strip()
    sender_password = input("Enter email password/app password: ").strip()
    
    # Test connection
    print("\n" + "-"*40)
    print("TESTING CONNECTION...")
    print("-"*40)
    
    if test_email_connection(smtp_server, smtp_port, sender_email, sender_password):
        # Save to .env
        set_key(env_path, 'SMTP_SERVER', smtp_server)
        set_key(env_path, 'SMTP_PORT', smtp_port)
        set_key(env_path, 'SENDER_EMAIL', sender_email)
        set_key(env_path, 'SENDER_PASSWORD', sender_password)
        
        print("\n[SUCCESS] Email configuration saved to .env file")
        
        # Configure alert recipients
        print("\n" + "-"*40)
        print("CONFIGURE ALERT RECIPIENTS:")
        print("-"*40)
        recipient_email = input("Enter email to receive alerts (can be same as sender): ").strip()
        set_key(env_path, 'ALERT_EMAIL', recipient_email)
        
        # Alert level configuration
        print("\n" + "-"*40)
        print("CONFIGURE ALERT LEVELS:")
        print("-"*40)
        print("Which alert levels should trigger emails?")
        print("1. Level 2 and 3 only (Building signals + Startups)")
        print("2. Level 3 only (Startups/Founders only)")
        print("3. All levels (1, 2, and 3)")
        
        level_choice = input("\nEnter choice (1-3) [default: 1]: ").strip() or '1'
        
        if level_choice == '1':
            set_key(env_path, 'MIN_ALERT_LEVEL', '2')
            print("[INFO] Will send emails for Level 2 and 3 alerts only")
        elif level_choice == '2':
            set_key(env_path, 'MIN_ALERT_LEVEL', '3')
            print("[INFO] Will send emails for Level 3 alerts only")
        else:
            set_key(env_path, 'MIN_ALERT_LEVEL', '1')
            print("[INFO] Will send emails for all alert levels")
        
        # Send test email
        print("\n" + "-"*40)
        test = input("Send a test email? (y/n): ").strip().lower()
        if test == 'y':
            send_test_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email)
        
        print("\n" + "="*60)
        print("EMAIL CONFIGURATION COMPLETE!")
        print("="*60)
        print("\nYour settings:")
        print(f"  SMTP Server: {smtp_server}")
        print(f"  SMTP Port: {smtp_port}")
        print(f"  Sender: {sender_email}")
        print(f"  Recipient: {recipient_email}")
        print(f"  Alert Levels: {level_choice}")
        print("\nEmail alerts will be sent automatically when departures are detected.")
        
    else:
        print("\n[ERROR] Email configuration failed. Please check your credentials.")
        print("Run this script again to retry.")

def check_current_config():
    """Check current email configuration"""
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print("\n[WARNING] No .env file found. Email alerts not configured.")
        return False
    
    load_dotenv(env_path)
    
    smtp_server = os.getenv('SMTP_SERVER')
    sender_email = os.getenv('SENDER_EMAIL')
    alert_email = os.getenv('ALERT_EMAIL')
    min_level = os.getenv('MIN_ALERT_LEVEL', '1')
    
    if not smtp_server or not sender_email:
        print("\n[WARNING] Email configuration incomplete.")
        return False
    
    print("\n" + "="*60)
    print("CURRENT EMAIL CONFIGURATION")
    print("="*60)
    print(f"  SMTP Server: {smtp_server}")
    print(f"  Sender Email: {sender_email}")
    print(f"  Alert Recipient: {alert_email or 'Not configured'}")
    print(f"  Minimum Alert Level: {min_level}")
    
    level_desc = {
        '1': 'All departures',
        '2': 'Level 2 (Building) and Level 3 (Startup) only',
        '3': 'Level 3 (Startup/Founder) only'
    }
    print(f"  Alert Policy: {level_desc.get(min_level, 'Unknown')}")
    
    return True

def main():
    """Main configuration menu"""
    print("\n" + "="*60)
    print("EMPLOYEE TRACKER - EMAIL ALERT SETUP")
    print("="*60)
    
    # Check current configuration
    has_config = check_current_config()
    
    print("\n" + "-"*40)
    print("OPTIONS:")
    print("-"*40)
    
    if has_config:
        print("1. Test current configuration")
        print("2. Reconfigure email settings")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            # Test current config
            load_dotenv(Path(__file__).parent / '.env')
            test_email_connection(
                os.getenv('SMTP_SERVER'),
                os.getenv('SMTP_PORT'),
                os.getenv('SENDER_EMAIL'),
                os.getenv('SENDER_PASSWORD')
            )
            
            test = input("\nSend test email? (y/n): ").strip().lower()
            if test == 'y':
                send_test_email(
                    os.getenv('SMTP_SERVER'),
                    os.getenv('SMTP_PORT'),
                    os.getenv('SENDER_EMAIL'),
                    os.getenv('SENDER_PASSWORD'),
                    os.getenv('ALERT_EMAIL', os.getenv('SENDER_EMAIL'))
                )
        elif choice == '2':
            configure_email()
    else:
        configure_email()

if __name__ == "__main__":
    main()