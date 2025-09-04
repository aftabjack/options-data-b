#!/usr/bin/env python3
"""
Test Critical Notifications via Telegram Bot
"""

import asyncio
import os
from telegram_bot_notifier import SimplifiedNotificationManager, TelegramBotNotifier

async def test_critical_notifications():
    """Test critical notification scenarios"""
    
    print("\n" + "="*60)
    print("TELEGRAM BOT NOTIFICATION TEST")
    print("="*60)
    
    # Test basic connection
    bot = TelegramBotNotifier()
    if not bot.enabled:
        print("❌ Bot not configured! Check .env file")
        return
    
    if not bot.test_connection():
        print("❌ Failed to connect to bot")
        return
    
    print(f"✅ Connected to Telegram bot")
    print(f"   Chat ID: {bot.chat_id}")
    
    # Test notification manager
    manager = SimplifiedNotificationManager()
    
    print("\n📤 Sending test notifications...")
    print("-" * 40)
    
    # Test 1: Critical Redis failure
    print("\n1. Testing CRITICAL Redis failure...")
    await manager.redis_critical("Connection refused - Redis container is down")
    print("   ✅ Sent Redis critical notification")
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Test 2: Critical WebSocket failure
    print("\n2. Testing CRITICAL WebSocket failure...")
    await manager.websocket_critical("Persistent connection failure after 10 attempts")
    print("   ✅ Sent WebSocket critical notification")
    
    await asyncio.sleep(2)
    
    # Test 3: Health check failure
    print("\n3. Testing CRITICAL health check failure...")
    await manager.health_check_critical("Redis", "No response for 5 minutes")
    print("   ✅ Sent health check critical notification")
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\n📱 Check your Telegram for 3 critical notifications")
    print("\nConfiguration summary:")
    print("✅ Bot Token: Configured")
    print(f"✅ Chat ID: {bot.chat_id}")
    print("✅ Throttling: 5 minutes between similar messages")
    print("✅ Mode: CRITICAL ERRORS ONLY")
    print("\nNotifications will be sent for:")
    print("• Redis connection failures")
    print("• Persistent WebSocket failures")
    print("• Health check failures")
    print("• Any manual intervention required")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_critical_notifications())