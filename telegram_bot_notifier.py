#!/usr/bin/env python3
"""
Simple Telegram Bot Notifier for Critical Errors
Uses bot token instead of API credentials (simpler setup)
"""

import os
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TelegramBotNotifier:
    """Simple Telegram bot notifier for critical alerts"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        # Throttling
        self.last_message_time = {}
        self.throttle_seconds = 300  # 5 minutes between similar messages
        
        if self.enabled:
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def should_send(self, message_type: str) -> bool:
        """Check if we should send (throttling)"""
        current_time = datetime.now().timestamp()
        
        if message_type in self.last_message_time:
            time_diff = current_time - self.last_message_time[message_type]
            if time_diff < self.throttle_seconds:
                return False
        
        self.last_message_time[message_type] = current_time
        return True
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Telegram bot"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False
    
    def send_critical_error(self, title: str, message: str, details: Dict[str, Any] = None) -> bool:
        """Send a critical error notification"""
        
        # Get project name
        project_name = os.getenv('PROJECT_NAME', 'Bybit Options Tracker')
        
        # Format the message
        text = f"<b>🚨 [{project_name}]</b>\n"
        text += f"<b>CRITICAL: {title}</b>\n\n"
        text += f"{message}\n"
        
        if details:
            text += "\n<b>Details:</b>\n"
            for key, value in details.items():
                text += f"• {key}: {value}\n"
        
        text += f"\n<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        return self.send_message(text)
    
    def test_connection(self) -> bool:
        """Test if bot can send messages"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    print(f"✅ Bot connected: @{bot_info['result']['username']}")
                    return True
            return False
        except Exception as e:
            print(f"❌ Bot connection failed: {e}")
            return False


class SimplifiedNotificationManager:
    """Simplified notification manager using bot token"""
    
    def __init__(self):
        self.notifier = TelegramBotNotifier()
        self.error_counts = {}
        self.max_errors_before_critical = 10
        self.enabled = self.notifier.enabled
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self.enabled
    
    async def send_critical(self, error_type: str, message: str, details: Dict = None):
        """Send critical notification"""
        if not self.enabled:
            return
        
        # Track errors
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Check if should send
        if not self.notifier.should_send(error_type):
            return  # Throttled
        
        # Send notification
        self.notifier.send_critical_error(
            f"{error_type} Error",
            message,
            details
        )
    
    async def websocket_critical(self, reason: str):
        """Critical WebSocket failure"""
        await self.send_critical(
            "WebSocket",
            f"WebSocket persistently failing: {reason}",
            {"Action": "Manual restart may be required"}
        )
    
    async def redis_critical(self, error: str):
        """Critical Redis failure"""
        await self.send_critical(
            "Redis",
            f"Redis connection failed: {error}",
            {"Impact": "Data storage unavailable", "Action": "Check Redis container"}
        )
    
    async def health_check_critical(self, component: str, reason: str):
        """Critical health check failure"""
        await self.send_critical(
            "HealthCheck",
            f"{component} health check failed",
            {"Reason": reason, "Action": "Manual intervention required"}
        )


# Global instance for easy import
bot_notifier = SimplifiedNotificationManager()


# Test function
def test_notification():
    """Test sending a notification"""
    notifier = TelegramBotNotifier()
    
    if not notifier.enabled:
        print("❌ Telegram bot not configured!")
        print("Please check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return False
    
    # Test connection
    if not notifier.test_connection():
        return False
    
    # Send test message
    success = notifier.send_critical_error(
        "Test Notification",
        "This is a test message from Bybit Options Tracker",
        {
            "Status": "Bot integration working",
            "Type": "Test message",
            "Action": "No action needed"
        }
    )
    
    if success:
        print(f"✅ Test message sent to chat {notifier.chat_id}")
        return True
    else:
        print("❌ Failed to send test message")
        return False


if __name__ == "__main__":
    test_notification()