#!/usr/bin/env python3
"""
Ultra-Minimal Bybit Options Tracker
- Live data only (no history)
- Latest packet replaces previous
- Minimal memory usage
"""

import asyncio
import os
import redis
import time
import signal
from pybit.unified_trading import WebSocket
from dotenv import load_dotenv

load_dotenv()

class MinimalTracker:
    def __init__(self):
        # Redis connection (minimal)
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_keepalive=True
        )
        
        # WebSocket
        self.ws = None
        self.running = True
        self.message_count = 0
        
        # Batch writing for efficiency
        self.batch = {}
        self.last_write = time.time()
        self.batch_timeout = 0.5  # Write every 0.5 seconds
        
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        self.running = False
    
    def handle_message(self, message):
        """Handle incoming WebSocket message - minimal processing"""
        if message.get("op") == "pong":
            return
        
        data = message.get("data")
        if not data:
            return
        
        symbol = data.get('symbol')
        if not symbol:
            return
        
        # Store minimal data (latest only)
        self.batch[symbol] = {
            'symbol': symbol,
            'last': data.get('lastPrice', 0),
            'mark': data.get('markPrice', 0),
            'iv': data.get('markPriceIv', 0),
            'bid': data.get('bidPrice', 0),
            'ask': data.get('askPrice', 0),
            'vol': data.get('volume24h', 0),
            'oi': data.get('openInterest', 0),
            'ts': time.time()
        }
        
        self.message_count += 1
        
        # Write batch if timeout reached
        if time.time() - self.last_write > self.batch_timeout:
            self.write_batch()
    
    def write_batch(self):
        """Write batch to Redis - replaces old data"""
        if not self.batch:
            return
        
        pipe = self.redis_client.pipeline()
        
        for symbol, data in self.batch.items():
            # Single hash per option - no history
            key = f"opt:{symbol}"
            pipe.hset(key, mapping=data)
            pipe.expire(key, 3600)  # 1 hour expiry
        
        # Update stats
        pipe.hset("stats", "count", self.message_count)
        pipe.hset("stats", "updated", time.time())
        
        pipe.execute()
        self.batch = {}
        self.last_write = time.time()
    
    async def run(self):
        """Main run loop - minimal setup"""
        print("Minimal Options Tracker starting...")
        
        # Test Redis
        try:
            self.redis_client.ping()
            print("✓ Redis connected")
        except:
            print("✗ Redis connection failed")
            return
        
        # Clear old data
        self.redis_client.flushdb()
        print("✓ Database cleared")
        
        # Get symbols (simplified)
        symbols = self.get_symbols()
        print(f"✓ Tracking {len(symbols)} symbols")
        
        # Connect WebSocket
        self.ws = WebSocket(
            testnet=False,
            channel_type="option",
            ping_interval=30,
            ping_timeout=10
        )
        
        # Subscribe in chunks
        for i in range(0, len(symbols), 50):
            chunk = symbols[i:i+50]
            self.ws.ticker_stream(
                symbol=chunk,
                callback=self.handle_message
            )
            await asyncio.sleep(0.2)
        
        print("✓ WebSocket connected")
        print(f"\nLive feed active - Memory usage: ~50-80 MB")
        print("Press Ctrl+C to stop\n")
        
        # Main loop
        while self.running:
            await asyncio.sleep(1)
            
            # Periodic batch write
            if time.time() - self.last_write > self.batch_timeout:
                self.write_batch()
            
            # Print stats every 30 seconds
            if self.message_count % 1000 == 0:
                print(f"Messages: {self.message_count:,} | Redis keys: {self.redis_client.dbsize()}")
        
        # Cleanup
        print("\nShutting down...")
        if self.ws:
            self.ws.exit()
        print("Done")
    
    def get_symbols(self):
        """Get option symbols - simplified"""
        import requests
        
        symbols = []
        for asset in ['BTC', 'ETH', 'SOL']:
            try:
                resp = requests.get(
                    'https://api.bybit.com/v5/market/instruments-info',
                    params={'category': 'option', 'baseCoin': asset, 'limit': 1000},
                    timeout=10
                )
                data = resp.json()
                items = data.get('result', {}).get('list', [])
                symbols.extend([
                    item['symbol'] for item in items 
                    if item.get('status') == 'Trading'
                ])
            except:
                pass
        
        return symbols


if __name__ == "__main__":
    tracker = MinimalTracker()
    asyncio.run(tracker.run())