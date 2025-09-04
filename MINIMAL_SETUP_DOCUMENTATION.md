# Minimal Setup Documentation
**Date**: December 4, 2024
**Purpose**: Document transition from full setup to minimal live-feed-only configuration

## 1. BASELINE - Before Changes

### Current Setup Status
**Time**: Starting documentation
**Configuration**: Full docker-compose.yml with all services

### Services Running:
```
- bybit-tracker   (WebSocket listener)
- bybit-redis     (Data storage)
- bybit-webapp    (Web dashboard)
- bybit-dataapi   (REST API)
- bybit-cron      (Symbol updater)
```

### Memory Usage - BEFORE:
**Time**: December 4, 2024, 15:01:59 IST

```
Container      | Memory Usage  | CPU %   | Purpose
---------------|---------------|---------|------------------
bybit-tracker  | 48.62 MB      | 55.95%  | WebSocket listener
bybit-redis    | 26.70 MB      | 2.27%   | Data storage
bybit-cron     | 0.80 MB       | 0.01%   | Symbol updater
bybit-webapp   | 95.00 MB      | 0.11%   | Web dashboard
bybit-dataapi  | 67.89 MB      | 0.06%   | REST API
---------------|---------------|---------|------------------
TOTAL          | 239.01 MB     |         | 5 containers
```

### Redis Data - BEFORE:
- **Total Keys**: 2,113
- **Data Type**: option:* (individual option contracts)
- **Expiry**: 24 hours TTL on all keys
- **Storage**: Full option data with all fields

---

## 2. TRANSITION TO MINIMAL

### Actions Taken:
1. **Stopped** full docker-compose setup (5 containers)
2. **Started** docker-compose.minimal.yml (2 containers only)
3. **Removed** services: webapp, dataapi, cron

### Configuration Changes:
- Redis memory limit: 512MB → 64MB
- Redis persistence: Disabled (RAM only)
- Tracker memory limit: 256MB → 128MB
- Write queue: 5000 → 500
- Batch size: 200 → 50

---

## 3. RESULTS - After Minimal Setup

### Memory Usage - AFTER:
**Time**: December 4, 2024, 15:04:15 IST

```
Container              | Memory Usage  | Limit   | CPU %   | Status
-----------------------|---------------|---------|---------|----------
bybit-tracker-minimal  | 43.82 MB      | 128 MB  | 48.60%  | Running
bybit-redis-minimal    | 10.56 MB      | 64 MB   | 2.06%   | Running
-----------------------|---------------|---------|---------|----------
TOTAL                  | 54.38 MB      |         |         | 2 containers
```

### Redis Data - AFTER:
- **Total Keys**: 2,113 (same as before)
- **Memory Used**: 2.19 MB (was ~20 MB before)
- **Data Type**: option:* (same structure)
- **Persistence**: NONE (RAM only)

---

## 4. COMPARISON

### Memory Reduction:
```
Component      | Before    | After     | Savings
---------------|-----------|-----------|----------
Total Memory   | 239.01 MB | 54.38 MB  | -77.2%
Containers     | 5         | 2         | -60%
Redis Memory   | 26.70 MB  | 10.56 MB  | -60.4%
Tracker Memory | 48.62 MB  | 43.82 MB  | -9.9%
```

### Features Lost:
- ❌ Web Dashboard (http://localhost:5001)
- ❌ REST API (http://localhost:8000)
- ❌ Symbol auto-updates (cron)
- ❌ Data persistence (Redis in RAM only)
- ❌ Historical data storage

### Features Retained:
- ✅ Live WebSocket feed from Bybit
- ✅ Latest option data in Redis
- ✅ All 2100+ option symbols tracked
- ✅ Real-time updates
- ✅ Telegram notifications (if configured)

---

## 5. OBSERVATIONS

### Positive:
1. **77% memory reduction** achieved
2. Redis using only 2.19 MB for actual data
3. System still tracking all 2100+ options
4. WebSocket connection maintained

### Issues Noticed:
1. WebSocket reconnection messages in logs (normal behavior)
2. CPU usage initially high during startup (stabilizes)

### Performance:
- **Startup time**: ~10 seconds
- **Data freshness**: Real-time (no delay)
- **Update frequency**: Same as before

---

## 6. HOW TO USE MINIMAL SETUP

### Starting the Minimal Setup:
```bash
# Start minimal containers
docker-compose -f docker-compose.minimal.yml up -d

# Check status
docker ps

# View logs
docker logs bybit-tracker-minimal -f
```

### Accessing Data (No Web UI):
```bash
# Check total keys
docker exec bybit-redis-minimal redis-cli DBSIZE

# Get specific option data
docker exec bybit-redis-minimal redis-cli hgetall "option:BTC-5SEP25-60000-C"

# List all BTC options
docker exec bybit-redis-minimal redis-cli --scan --pattern "option:BTC-*"

# Get latest price for an option
docker exec bybit-redis-minimal redis-cli hget "option:BTC-5SEP25-60000-C" mark_price

# Monitor real-time updates
docker exec bybit-redis-minimal redis-cli monitor
```

### Python Access Example:
```python
import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6380, decode_responses=True)

# Get option data
data = r.hgetall("option:BTC-5SEP25-60000-C")
print(f"Mark Price: {data['mark_price']}")
print(f"IV: {data['mark_iv']}")
print(f"Volume: {data['volume_24h']}")

# Get all BTC options
for key in r.scan_iter("option:BTC-*"):
    option_data = r.hgetall(key)
    print(f"{key}: ${option_data['mark_price']}")
```

### Stopping:
```bash
docker-compose -f docker-compose.minimal.yml down
```

---

## 7. SUMMARY

### What Changed:
- **Memory**: 239 MB → 54 MB (-77%)
- **Containers**: 5 → 2 (-60%)
- **Features**: Removed web UI, API, persistence
- **Purpose**: Pure live feed only

### Use Cases:
- ✅ **Minimal Setup**: When you only need live data feed
- ✅ **Full Setup**: When you need web UI, API, persistence

### Recommendation:
The minimal setup is perfect for:
- Algorithmic trading systems
- Data collection scripts
- Low-resource environments
- Headless servers

Use the full setup when you need:
- Visual monitoring
- REST API access  
- Data persistence
- Manual trading