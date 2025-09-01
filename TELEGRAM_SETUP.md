# Telegram Notifications Setup Guide

## Overview
The Bybit Options Tracker includes Telegram notifications for critical alerts, errors, and system status updates.

## Prerequisites
1. Telegram account
2. Telegram API credentials (API ID and API Hash)
3. A Telegram channel or group for notifications

## Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click on "API development tools"
4. Create a new application:
   - App title: Bybit Options Tracker
   - Short name: bybit_tracker
   - Platform: Other
5. Save your:
   - **API ID**: (numerical value)
   - **API Hash**: (alphanumeric string)

## Step 2: Initial Setup

Run the Telegram setup script:

```bash
# Activate Python environment if needed
python3 telegram_notifier.py
```

Follow the prompts:
1. Enter your API ID
2. Enter your API Hash
3. Enter your phone number (with country code, e.g., +1234567890)
4. Enter the verification code sent to your Telegram
5. If you have 2FA enabled, enter your password
6. Select a channel/group ID from the displayed list

## Step 3: Configure Environment

Add the credentials to your `.env` file:

```env
# Enable notifications
ENABLE_NOTIFICATIONS=true

# Your Telegram API credentials
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_NOTIFICATION_CHANNEL=your_channel_id_here
```

## Step 4: Test Notifications

Run the test script to verify everything works:

```bash
python3 scripts/test_telegram.py
```

You should receive test notifications for:
- ✅ Success message
- 🔵 Info message
- 🟡 Warning message
- 🟠 Error message
- 🔴 Critical alert

## Step 5: Docker Integration

For Docker deployment, update your `.env` file and restart:

```bash
# Stop services
./docker-stop.sh

# Start with notifications enabled
./docker-start.sh
```

## Notification Types

### Critical Alerts 🔴
- System failures
- Redis connection lost
- Multiple consecutive errors

### Error Notifications 🟠
- WebSocket disconnections
- API failures
- Processing errors

### Warning Messages 🟡
- High resource usage
- Performance degradation
- Rate limiting

### Info Messages 🔵
- System startup
- System shutdown
- Configuration changes

### Success Messages 🟢
- Successful connections
- Test completions
- Recovery from errors

## Throttling

To prevent spam, similar messages are throttled:
- Same error type: 60 seconds minimum between messages
- Escalation: After 5 errors of same type, escalates to critical

## Troubleshooting

### Session File Issues
If you see "Session file corrupted":
```bash
rm bybit_tracker_session.session
python3 telegram_notifier.py
```

### Authorization Issues
If authorization fails:
1. Ensure phone number includes country code
2. Check that API credentials are correct
3. Verify 2FA password if enabled

### No Messages Received
1. Check ENABLE_NOTIFICATIONS=true in .env
2. Verify channel ID is correct (negative number for channels)
3. Ensure bot has permission to post in channel
4. Check Docker logs: `docker-compose logs tracker`

### Rate Limiting
If you see "FloodWaitError":
- Telegram is rate limiting your requests
- Wait the specified time before retrying
- Throttling is automatic for subsequent messages

## Security Notes

1. **Never commit** your `.env` file with credentials
2. Keep your API Hash secret
3. The session file (`bybit_tracker_session.session`) contains authentication - keep it secure
4. Use environment variables for production deployments

## Advanced Configuration

### Custom Throttle Time
Modify in `telegram_notifier.py`:
```python
self.throttle_seconds = 60  # Change to desired seconds
```

### Error Escalation Threshold
Modify in `telegram_notifier.py`:
```python
self.max_errors_before_critical = 5  # Change threshold
```

### Add Custom Notification Types
In your code:
```python
from telegram_notifier import notification_manager

# Send custom notification
await notification_manager.notifier.send_notification(
    title="Custom Alert",
    message="Your custom message",
    severity="INFO",
    details={"key": "value"}
)
```

## Monitoring Integration

The notification system integrates with:
- Health checks (`scripts/health_check.sh`)
- Resource monitoring (`scripts/monitor_resources.py`)
- Status checks (`scripts/check_status.py`)

All critical issues detected by monitoring scripts trigger Telegram alerts automatically.

## Disable Notifications

To temporarily disable without removing configuration:

```env
ENABLE_NOTIFICATIONS=false
```

## Support

For issues with Telegram notifications:
1. Check the tracker logs: `docker-compose logs tracker`
2. Verify credentials in `.env`
3. Run test script: `python3 scripts/test_telegram.py`
4. Review this guide for troubleshooting steps