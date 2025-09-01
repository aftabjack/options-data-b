#!/usr/bin/env python3
"""
Daily Symbol Updater for Bybit Options
Runs via cron job at 08:05 UTC to update expired and new symbols
"""

from dotenv import load_dotenv
load_dotenv()

import os
import json
import redis
import requests
from datetime import datetime
from typing import List, Set
from telegram_notifier import notification_manager
import asyncio

class SymbolUpdater:
    """Updates option symbols daily - removes expired, adds new"""
    
    def __init__(self):
        self.redis_client = None
        self.api_url = os.getenv('BYBIT_API_URL', 'https://api.bybit.com/v5/market/instruments-info')
        self.cache_file = 'symbols_cache.json'
        self.notifications_enabled = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
        
    def init_redis(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD', None),
                decode_responses=True
            )
            self.redis_client.ping()
            return True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return False
    
    def fetch_symbols(self) -> List[str]:
        """Fetch all current option symbols from Bybit"""
        all_symbols = []
        assets = os.getenv('OPTION_ASSETS', 'BTC,ETH,SOL').split(',')
        
        for asset in assets:
            try:
                params = {
                    'category': 'option',
                    'baseCoin': asset.strip(),
                    'limit': 1000
                }
                
                cursor = None
                while True:
                    if cursor:
                        params['cursor'] = cursor
                    
                    response = requests.get(
                        self.api_url,
                        params=params,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('retCode') == 0:
                            result = data.get('result', {})
                            items = result.get('list', [])
                            
                            for item in items:
                                if item.get('status') == 'Trading':
                                    all_symbols.append(item['symbol'])
                            
                            cursor = result.get('nextPageCursor')
                            if not cursor:
                                break
                        else:
                            break
                    else:
                        break
                        
            except Exception as e:
                print(f"Error fetching {asset} symbols: {e}")
                
        return all_symbols
    
    def get_expired_symbols(self, current_symbols: Set[str]) -> Set[str]:
        """Find expired symbols (in Redis but not in current API)"""
        try:
            # Get all option keys from Redis
            redis_symbols = set()
            for key in self.redis_client.keys("option:*"):
                symbol = key.replace("option:", "")
                redis_symbols.add(symbol)
            
            # Expired = in Redis but not in current symbols
            expired = redis_symbols - current_symbols
            return expired
            
        except Exception:
            return set()
    
    def remove_expired_symbols(self, expired_symbols: Set[str]) -> int:
        """Remove expired symbols from Redis"""
        removed_count = 0
        
        if not expired_symbols:
            return 0
            
        try:
            pipe = self.redis_client.pipeline()
            
            for symbol in expired_symbols:
                # Remove option data
                pipe.delete(f"option:{symbol}")
                # Remove time series data
                pipe.delete(f"ts:{symbol}")
                removed_count += 1
            
            pipe.execute()
            
        except Exception as e:
            print(f"Error removing expired symbols: {e}")
            
        return removed_count
    
    def update_cache(self, symbols: List[str]):
        """Update local cache file"""
        try:
            cache_data = {
                'symbols': symbols,
                'last_update': datetime.now().isoformat(),
                'count': len(symbols)
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating cache: {e}")
    
    async def run(self):
        """Main update process"""
        start_time = datetime.now()
        
        # Initialize notifications if enabled
        if self.notifications_enabled:
            await notification_manager.initialize()
        
        # Initialize Redis
        if not self.init_redis():
            if self.notifications_enabled:
                await notification_manager.error(
                    "Symbol Update Failed",
                    "Could not connect to Redis for daily symbol update"
                )
            return
        
        # Fetch current symbols from API
        current_symbols = self.fetch_symbols()
        current_set = set(current_symbols)
        
        # Find and remove expired symbols
        expired_symbols = self.get_expired_symbols(current_set)
        removed_count = self.remove_expired_symbols(expired_symbols)
        
        # Update cache
        self.update_cache(current_symbols)
        
        # Update stats in Redis
        try:
            self.redis_client.hset("stats:symbols", mapping={
                "total": len(current_symbols),
                "removed": removed_count,
                "expired_list": json.dumps(list(expired_symbols)[:10]),  # Store first 10 for reference
                "last_update": datetime.now().isoformat()
            })
        except Exception:
            pass
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Send notification if enabled
        if self.notifications_enabled and (removed_count > 0 or execution_time > 30):
            await notification_manager.info(
                "Daily Symbol Update",
                f"Symbol update completed successfully",
                {
                    "Total Symbols": len(current_symbols),
                    "Expired Removed": removed_count,
                    "Execution Time": f"{execution_time:.1f}s"
                }
            )
        
        # Cleanup
        if self.notifications_enabled:
            await notification_manager.shutdown()
        
        print(f"Symbol update complete: {len(current_symbols)} active, {removed_count} expired removed")

if __name__ == "__main__":
    updater = SymbolUpdater()
    asyncio.run(updater.run())