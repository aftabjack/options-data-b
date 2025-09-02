#!/usr/bin/env python3
"""
Configuration Loader for Bybit Options Production
Loads settings from config.yaml and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for the application"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_file.exists():
            print(f"Warning: {self.config_file} not found, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'services': {
                'webapp': {
                    'enabled': True,
                    'host': '0.0.0.0',
                    'port': 5001,
                    'external_url': 'http://localhost:5001'
                },
                'api': {
                    'enabled': True,
                    'host': '0.0.0.0', 
                    'port': 8000,
                    'external_url': 'http://localhost:8000',
                    'docs_url': 'http://localhost:8000/docs'
                }
            },
            'redis': {
                'host': 'redis',
                'port': 6379,
                'db': 0
            },
            'websocket': {
                'ping_interval': 45,
                'ping_timeout': 15,
                'batch_size': 200
            },
            'tracker': {
                'assets': ['BTC', 'ETH', 'SOL']
            }
        }
    
    def _apply_env_overrides(self):
        """Override config with environment variables"""
        # Override Redis settings
        if os.getenv('REDIS_HOST'):
            self.config['redis']['host'] = os.getenv('REDIS_HOST')
        if os.getenv('REDIS_PORT'):
            self.config['redis']['port'] = int(os.getenv('REDIS_PORT'))
        
        # Override service ports
        if os.getenv('WEBAPP_PORT'):
            self.config['services']['webapp']['port'] = int(os.getenv('WEBAPP_PORT'))
        if os.getenv('API_PORT'):
            self.config['services']['api']['port'] = int(os.getenv('API_PORT'))
        
        # Override Telegram settings
        if os.getenv('TELEGRAM_API_ID'):
            self.config['telegram']['api_id'] = os.getenv('TELEGRAM_API_ID')
        if os.getenv('TELEGRAM_API_HASH'):
            self.config['telegram']['api_hash'] = os.getenv('TELEGRAM_API_HASH')
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get config value by dot-notation path"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get all service URLs for display"""
        urls = {}
        
        for service, config in self.config.get('services', {}).items():
            if config.get('enabled'):
                urls[service] = {
                    'url': config.get('external_url'),
                    'description': config.get('description', ''),
                    'docs': config.get('docs_url', '')
                }
        
        return urls
    
    def print_access_info(self):
        """Print formatted access information"""
        print("\n" + "="*60)
        print("🚀 BYBIT OPTIONS PRODUCTION - ACCESS URLS")
        print("="*60)
        
        urls = self.get_service_urls()
        
        for service, info in urls.items():
            print(f"\n📌 {service.upper()}")
            print(f"   URL: {info['url']}")
            if info.get('description'):
                print(f"   Description: {info['description']}")
            if info.get('docs'):
                print(f"   API Docs: {info['docs']}")
        
        print("\n" + "="*60)
        print("💡 QUICK COMMANDS")
        print("="*60)
        print("• View logs:     docker-compose logs -f")
        print("• Check status:  python3 scripts/check_status.py")
        print("• Stop services: ./docker-stop.sh")
        print("• Restart:       docker-compose restart")
        
        print("\n" + "="*60)
        print("📊 MONITORING")
        print("="*60)
        print(f"• Redis CLI:     redis-cli -p {self.get('redis.port', 6379)}")
        print("• Container stats: docker stats")
        print("• Resource usage:  python3 scripts/monitor_resources.py")
        
        if self.get('telegram.enabled'):
            print("\n" + "="*60)
            print("🔔 NOTIFICATIONS: Telegram alerts enabled")
            print("="*60)
        
        print("\n✅ All services are starting...\n")

# Singleton instance
config = Config()

if __name__ == "__main__":
    # Test the config loader
    config = Config()
    config.print_access_info()
    
    # Print some config values
    print("\n📋 Configuration Test:")
    print(f"  Redis Host: {config.get('redis.host')}")
    print(f"  WebApp Port: {config.get('services.webapp.port')}")
    print(f"  API Port: {config.get('services.api.port')}")
    print(f"  Assets: {config.get('tracker.assets')}")
    print(f"  Environment: {config.get('environment', 'production')}")