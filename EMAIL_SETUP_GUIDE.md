# Email Alert Setup Guide

## Quick Setup

Run this command to configure email alerts:
```bash
setup_email.bat
```

Or manually:
```bash
python configure_email.py
```

## What Gets Configured

### Alert Levels
By default, you'll receive emails for:
- **Level 2 (Orange)**: "Building something new" signals
- **Level 3 (Red)**: Joined startup or became founder

Level 1 (standard departures) are NOT emailed by default to reduce noise.

### Email Types You'll Receive

#### Level 3 - HIGH PRIORITY (Red Alert)
```
Subject: 🚨 HIGH PRIORITY - Startup Departure: John Doe from OpenAI
Priority: High (marked urgent in email client)

John Doe left OpenAI
Now at: TinyAI Startup (1-10 employees, founded 2024)
Title: CTO & Co-Founder
Signals: startup_size, recent_founding, cto_cofounder
LinkedIn: [profile link]
```

#### Level 2 - IMPORTANT (Orange Alert)
```
Subject: ⚠️ IMPORTANT - Building Signals: Jane Smith from Anthropic

Jane Smith showing building signals
Headline: "Building something new in AI | Ex-Anthropic"
Signals: building_something, stealth_mode
LinkedIn: [profile link]
```

## Gmail Setup Instructions

### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow prompts to enable

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" as the app
3. Select "Other" as device
4. Name it "Employee Tracker"
5. Copy the 16-character password (no spaces!)

### Step 3: Configure
```
SMTP Server: smtp.gmail.com
SMTP Port: 587
Email: your-email@gmail.com
Password: [16-character app password from Step 2]
```

## Outlook/Hotmail Setup

### For Outlook.com/Hotmail
```
SMTP Server: smtp-mail.outlook.com
SMTP Port: 587
Email: your-email@outlook.com
Password: Your regular password (or app password if 2FA enabled)
```

### For Office 365
```
SMTP Server: smtp.office365.com
SMTP Port: 587
Email: your-email@company.com
Password: Your password
```

## Testing Your Configuration

### 1. Check Current Configuration
```bash
python configure_email.py
```
Choose option 1 to see current settings

### 2. Send Test Email
The setup script will offer to send a test email. This helps verify:
- Credentials are correct
- Email delivery works
- You can receive alerts

### 3. Test with Mock Departure
```bash
python scripts/send_departure_alerts.py
```
This sends test alerts without using real data

## When Emails Are Sent

Emails are sent automatically when:

1. **During Departure Check**
   - When you click "Check for Departures" in UI
   - When monthly automated check runs
   - When you run `python scripts/employee_tracker.py`

2. **Only for Qualified Departures**
   - Level 2: Building signals detected
   - Level 3: Joined startup/small company

3. **Smart Grouping**
   - Level 3 alerts sent individually (highest priority)
   - Level 2 alerts grouped by company
   - Level 1 alerts grouped together (if enabled)

## Configuration File

Your settings are saved in `.env` file:
```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Alert Configuration
ALERT_EMAIL=alerts@yourcompany.com
MIN_ALERT_LEVEL=2  # 1=all, 2=Level2+3, 3=Level3 only
```

## Troubleshooting

### "Authentication failed"
- Gmail: Make sure you're using app password, not regular password
- Check 2-factor authentication is enabled
- Verify no spaces in app password

### "Connection timeout"
- Check firewall/antivirus isn't blocking port 587
- Try port 465 with SSL if 587 doesn't work
- Verify SMTP server address is correct

### Not receiving emails
- Check spam/junk folder
- Verify ALERT_EMAIL is correct in .env
- Run test to confirm delivery works

### Test without real data
```bash
cd employee_tracker/test_system
python test_departure_system.py
```
This won't send emails but shows what would be sent

## Security Notes

- **Never commit .env file** to version control
- App passwords are safer than regular passwords
- Consider using a dedicated email account for alerts
- The .env file contains sensitive credentials - keep it secure

## Changing Configuration

To change email settings later:
```bash
python configure_email.py
```
Choose option 2 to reconfigure

## Disabling Email Alerts

To temporarily disable without losing configuration:
1. Set `MIN_ALERT_LEVEL=99` in .env file
2. Or remove ALERT_EMAIL from .env file

To completely remove:
1. Delete the .env file
2. Emails will no longer be sent