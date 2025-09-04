#!/usr/bin/env python3
"""
Production-Ready Bybit Options Tracker
Optimized for efficiency, stability, and Docker deployment
"""

import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import json
import logging
import os
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import redis
import requests
from pybit.unified_trading import WebSocket
from redis.exceptions import ConnectionError, TimeoutError, RedisError
from telegram_bot_notifier import bot_notifier as notification_manager


# ==================== CONFIGURATION ====================

class Config:
    """Centralized configuration with environment variable support"""
    
    # API Settings
    API_URL = os.getenv('BYBIT_API_URL', 'https://api.bybit.com/v5/market/instruments-info')
    API_KEY = os.getenv('BYBIT_API_KEY', '')
    API_SECRET = os.getenv('BYBIT_API_SECRET', '')
    TESTNET = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
    API_RETRY_COUNT = int(os.getenv('API_RETRY_COUNT', '3'))
    API_RETRY_DELAY = float(os.getenv('API_RETRY_DELAY', '1.0'))
    
    # Redis Settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
    REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
    REDIS_CONNECTION_POOL_MAX = int(os.getenv('REDIS_POOL_MAX', '50'))
    REDIS_RETRY_ON_TIMEOUT = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
    
    # WebSocket Settings - OPTIMIZED
    WS_PING_INTERVAL = int(os.getenv('WS_PING_INTERVAL', '45'))  # Increased from 30
    WS_PING_TIMEOUT = int(os.getenv('WS_PING_TIMEOUT', '15'))   # Increased from 10
    WS_RECONNECT_DELAY = int(os.getenv('WS_RECONNECT_DELAY', '10'))  # Increased from 5
    WS_MAX_RECONNECT_ATTEMPTS = int(os.getenv('WS_MAX_RECONNECT_ATTEMPTS', '10'))
    WS_SUBSCRIPTION_CHUNK_SIZE = int(os.getenv('WS_SUBSCRIPTION_CHUNK_SIZE', '100'))  # Increased from 50
    WS_SUBSCRIPTION_DELAY = float(os.getenv('WS_SUBSCRIPTION_DELAY', '0.5'))  # Increased from 0.2
    
    # Cache Settings
    CACHE_FILE = os.getenv('CACHE_FILE', 'symbols_cache.json')
    CACHE_DURATION_HOURS = int(os.getenv('CACHE_DURATION_HOURS', '24'))
    KNOWN_OPTION_ASSETS = os.getenv('OPTION_ASSETS', 'BTC,ETH,SOL').split(',')
    
    # Performance Settings - OPTIMIZED FOR LOWER MEMORY
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))  # Reduced for memory
    BATCH_TIMEOUT = float(os.getenv('BATCH_TIMEOUT', '1.0'))  # Faster writes
    WRITE_QUEUE_SIZE = int(os.getenv('WRITE_QUEUE_SIZE', '2000'))  # Reduced from 5000
    STATS_INTERVAL = int(os.getenv('STATS_INTERVAL', '60'))  # Increased from 30
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Health Check
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
    ENABLE_HEALTH_CHECK = os.getenv('ENABLE_HEALTH_CHECK', 'true').lower() == 'true'
    
    # Telegram Notifications
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'


# ==================== LOGGING SETUP ====================

# Minimal logging - only errors and critical messages
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ==================== OPTIMIZED TRACKER ====================

class ProductionOptionsTracker:
    def __init__(self):
        self.config = Config()
        self.redis_pool = None
        self.redis_client = None
        self.ws = None
        self.running = False
        self.ping_thread = None
        self.write_queue = deque(maxlen=Config.WRITE_QUEUE_SIZE)
        self.batch_writer_task = None
        self.health_server_task = None
        self.reconnect_count = 0
        self.notifications_enabled = Config.ENABLE_NOTIFICATIONS
        
        # Performance metrics
        self.metrics = {
            'messages_received': 0,
            'messages_processed': 0,
            'messages_dropped': 0,
            'redis_writes': 0,
            'redis_errors': 0,
            'ws_reconnects': 0,
            'last_message_time': None,
            'last_ping_time': None,
            'start_time': datetime.now()
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        # Graceful shutdown initiated
        self.running = False
    
    # ==================== REDIS OPTIMIZATION ====================
    
    def init_redis(self) -> bool:
        """Initialize Redis with connection pooling and retry logic"""
        try:
            # Create connection pool for better performance
            self.redis_pool = redis.ConnectionPool(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                max_connections=Config.REDIS_CONNECTION_POOL_MAX,
                socket_timeout=Config.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=Config.REDIS_SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=Config.REDIS_RETRY_ON_TIMEOUT,
                decode_responses=True
            )
            
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Test connection
            self.redis_client.ping()
            return True
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection failed: {e}")
            if self.notifications_enabled:
                asyncio.create_task(notification_manager.redis_critical(str(e)))
            return False
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            if self.notifications_enabled:
                asyncio.create_task(notification_manager.redis_critical(
                    f"Unexpected error: {e}"
                ))
            return False
    
    def clear_database(self):
        """Clear Redis database with safety check"""
        try:
            clear_on_start = os.getenv('CLEAR_DB_ON_START', 'false').lower() == 'true'
            allow_clear = os.getenv('ALLOW_DB_CLEAR', 'true').lower() == 'true'
            
            if clear_on_start and allow_clear:
                self.redis_client.flushdb()
        except RedisError as e:
            logger.error(f"Failed to clear database: {e}")
    
    async def batch_writer(self):
        """Optimized batch writer with pipelining"""
        pipeline_batch = []
        last_write = time.time()
        
        while self.running:
            try:
                # Collect items for batch
                while len(pipeline_batch) < Config.BATCH_SIZE:
                    if self.write_queue:
                        pipeline_batch.append(self.write_queue.popleft())
                    else:
                        break
                
                # Write batch if we have data or timeout reached
                if pipeline_batch and (
                    len(pipeline_batch) >= Config.BATCH_SIZE or 
                    time.time() - last_write > Config.BATCH_TIMEOUT
                ):
                    await self._write_batch_with_pipeline(pipeline_batch)
                    pipeline_batch = []
                    last_write = time.time()
                
                await asyncio.sleep(0.01)  # Small sleep to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Batch writer error: {e}")
                self.metrics['redis_errors'] += 1
                if self.notifications_enabled and self.metrics['redis_errors'] % 10 == 0:
                    await notification_manager.send_critical(
                        "BatchWriter", 
                        f"Multiple batch write failures: {self.metrics['redis_errors']} errors",
                        {"Last Error": str(e)}
                    )
                await asyncio.sleep(1)
    
    async def _write_batch_with_pipeline(self, batch: List[Dict]):
        """Write batch using Redis pipeline for efficiency"""
        try:
            pipe = self.redis_client.pipeline(transaction=False)
            
            for item in batch:
                symbol = item.get('symbol')
                if not symbol:
                    continue
                
                hash_key = f"option:{symbol}"
                
                # Use HSET for main data (including symbol field)
                pipe.hset(hash_key, mapping={
                    k: str(v) if v is not None else ""
                    for k, v in item.items()
                })
                
                # Set TTL
                pipe.expire(hash_key, 86400)
                
                # Skip time series storage to save memory (not used anywhere)
                # Previously stored 100 entries per symbol = high memory usage
            
            # Update global stats
            pipe.hincrby("stats:global", "messages", len(batch))
            pipe.hset("stats:global", "last_update", str(time.time()))
            
            # Execute pipeline
            pipe.execute()
            
            self.metrics['redis_writes'] += len(batch)
            self.metrics['messages_processed'] += len(batch)
            
        except RedisError as e:
            logger.error(f"Redis pipeline error: {e}")
            self.metrics['redis_errors'] += 1
            if self.notifications_enabled and self.metrics['redis_errors'] % 10 == 0:
                await notification_manager.send_critical(
                    "Redis Pipeline",
                    f"Pipeline write failures: {self.metrics['redis_errors']} total errors",
                    {"Error": str(e), "Batch Size": len(batch)}
                )
        except Exception as e:
            logger.error(f"Unexpected pipeline error: {e}")
    
    # ==================== WEBSOCKET OPTIMIZATION ====================
    
    def handle_message(self, message):
        """Optimized message handler with minimal processing"""
        try:
            self.metrics['messages_received'] += 1
            self.metrics['last_message_time'] = datetime.now()
            
            # Handle pong messages
            if message.get("op") == "pong":
                pass  # Pong received
                return
            
            data = message.get("data")
            if not data:
                return
            
            symbol = data.get('symbol')
            if not symbol:
                return
            
            # Prepare minimal data structure
            record = {
                'symbol': symbol,
                'timestamp': time.time(),
                'bid_iv': self._fast_float(data.get('bidIv')),
                'ask_iv': self._fast_float(data.get('askIv')),
                'last_price': self._fast_float(data.get('lastPrice')),
                'mark_price': self._fast_float(data.get('markPrice')),
                'index_price': self._fast_float(data.get('indexPrice')),
                'mark_iv': self._fast_float(data.get('markPriceIv')),
                'underlying_price': self._fast_float(data.get('underlyingPrice')),
                'open_interest': self._fast_float(data.get('openInterest')),
                'delta': self._fast_float(data.get('delta')),
                'gamma': self._fast_float(data.get('gamma')),
                'vega': self._fast_float(data.get('vega')),
                'theta': self._fast_float(data.get('theta')),
                'volume_24h': self._fast_float(data.get('volume24h')),
                'turnover_24h': self._fast_float(data.get('turnover24h')),
            }
            
            # Add to queue (non-blocking)
            if len(self.write_queue) < Config.WRITE_QUEUE_SIZE:
                self.write_queue.append(record)
            else:
                self.metrics['messages_dropped'] += 1
                if self.metrics['messages_dropped'] % 1000 == 0:
                    logger.warning(f"Queue full, dropped {self.metrics['messages_dropped']} messages")
            
        except Exception as e:
            if self.metrics['messages_received'] % 10000 == 0:
                logger.error(f"Message handler error: {e}")
    
    def _fast_float(self, value):
        """Fast float conversion without exception handling in hot path"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def ping_keeper(self):
        """Dedicated thread for WebSocket ping/pong"""
        while self.running:
            try:
                if self.ws and self.ws.ws and self.ws.ws.sock:
                    # Send ping message
                    ping_msg = json.dumps({
                        "op": "ping",
                        "req_id": str(int(time.time() * 1000))
                    })
                    self.ws.ws.send(ping_msg)
                    self.metrics['last_ping_time'] = datetime.now()
                    pass  # Ping sent
                
                time.sleep(Config.WS_PING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Ping error: {e}")
                time.sleep(Config.WS_PING_INTERVAL)
    
    async def subscribe_with_retry(self, symbols: List[str]):
        """Subscribe to symbols with automatic retry on failure"""
        max_attempts = Config.WS_MAX_RECONNECT_ATTEMPTS
        attempt = 0
        
        while attempt < max_attempts and self.running:
            try:
                attempt += 1
                if attempt > 1:  # Only log retries
                    print(f"Reconnection attempt {attempt}/{max_attempts}")
                
                # Initialize WebSocket (uses Config.TESTNET from .env)
                self.ws = WebSocket(
                    testnet=Config.TESTNET,
                    channel_type="option",
                    ping_interval=Config.WS_PING_INTERVAL,
                    ping_timeout=Config.WS_PING_TIMEOUT
                )
                
                # Subscribe in chunks
                chunks = [symbols[i:i + Config.WS_SUBSCRIPTION_CHUNK_SIZE] 
                         for i in range(0, len(symbols), Config.WS_SUBSCRIPTION_CHUNK_SIZE)]
                
                for i, chunk in enumerate(chunks):
                    if not self.running:
                        break
                        
                    self.ws.ticker_stream(
                        symbol=chunk,
                        callback=self.handle_message
                    )
                    pass  # Batch subscribed
                    await asyncio.sleep(Config.WS_SUBSCRIPTION_DELAY)
                
                # Start ping thread
                if not self.ping_thread or not self.ping_thread.is_alive():
                    self.ping_thread = threading.Thread(target=self.ping_keeper, daemon=True)
                    self.ping_thread.start()
                    pass  # Ping thread started
                
                self.reconnect_count = 0
                return True  # Success
                return True
                
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                self.metrics['ws_reconnects'] += 1
                
                if attempt < max_attempts:
                    delay = Config.WS_RECONNECT_DELAY * attempt
                    await asyncio.sleep(delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max reconnection attempts reached")
                    return False
    
    # ==================== SYMBOL MANAGEMENT ====================
    
    def fetch_symbols_with_retry(self) -> List[str]:
        """Fetch symbols with retry logic"""
        for attempt in range(Config.API_RETRY_COUNT):
            try:
                return self._fetch_symbols()
            except Exception as e:
                logger.error(f"Symbol fetch attempt {attempt + 1} failed: {e}")
                if attempt < Config.API_RETRY_COUNT - 1:
                    time.sleep(Config.API_RETRY_DELAY * (attempt + 1))
        
        logger.error("Failed to fetch symbols after all retries")
        return []
    
    def _fetch_symbols(self) -> List[str]:
        """Internal symbol fetching"""
        all_symbols = []
        
        for coin in Config.KNOWN_OPTION_ASSETS:
            cursor = None
            
            while True:
                params = {
                    "category": "option",
                    "baseCoin": coin,
                    "limit": 1000
                }
                if cursor:
                    params["cursor"] = cursor
                
                # Prepare headers (add authentication if credentials are provided)
                headers = {}
                if Config.API_KEY and Config.API_SECRET:
                    # Note: For public endpoints, authentication is not required
                    # This is here for future use with private endpoints
                    headers['X-BAPI-API-KEY'] = Config.API_KEY
                
                response = requests.get(
                    Config.API_URL,
                    params=params,
                    headers=headers,
                    timeout=Config.API_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get("retCode") != 0:
                    pass  # API error, continue
                    break
                
                items = data.get("result", {}).get("list", [])
                if not items:
                    break
                
                symbols = [
                    item["symbol"]
                    for item in items
                    if item.get("status") == "Trading"
                ]
                all_symbols.extend(symbols)
                
                cursor = data.get("result", {}).get("nextPageCursor")
                if not cursor:
                    break
            
            # Fetched coin options
        
        return all_symbols
    
    def load_or_fetch_symbols(self) -> List[str]:
        """Load symbols from cache or fetch if needed"""
        cache_path = Path(Config.CACHE_FILE)
        
        # Try to load from cache
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                
                expires_at = datetime.fromisoformat(cache_data['expires_at'])
                if datetime.now() < expires_at:
                    # Loaded from cache
                    return cache_data['symbols']
                else:
                    pass  # Cache expired
            except Exception as e:
                pass  # Cache error
        
        # Fetch fresh symbols
        symbols = self.fetch_symbols_with_retry()
        
        if symbols:
            # Save to cache
            cache_data = {
                'symbols': symbols,
                'count': len(symbols),
                'updated_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=Config.CACHE_DURATION_HOURS)).isoformat(),
                'by_asset': {
                    asset: len([s for s in symbols if s.startswith(f"{asset}-")])
                    for asset in Config.KNOWN_OPTION_ASSETS
                }
            }
            
            try:
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                pass  # Cache saved
            except Exception as e:
                logger.error(f"Cache write error: {e}")
        
        return symbols
    
    # ==================== HEALTH CHECK ====================
    
    async def health_check_server(self):
        """Simple HTTP health check endpoint for Docker/K8s"""
        if not Config.ENABLE_HEALTH_CHECK:
            return
        
        from aiohttp import web
        
        async def health(request):
            """Health check endpoint"""
            status = "healthy"
            details = {
                "status": status,
                "uptime": str(datetime.now() - self.metrics['start_time']),
                "messages_received": self.metrics['messages_received'],
                "messages_processed": self.metrics['messages_processed'],
                "messages_dropped": self.metrics['messages_dropped'],
                "redis_errors": self.metrics['redis_errors'],
                "ws_reconnects": self.metrics['ws_reconnects'],
                "last_message": str(self.metrics['last_message_time']) if self.metrics['last_message_time'] else "None",
                "queue_size": len(self.write_queue)
            }
            
            # Check if we're receiving data
            if self.metrics['last_message_time']:
                time_since_last = (datetime.now() - self.metrics['last_message_time']).seconds
                if time_since_last > 60:
                    status = "unhealthy"
                    details["status"] = status
                    details["error"] = f"No messages for {time_since_last} seconds"
            
            return web.json_response(details, status=200 if status == "healthy" else 503)
        
        app = web.Application()
        app.router.add_get('/health', health)
        app.router.add_get('/ready', health)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', Config.HEALTH_CHECK_PORT)
        await site.start()
        
        print(f"Health check on port {Config.HEALTH_CHECK_PORT}")
    
    # ==================== MAIN EXECUTION ====================
    
    async def run(self):
        """Main execution loop with all optimizations"""
        print("Bybit Options Tracker started")
        
        # Notifications are initialized automatically with bot notifier
        if self.notifications_enabled:
            pass  # Bot notifier is ready
        
        # Initialize Redis
        if not self.init_redis():
            logger.error("Failed to initialize Redis. Exiting.")
            return
        
        # Clear database if needed
        self.clear_database()
        
        # Load symbols
        symbols = self.load_or_fetch_symbols()
        if not symbols:
            logger.error("No symbols available. Exiting.")
            return
        
        print(f"Tracking {len(symbols)} symbols")
        
        self.running = True
        
        # Start background tasks
        self.batch_writer_task = asyncio.create_task(self.batch_writer())
        
        # Start health check server
        if Config.ENABLE_HEALTH_CHECK:
            self.health_server_task = asyncio.create_task(self.health_check_server())
        
        # Subscribe to WebSocket with retry
        success = await self.subscribe_with_retry(symbols)
        if not success:
            logger.error("Failed to establish WebSocket connection")
            if self.notifications_enabled:
                await notification_manager.websocket_critical(
                    f"Failed to establish initial connection for {len(symbols)} symbols"
                )
            self.running = False
            return
        
        # Main monitoring loop
        last_stats_time = time.time()
        
        while self.running:
            try:
                await asyncio.sleep(1)
                
                # Print stats periodically
                if time.time() - last_stats_time > Config.STATS_INTERVAL:
                    self.print_stats()
                    last_stats_time = time.time()
                
                # Check WebSocket health
                if self.metrics['last_message_time']:
                    time_since_last = (datetime.now() - self.metrics['last_message_time']).seconds
                    if time_since_last > 60:
                        # Silently attempt reconnect
                        if self.notifications_enabled and time_since_last > 120:
                            await notification_manager.websocket_critical(
                                f"No data for {time_since_last} seconds"
                            )
                        await self.subscribe_with_retry(symbols)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(5)
        
        # Cleanup
        await self.cleanup()
    
    def print_stats(self):
        """Print minimal performance statistics"""
        if self.metrics['messages_received'] % 10000 == 0:  # Only print every 10k messages
            print(f"Stats: {self.metrics['messages_received']:,} received, "
                  f"{self.metrics['messages_processed']:,} processed, "
                  f"Queue: {len(self.write_queue)}/{Config.WRITE_QUEUE_SIZE}")
    
    async def cleanup(self):
        """Graceful cleanup"""
        print("Shutting down...")
        
        self.running = False
        
        # No shutdown notification (not critical)
        pass
        
        # Process remaining queue items silently
        remaining = list(self.write_queue)
        if remaining:
            await self._write_batch_with_pipeline(remaining)
        
        # Cancel tasks
        if self.batch_writer_task:
            self.batch_writer_task.cancel()
        
        if self.health_server_task:
            self.health_server_task.cancel()
        
        # Close WebSocket
        if self.ws:
            try:
                self.ws.exit()
                pass  # WebSocket closed
            except:
                pass
        
        # Close Redis
        if self.redis_pool:
            self.redis_pool.disconnect()
            pass  # Redis closed
        
        # Final stats
        self.print_stats()
        print("Shutdown complete")


# ==================== ENTRY POINT ====================

def main():
    """Main entry point with mode selection"""
    
    # Parse command-line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "track"
    
    if mode in ['--help', '-h']:
        print("Usage: python options_tracker_production.py [mode]")
        print("\nModes:")
        print("  fetch    - Fetch symbols and update cache")
        print("  track    - Run the tracker (default)")
        print("  test     - Test connections and exit")
        print("\nEnvironment variables:")
        print("  REDIS_HOST, REDIS_PORT, REDIS_PASSWORD")
        print("  WS_PING_INTERVAL, WS_RECONNECT_DELAY")
        print("  LOG_LEVEL, HEALTH_CHECK_PORT")
        return
    
    tracker = ProductionOptionsTracker()
    
    if mode == 'fetch':
        # Just fetch and cache symbols
        print("Fetching symbols...")
        symbols = tracker.fetch_symbols_with_retry()
        if symbols:
            print(f"Fetched {len(symbols)} symbols")
        else:
            logger.error("Failed to fetch symbols")
            sys.exit(1)
    
    elif mode == 'test':
        # Test connections
        print("Testing connections...")
        
        # Test Redis
        if tracker.init_redis():
            print("✓ Redis OK")
        else:
            logger.error("✗ Redis connection failed")
            sys.exit(1)
        
        # Test API
        symbols = tracker.fetch_symbols_with_retry()
        if symbols:
            print(f"✓ API OK ({len(symbols)} symbols)")
        else:
            logger.error("✗ API connection failed")
            sys.exit(1)
        
        print("✓ All tests passed")
    
    else:
        # Run the tracker
        try:
            asyncio.run(tracker.run())
        except KeyboardInterrupt:
            print("\nInterrupted")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()