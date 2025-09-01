#!/usr/bin/env python3
"""
Telegram Notification System for Bybit Options Tracker
Sends critical alerts and error notifications
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
import json

# Suppress telethon info logs
logging.getLogger('telethon').setLevel(logging.WARNING)

class TelegramNotifier:
    """Handles critical error notifications via Telegram"""
    
    def __init__(self, api_id: int = None, api_hash: str = None, 
                 session_name: str = 'bybit_tracker_session',
                 notification_channel: int = None):
        """
        Initialize Telegram notifier
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_name: Session file name
            notification_channel: Channel/chat ID for notifications
        """
        self.api_id = api_id or int(os.getenv('TELEGRAM_API_ID', '0'))
        self.api_hash = api_hash or os.getenv('TELEGRAM_API_HASH', '')
        self.session_name = session_name
        self.notification_channel = notification_channel or int(os.getenv('TELEGRAM_NOTIFICATION_CHANNEL', '0'))
        
        self.client = None
        self.connected = False
        self.enabled = bool(self.api_id and self.api_hash and self.notification_channel)
        
        # Message throttling
        self.last_message_time = {}
        self.throttle_seconds = 60  # Minimum seconds between similar messages
        
    async def connect(self):
        """Connect to Telegram"""
        if not self.enabled:
            return False
            
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logging.warning("Telegram client not authorized. Please run setup separately.")
                return False
                
            self.connected = True
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to Telegram: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
    
    def should_send_message(self, message_type: str) -> bool:
        """Check if we should send a message (throttling)"""
        current_time = datetime.now().timestamp()
        
        if message_type in self.last_message_time:
            time_diff = current_time - self.last_message_time[message_type]
            if time_diff < self.throttle_seconds:
                return False
        
        self.last_message_time[message_type] = current_time
        return True
    
    async def send_notification(self, title: str, message: str, 
                               severity: str = 'ERROR', 
                               details: Dict[str, Any] = None) -> bool:
        """
        Send notification to Telegram
        
        Args:
            title: Notification title
            message: Main message text
            severity: ERROR, WARNING, CRITICAL, INFO
            details: Additional details as dict
        
        Returns:
            bool: Success status
        """
        if not self.enabled or not self.connected:
            return False
        
        # Throttle similar messages
        message_type = f"{severity}:{title}"
        if not self.should_send_message(message_type):
            return False
        
        # Format message
        emoji_map = {
            'CRITICAL': '🔴',
            'ERROR': '🟠',
            'WARNING': '🟡',
            'INFO': '🔵',
            'SUCCESS': '🟢'
        }
        
        emoji = emoji_map.get(severity, '⚪')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        formatted_message = f"""
{emoji} **Bybit Options Tracker Alert**

**Severity:** {severity}
**Time:** {timestamp}
**Title:** {title}

**Message:**
{message}
"""
        
        if details:
            formatted_message += "\n**Details:**\n"
            for key, value in details.items():
                formatted_message += f"• {key}: {value}\n"
        
        try:
            await self.client.send_message(
                self.notification_channel,
                formatted_message,
                parse_mode='Markdown'
            )
            return True
            
        except FloodWaitError as e:
            logging.warning(f"Telegram rate limit: wait {e.seconds} seconds")
            return False
            
        except Exception as e:
            logging.error(f"Failed to send Telegram notification: {e}")
            return False
    
    # Convenience methods for different severity levels
    
    async def critical(self, title: str, message: str, details: Dict = None) -> bool:
        """Send critical error notification"""
        return await self.send_notification(title, message, 'CRITICAL', details)
    
    async def error(self, title: str, message: str, details: Dict = None) -> bool:
        """Send error notification"""
        return await self.send_notification(title, message, 'ERROR', details)
    
    async def warning(self, title: str, message: str, details: Dict = None) -> bool:
        """Send warning notification"""
        return await self.send_notification(title, message, 'WARNING', details)
    
    async def info(self, title: str, message: str, details: Dict = None) -> bool:
        """Send info notification"""
        return await self.send_notification(title, message, 'INFO', details)
    
    async def success(self, title: str, message: str, details: Dict = None) -> bool:
        """Send success notification"""
        return await self.send_notification(title, message, 'SUCCESS', details)


class NotificationManager:
    """Manages notifications for the options tracker"""
    
    def __init__(self):
        self.notifier = None
        self.error_counts = {}
        self.max_errors_before_critical = 5
        
    async def initialize(self):
        """Initialize the notification system"""
        self.notifier = TelegramNotifier()
        
        if await self.notifier.connect():
            await self.notifier.info(
                "System Started",
                "Bybit Options Tracker has been started successfully",
                {
                    "Redis": os.getenv('REDIS_HOST', 'localhost'),
                    "Environment": os.getenv('ENV', 'production')
                }
            )
            return True
        return False
    
    async def shutdown(self):
        """Clean shutdown of notification system"""
        if self.notifier and self.notifier.connected:
            await self.notifier.info(
                "System Shutdown",
                "Bybit Options Tracker is shutting down gracefully"
            )
            await self.notifier.disconnect()
    
    async def handle_error(self, error_type: str, error_message: str, 
                          details: Dict = None, critical: bool = False):
        """
        Handle and notify about errors
        
        Args:
            error_type: Type of error (e.g., 'WebSocket', 'Redis', 'API')
            error_message: Error message
            details: Additional error details
            critical: Whether this is a critical error
        """
        if not self.notifier:
            return
        
        # Track error frequency
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        
        self.error_counts[error_type] += 1
        
        # Escalate to critical if too many errors
        if self.error_counts[error_type] >= self.max_errors_before_critical:
            critical = True
            self.error_counts[error_type] = 0  # Reset counter
        
        # Send appropriate notification
        if critical:
            await self.notifier.critical(
                f"Critical {error_type} Error",
                error_message,
                details
            )
        else:
            await self.notifier.error(
                f"{error_type} Error",
                error_message,
                details
            )
    
    async def websocket_disconnected(self, reason: str = None):
        """Notify about WebSocket disconnection"""
        await self.handle_error(
            "WebSocket",
            f"WebSocket connection lost: {reason or 'Unknown reason'}",
            {"Action": "Attempting reconnection"},
            critical=False
        )
    
    async def redis_connection_failed(self, error: str):
        """Notify about Redis connection failure"""
        await self.handle_error(
            "Redis",
            f"Failed to connect to Redis: {error}",
            {"Impact": "Data storage unavailable"},
            critical=True
        )
    
    async def api_error(self, endpoint: str, error: str):
        """Notify about API errors"""
        await self.handle_error(
            "API",
            f"API request failed: {error}",
            {"Endpoint": endpoint},
            critical=False
        )
    
    async def performance_warning(self, metric: str, value: float, threshold: float):
        """Notify about performance issues"""
        if value > threshold:
            await self.notifier.warning(
                "Performance Warning",
                f"{metric} exceeded threshold",
                {
                    "Current": f"{value:.2f}",
                    "Threshold": f"{threshold:.2f}",
                    "Metric": metric
                }
            )
    
    async def health_check_failed(self, component: str, reason: str):
        """Notify about health check failures"""
        await self.handle_error(
            "HealthCheck",
            f"Health check failed for {component}",
            {"Reason": reason},
            critical=True
        )


# Singleton instance
notification_manager = NotificationManager()


# Setup script for first-time authorization
async def setup_telegram():
    """Setup script for Telegram authorization"""
    print("=== Telegram Notification Setup ===")
    
    api_id = input("Enter your Telegram API ID: ")
    api_hash = input("Enter your Telegram API Hash: ")
    phone = input("Enter your phone number (with country code): ")
    
    client = TelegramClient('bybit_tracker_session', int(api_id), api_hash)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("Enter the code you received: ")
        
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Two-factor authentication enabled. Enter password: ")
            await client.sign_in(password=password)
    
    print("✅ Successfully authorized!")
    
    # Get list of channels/chats
    print("\n=== Your Channels/Chats ===")
    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group:
            print(f"ID: {dialog.id} | Name: {dialog.name}")
    
    channel_id = input("\nEnter the channel/chat ID for notifications: ")
    
    # Save configuration
    print(f"""
✅ Setup complete! Add these to your .env file:

TELEGRAM_API_ID={api_id}
TELEGRAM_API_HASH={api_hash}
TELEGRAM_NOTIFICATION_CHANNEL={channel_id}
""")
    
    await client.disconnect()


if __name__ == "__main__":
    # Run setup if executed directly
    asyncio.run(setup_telegram())