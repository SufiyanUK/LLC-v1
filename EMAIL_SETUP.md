# Email Alert Configuration Guide

## How to Set Up Email Alerts for Departures

### Step 1: Configure Your Email Settings

Add these to your `.env` file in the employee_tracker folder:

```env
# Email Configuration (for departure alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### Step 2: Gmail Setup (Recommended)

If using Gmail:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Other" as device
   - Name it "Employee Tracker"
   - Copy the 16-character password
3. **Use this App Password** (not your regular password) in the `.env` file

### Step 3: Other Email Providers

#### Outlook/Hotmail:
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

#### Yahoo:
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

#### Custom/Corporate:
Ask your IT department for SMTP settings.

### Step 4: Test Your Configuration

1. Restart the API server after updating `.env`
2. Go to the Monitor tab
3. Enter your email in "Alert Email" field
4. Click "Test Check (No Credits)"
5. Check if you receive a test email

### How It Works

When you run a Departure Check with email alerts enabled:
1. System checks all employees for company changes
2. If departures are detected, creates an HTML email
3. Sends alert to your specified email address
4. Email includes:
   - Number of departures
   - Employee names and new companies
   - Seniority levels
   - Days since departure

### Troubleshooting

**"Sender credentials not configured"**
- Check your `.env` file has all 4 email settings

**"Failed to send: Authentication failed"**
- Wrong password (use App Password for Gmail)
- 2FA not enabled (required for App Passwords)

**"Failed to send: Connection refused"**
- Wrong SMTP server or port
- Firewall blocking connection

**No email received but no error**
- Check spam/junk folder
- Verify recipient email is correct

### Security Notes

- Never commit `.env` file to Git
- Use App Passwords, not regular passwords
- Consider creating a dedicated email account for alerts