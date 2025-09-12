"""
Automated Monthly Departure Check Scheduler
Runs departure checks automatically on a schedule
"""

import schedule
import time
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

from scripts.employee_tracker import EmployeeTracker
from scripts.email_alerts import EmailAlertSender
from scripts.departure_classifier import DepartureClassifier

# Configuration
CHECK_DAY = 1  # Day of month to run (1 = first day)
CHECK_TIME = "09:00"  # Time to run (24-hour format)
ALERT_EMAIL = None  # Set to your email or leave None to get from .env

def run_monthly_check():
    """Run the monthly departure check"""
    print(f"\n{'='*60}")
    print(f"🤖 AUTOMATED DEPARTURE CHECK")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # Initialize tracker
        tracker = EmployeeTracker()
        
        # Get current tracking status
        status = tracker.get_tracking_status()
        print(f"\n📊 Current Status:")
        print(f"  Total Tracked: {status['total_tracked']}")
        print(f"  Active: {status['active']}")
        print(f"  Credits to be used: {status['active']}")
        
        if status['active'] == 0:
            print("\n⚠️ No active employees to check")
            return
        
        # Run the departure check
        print(f"\n🔍 Starting departure check...")
        departures = tracker.monthly_check()
        
        if departures:
            print(f"\n✅ Found {len(departures)} departures!")
            
            # Group by alert level
            level_3 = [d for d in departures if d.get('alert_level') == 3]
            level_2 = [d for d in departures if d.get('alert_level') == 2]
            level_1 = [d for d in departures if d.get('alert_level') == 1]
            
            # Print summary
            print(f"\n📊 Alert Summary:")
            if level_3:
                print(f"  🔴 Level 3 (Startup): {len(level_3)}")
                for dep in level_3:
                    print(f"     - {dep['name']} → {dep['new_company']}")
            if level_2:
                print(f"  🟠 Level 2 (Building): {len(level_2)}")
                for dep in level_2:
                    print(f"     - {dep['name']}: {', '.join(dep.get('alert_signals', [])[:1])}")
            if level_1:
                print(f"  🟡 Level 1 (Departed): {len(level_1)}")
            
            # Send email alerts if configured
            alert_sender = EmailAlertSender()
            if alert_sender.sender_email and alert_sender.sender_password:
                email_to_send = ALERT_EMAIL or alert_sender.sender_email
                
                # Send high priority alerts immediately
                if level_3:
                    print(f"\n📧 Sending Level 3 alerts to {email_to_send}")
                    import asyncio
                    asyncio.run(alert_sender.send_alert(
                        recipient_email=email_to_send,
                        company='Multiple',
                        departures=level_3
                    ))
                
                # Send other alerts in digest
                if level_2 or level_1:
                    all_others = level_2 + level_1
                    print(f"📧 Sending digest for {len(all_others)} other departures")
                    asyncio.run(alert_sender.send_alert(
                        recipient_email=email_to_send,
                        company='Multiple',
                        departures=all_others
                    ))
            else:
                print("\n📧 Email not configured - skipping alerts")
        else:
            print("\n✅ No departures detected")
        
        # Show next scheduled run
        next_run = schedule.next_run()
        if next_run:
            print(f"\n⏰ Next check scheduled for: {next_run}")
        
    except Exception as e:
        print(f"\n❌ Error in departure check: {e}")
        import traceback
        traceback.print_exc()

def run_test_check():
    """Run a test check without using credits"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST CHECK (No Credits Used)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        tracker = EmployeeTracker()
        status = tracker.get_tracking_status()
        
        print(f"\n📊 Would check:")
        print(f"  Employees: {status['active']}")
        print(f"  Credits: {status['active']}")
        print(f"  Companies: {', '.join(status['companies'].keys())}")
        
        print(f"\n✅ Test complete - system ready")
        
    except Exception as e:
        print(f"\n❌ Error in test: {e}")

def setup_schedule(schedule_type='monthly'):
    """
    Set up the schedule based on preference
    
    Options:
        'monthly' - Run on specific day each month
        'days' - Run every N days
        'weekly' - Run weekly
        'test' - Run every minute for testing
    """
    
    if schedule_type == 'monthly':
        # Run on the 1st of each month at 9 AM
        schedule.every().day.at(CHECK_TIME).do(check_if_first_of_month)
        print(f"📅 Scheduled: {CHECK_DAY}st of each month at {CHECK_TIME}")
        
    elif schedule_type == 'days':
        # Run every 30 days
        schedule.every(30).days.at(CHECK_TIME).do(run_monthly_check)
        print(f"📅 Scheduled: Every 30 days at {CHECK_TIME}")
        
    elif schedule_type == 'weekly':
        # Run every Monday
        schedule.every().monday.at(CHECK_TIME).do(run_monthly_check)
        print(f"📅 Scheduled: Every Monday at {CHECK_TIME}")
        
    elif schedule_type == 'test':
        # Run every minute for testing
        schedule.every(1).minutes.do(run_test_check)
        print(f"📅 TEST MODE: Running every minute")
    
    else:
        print(f"❌ Unknown schedule type: {schedule_type}")
        return False
    
    return True

def check_if_first_of_month():
    """Check if today is the scheduled day of month"""
    if datetime.now().day == CHECK_DAY:
        run_monthly_check()
    else:
        print(f"📅 Not the {CHECK_DAY}st yet (today is {datetime.now().day})")

def main():
    """Main scheduler loop"""
    print(f"\n{'='*60}")
    print(f"🤖 EMPLOYEE DEPARTURE CHECK SCHEDULER")
    print(f"{'='*60}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Choose schedule type (change this as needed)
    # Options: 'monthly', 'days', 'weekly', 'test'
    SCHEDULE_TYPE = 'monthly'
    
    # Set up schedule
    if not setup_schedule(SCHEDULE_TYPE):
        return
    
    # Show configuration
    tracker = EmployeeTracker()
    status = tracker.get_tracking_status()
    
    print(f"\n📊 Current Configuration:")
    print(f"  Tracking: {status['total_tracked']} employees")
    print(f"  Active: {status['active']} employees")
    print(f"  Companies: {len(status['companies'])}")
    print(f"  Credits per check: {status['active']}")
    
    # Calculate monthly cost
    monthly_cost = status['active']
    print(f"\n💰 Estimated Monthly Cost: {monthly_cost} credits")
    
    # Check email configuration
    from scripts.email_alerts import EmailAlertSender
    alert_sender = EmailAlertSender()
    if alert_sender.sender_email:
        print(f"📧 Email alerts: Configured ✅")
    else:
        print(f"📧 Email alerts: Not configured ⚠️")
    
    # Show next run time
    if schedule.next_run():
        print(f"\n⏰ First check will run at: {schedule.next_run()}")
    
    print(f"\n🎯 Scheduler is running! Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    # Optional: Run test immediately
    if SCHEDULE_TYPE == 'test':
        run_test_check()
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print(f"\n\n🛑 Scheduler stopped by user")
        print(f"Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Departure Check Scheduler')
    parser.add_argument('--test', action='store_true', help='Run in test mode (every minute, no credits)')
    parser.add_argument('--once', action='store_true', help='Run check once and exit')
    parser.add_argument('--schedule', choices=['monthly', 'days', 'weekly'], 
                       default='monthly', help='Schedule type')
    
    args = parser.parse_args()
    
    if args.once:
        # Just run once and exit
        run_monthly_check()
    elif args.test:
        # Test mode
        print("🧪 Running in TEST MODE")
        SCHEDULE_TYPE = 'test'
        main()
    else:
        # Normal scheduled mode
        main()