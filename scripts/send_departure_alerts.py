"""
Send Email Alerts for Departures
Filters by alert level and sends appropriate notifications
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from email_alerts import EmailAlertSender

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

async def send_departure_alerts(departures: List[Dict]) -> bool:
    """
    Send email alerts for departures based on configured alert levels
    
    Args:
        departures: List of departure dictionaries with alert_level field
    
    Returns:
        True if emails were sent successfully
    """
    
    if not departures:
        print("[ALERTS] No departures to send alerts for")
        return False
    
    # Get configuration
    min_alert_level = int(os.getenv('MIN_ALERT_LEVEL', '2'))
    alert_email = os.getenv('ALERT_EMAIL', os.getenv('SENDER_EMAIL'))
    
    if not alert_email:
        print("[ALERTS] No alert email configured. Run configure_email.py to set up.")
        return False
    
    # Filter departures by alert level
    filtered_departures = [
        d for d in departures 
        if d.get('alert_level', 1) >= min_alert_level
    ]
    
    if not filtered_departures:
        print(f"[ALERTS] No departures at or above Level {min_alert_level}")
        return False
    
    # Group by alert level for separate emails
    level_3 = [d for d in filtered_departures if d.get('alert_level') == 3]
    level_2 = [d for d in filtered_departures if d.get('alert_level') == 2]
    level_1 = [d for d in filtered_departures if d.get('alert_level') == 1]
    
    sender = EmailAlertSender()
    success = True
    
    # Send Level 3 alerts (Highest Priority)
    if level_3:
        print(f"\n[ALERTS] Sending HIGH PRIORITY alert for {len(level_3)} startup departures...")
        for dep in level_3:
            # Send individual emails for Level 3
            result = await sender.send_alert(
                recipient_email=alert_email,
                company=dep['old_company'],
                departures=[dep],
                is_test=False
            )
            if result:
                print(f"  [SENT] Level 3 Alert: {dep['name']} -> {dep['new_company']}")
            else:
                success = False
    
    # Send Level 2 alerts (Important)
    if level_2:
        print(f"\n[ALERTS] Sending IMPORTANT alert for {len(level_2)} building signals...")
        # Group Level 2 alerts by company
        by_company = {}
        for dep in level_2:
            company = dep['old_company']
            if company not in by_company:
                by_company[company] = []
            by_company[company].append(dep)
        
        for company, deps in by_company.items():
            result = await sender.send_alert(
                recipient_email=alert_email,
                company=company,
                departures=deps,
                is_test=False
            )
            if result:
                print(f"  [SENT] Level 2 Alert: {len(deps)} from {company}")
            else:
                success = False
    
    # Send Level 1 alerts (if configured)
    if level_1 and min_alert_level <= 1:
        print(f"\n[ALERTS] Sending standard alert for {len(level_1)} departures...")
        # Group Level 1 alerts together
        result = await sender.send_alert(
            recipient_email=alert_email,
            company="Multiple",
            departures=level_1,
            is_test=False
        )
        if result:
            print(f"  [SENT] Level 1 Alert: {len(level_1)} standard departures")
        else:
            success = False
    
    # Summary
    print(f"\n[ALERTS SUMMARY]")
    print(f"  Total departures: {len(departures)}")
    print(f"  Alerts sent for: {len(filtered_departures)}")
    print(f"  Level 3 (Startup): {len(level_3)}")
    print(f"  Level 2 (Building): {len(level_2)}")
    if min_alert_level <= 1:
        print(f"  Level 1 (Standard): {len(level_1)}")
    
    return success

def send_alerts_sync(departures: List[Dict]) -> bool:
    """Synchronous wrapper for sending alerts"""
    try:
        return asyncio.run(send_departure_alerts(departures))
    except Exception as e:
        print(f"[ERROR] Failed to send alerts: {e}")
        return False

if __name__ == "__main__":
    # Test with sample data
    print("\n[TEST MODE] Testing email alert system...")
    
    test_departures = [
        {
            'name': 'John Doe',
            'old_company': 'OpenAI',
            'new_company': 'TinyStartup AI',
            'alert_level': 3,
            'alert_signals': ['startup_size', 'recent_founding']
        },
        {
            'name': 'Jane Smith',
            'old_company': 'Anthropic',
            'new_company': 'Stealth Mode',
            'alert_level': 2,
            'alert_signals': ['building_something', 'stealth_mode']
        }
    ]
    
    send_alerts_sync(test_departures)