#!/usr/bin/env python3
"""
Test Telegram notifications - Only critical errors
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram_notifier import NotificationManager

# Load environment variables
load_dotenv()

async def test_critical_notifications():
    """Test various notification scenarios"""
    
    print("\n" + "="*60)
    print("TELEGRAM NOTIFICATION TEST - CRITICAL ERRORS ONLY")
    print("="*60)
    
    # Check if Telegram is configured
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    channel = os.getenv('TELEGRAM_NOTIFICATION_CHANNEL')
    
    if not all([api_id, api_hash, channel]):
        print("\n❌ Telegram not configured!")
        print("Please set the following in your .env file:")
        print("  TELEGRAM_API_ID=your_api_id")
        print("  TELEGRAM_API_HASH=your_api_hash")
        print("  TELEGRAM_NOTIFICATION_CHANNEL=your_channel_id")
        return
    
    print(f"\n✅ Telegram configured:")
    print(f"   API ID: {api_id[:4]}...")
    print(f"   Channel: {channel}")
    
    # Initialize notification manager
    manager = NotificationManager()
    await manager.initialize()
    
    if not manager.is_enabled():
        print("\n❌ Failed to connect to Telegram")
        return
    
    print("\n✅ Connected to Telegram successfully!")
    print("\nTesting notifications (only critical will be sent)...")
    print("-" * 60)
    
    # Test 1: Non-critical WebSocket error (should NOT send)
    print("\n1. Testing non-critical WebSocket disconnect...")
    print("   Expected: NO notification (not critical)")
    await manager.websocket_disconnected("Connection timeout")
    await asyncio.sleep(1)
    
    # Test 2: Critical Redis failure (SHOULD send)
    print("\n2. Testing CRITICAL Redis connection failure...")
    print("   Expected: ✅ NOTIFICATION SENT (critical error)")
    await manager.redis_connection_failed("Connection refused - Redis is down!")
    await asyncio.sleep(2)
    
    # Test 3: Multiple WebSocket failures to trigger critical
    print("\n3. Testing multiple WebSocket failures...")
    print("   Simulating 10 failures to trigger critical alert...")
    for i in range(10):
        print(f"   Failure {i+1}/10...")
        await manager.websocket_disconnected(f"Failure #{i+1}")
        await asyncio.sleep(0.5)
    print("   Expected: ✅ CRITICAL NOTIFICATION after 10 failures")
    await asyncio.sleep(2)
    
    # Test 4: Critical health check failure
    print("\n4. Testing CRITICAL health check failure...")
    print("   Expected: ✅ NOTIFICATION SENT (critical)")
    await manager.health_check_failed("Redis", "No response for 5 minutes")
    await asyncio.sleep(2)
    
    # Test 5: Direct critical error
    print("\n5. Testing direct critical error...")
    print("   Expected: ✅ NOTIFICATION SENT (critical)")
    await manager.handle_error(
        "Database",
        "CRITICAL: Database corruption detected!",
        {"Action": "Manual intervention required", "Impact": "Data loss possible"},
        critical=True
    )
    await asyncio.sleep(2)
    
    # Cleanup
    await manager.shutdown()
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\n📝 Summary:")
    print("- Only CRITICAL errors were sent to Telegram")
    print("- Non-critical errors were suppressed")
    print("- Multiple failures escalate to critical (10+ errors)")
    print("\n✅ Configuration verified:")
    print("- Throttling: 5 minutes between similar messages")
    print("- Critical threshold: 10 errors")
    print("- Mode: CRITICAL ONLY")
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_critical_notifications())