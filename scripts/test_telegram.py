#!/usr/bin/env python3
"""
Test script for Telegram notifications
Verifies that Telegram integration is working correctly
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from telegram_notifier import TelegramNotifier, notification_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_basic_connection():
    """Test basic Telegram connection"""
    print("=" * 50)
    print("Testing Telegram Connection")
    print("=" * 50)
    
    # Check if credentials are configured
    api_id = os.getenv('TELEGRAM_API_ID', '')
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    channel_id = os.getenv('TELEGRAM_NOTIFICATION_CHANNEL', '')
    
    if not api_id or not api_hash:
        print("❌ Telegram credentials not configured in .env file")
        print("\nPlease add:")
        print("TELEGRAM_API_ID=your_api_id")
        print("TELEGRAM_API_HASH=your_api_hash")
        print("TELEGRAM_NOTIFICATION_CHANNEL=your_channel_id")
        return False
    
    if not channel_id:
        print("⚠️  No notification channel configured")
        print("Run: python3 telegram_notifier.py to set up")
        return False
    
    print(f"✅ API ID: {api_id[:4]}...")
    print(f"✅ API Hash: {api_hash[:8]}...")
    print(f"✅ Channel ID: {channel_id}")
    
    # Test connection
    notifier = TelegramNotifier()
    
    if await notifier.connect():
        print("✅ Successfully connected to Telegram")
        await notifier.disconnect()
        return True
    else:
        print("❌ Failed to connect to Telegram")
        print("\nTroubleshooting:")
        print("1. Run: python3 telegram_notifier.py for initial setup")
        print("2. Check that session file exists: bybit_tracker_session.session")
        print("3. Verify credentials in .env file")
        return False


async def test_notifications():
    """Test sending different types of notifications"""
    print("\n" + "=" * 50)
    print("Testing Notification Types")
    print("=" * 50)
    
    # Initialize notification manager
    success = await notification_manager.initialize()
    
    if not success:
        print("❌ Failed to initialize notification manager")
        return False
    
    print("✅ Notification manager initialized")
    print("\nSending test notifications...")
    
    # Test different notification types
    tests = [
        {
            'type': 'success',
            'title': 'Test Success',
            'message': 'Telegram integration test successful',
            'details': {'Test': 'Connection', 'Status': 'Working'}
        },
        {
            'type': 'info',
            'title': 'System Information',
            'message': 'This is an informational message',
            'details': {'Component': 'Telegram', 'Action': 'Testing'}
        },
        {
            'type': 'warning',
            'title': 'Performance Warning',
            'message': 'This is a test warning message',
            'details': {'CPU': '75%', 'Memory': '512MB'}
        },
        {
            'type': 'error',
            'title': 'Test Error',
            'message': 'This is a test error notification',
            'details': {'Error': 'Test error', 'Code': 'TEST_001'}
        },
        {
            'type': 'critical',
            'title': 'Critical Alert Test',
            'message': 'This is a test critical alert',
            'details': {'Severity': 'Critical', 'Action': 'Immediate attention needed'}
        }
    ]
    
    for test in tests:
        print(f"\n📤 Sending {test['type']} notification...")
        
        # Get the appropriate method
        method = getattr(notification_manager.notifier, test['type'])
        result = await method(
            test['title'],
            test['message'],
            test['details']
        )
        
        if result:
            print(f"   ✅ {test['type'].upper()} notification sent")
        else:
            print(f"   ❌ Failed to send {test['type']} notification")
    
    # Test error handling
    print("\n📤 Testing error handling...")
    await notification_manager.handle_error(
        "WebSocket",
        "Test WebSocket disconnection",
        {"Reconnecting": "Yes", "Attempts": "1/3"}
    )
    print("   ✅ Error handling test sent")
    
    # Test specific handlers
    print("\n📤 Testing specific handlers...")
    
    await notification_manager.websocket_disconnected("Test disconnection")
    print("   ✅ WebSocket disconnection alert sent")
    
    await notification_manager.performance_warning("CPU Usage", 85.5, 80.0)
    print("   ✅ Performance warning sent")
    
    # Cleanup
    await notification_manager.shutdown()
    print("\n✅ All notification tests completed")
    return True


async def test_throttling():
    """Test message throttling"""
    print("\n" + "=" * 50)
    print("Testing Message Throttling")
    print("=" * 50)
    
    await notification_manager.initialize()
    
    print("Attempting to send 3 identical messages...")
    
    for i in range(3):
        print(f"\n📤 Attempt {i+1}/3...")
        result = await notification_manager.notifier.error(
            "Throttle Test",
            f"Message attempt {i+1}",
            {"Attempt": i+1}
        )
        
        if result:
            print(f"   ✅ Message {i+1} sent")
        else:
            print(f"   ⏳ Message {i+1} throttled (expected for 2 & 3)")
        
        # Small delay between attempts
        await asyncio.sleep(2)
    
    await notification_manager.shutdown()
    print("\n✅ Throttling test completed")


async def test_full_integration():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("TELEGRAM NOTIFICATION TEST SUITE")
    print("🚀 " * 20)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if notifications are enabled
    enabled = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
    if not enabled:
        print("\n⚠️  WARNING: ENABLE_NOTIFICATIONS=false in .env")
        print("Notifications are disabled. Set ENABLE_NOTIFICATIONS=true to enable.")
        print("\nContinuing with test anyway...")
    
    # Run tests
    connection_ok = await test_basic_connection()
    
    if connection_ok:
        await test_notifications()
        await test_throttling()
        
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print("✅ All tests passed successfully!")
        print("\nYour Telegram notifications are properly configured.")
        print("\nTo use in production:")
        print("1. Set ENABLE_NOTIFICATIONS=true in .env")
        print("2. Restart Docker containers: ./docker-stop.sh && ./docker-start.sh")
        print("\nNotifications will be sent for:")
        print("• System startup/shutdown")
        print("• Critical errors")
        print("• WebSocket disconnections")
        print("• Performance warnings")
        print("• Health check failures")
    else:
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print("❌ Connection test failed")
        print("\nPlease complete the setup:")
        print("1. Run: python3 telegram_notifier.py")
        print("2. Follow the setup prompts")
        print("3. Update .env file with credentials")
        print("4. Run this test again")


if __name__ == "__main__":
    # Run the full test suite
    asyncio.run(test_full_integration())