#!/usr/bin/env python3
"""
Send a single test notification to verify Telegram is working
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram_notifier import TelegramNotifier

# Load environment variables
load_dotenv()

async def send_test():
    """Send a test notification"""
    
    print("\n" + "="*60)
    print("TELEGRAM TEST NOTIFICATION")
    print("="*60)
    
    # Check configuration
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    channel = os.getenv('TELEGRAM_NOTIFICATION_CHANNEL')
    
    if not api_id or api_id == "":
        print("\n❌ TELEGRAM_API_ID not set in .env file")
        print("\nTo get your Telegram API credentials:")
        print("1. Go to https://my.telegram.org")
        print("2. Login with your phone number")
        print("3. Click 'API Development Tools'")
        print("4. Create an app if you haven't already")
        print("5. Copy the API ID and API Hash")
        return
    
    if not api_hash or api_hash == "":
        print("\n❌ TELEGRAM_API_HASH not set in .env file")
        return
        
    if not channel or channel == "":
        print("\n❌ TELEGRAM_NOTIFICATION_CHANNEL not set in .env file")
        print("\nTo get your channel ID:")
        print("1. Create a Telegram channel or use an existing one")
        print("2. Forward a message from the channel to @userinfobot")
        print("3. The bot will reply with the channel ID (e.g., -1001234567890)")
        return
    
    print(f"\n✅ Configuration found:")
    print(f"   API ID: {api_id[:4]}..." if len(api_id) > 4 else f"   API ID: {api_id}")
    print(f"   Channel: {channel}")
    
    # Create notifier
    notifier = TelegramNotifier()
    
    if not notifier.enabled:
        print("\n❌ Telegram notifier not enabled. Check your credentials.")
        return
    
    print("\n🔄 Connecting to Telegram...")
    connected = await notifier.connect()
    
    if not connected:
        print("\n❌ Failed to connect to Telegram!")
        print("\nIf this is your first time:")
        print("1. You may need to authorize the app")
        print("2. Run this script and follow the prompts")
        print("3. You might need to enter your phone number and confirmation code")
        return
    
    print("✅ Connected to Telegram!")
    
    # Send test notification
    print("\n📤 Sending test notification...")
    
    success = await notifier.critical(
        "🧪 Test Notification",
        "This is a test message from Bybit Options Tracker",
        {
            "Status": "Telegram integration working",
            "Type": "Test message", 
            "Action": "No action needed"
        }
    )
    
    if success:
        print("✅ Test notification sent successfully!")
        print(f"\n📱 Check your Telegram channel: {channel}")
    else:
        print("❌ Failed to send test notification")
        print("   Check that the channel ID is correct and the bot has access")
    
    # Disconnect
    await notifier.disconnect()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(send_test())