# Memory Usage Comparison

## Full Setup (Current) - 230 MB Total
```
Service     | Memory  | Purpose                        | Can Disable?
------------|---------|--------------------------------|-------------
Tracker     | 39 MB   | WebSocket listener             | ❌ Required
Redis       | 27 MB   | Data storage                   | ❌ Required  
WebApp      | 95 MB   | Web dashboard                  | ✅ Yes
DataAPI     | 68 MB   | REST API                       | ✅ Yes
Cron        | <1 MB   | Symbol updater                 | ✅ Yes
------------|---------|--------------------------------|-------------
TOTAL       | 230 MB  |                                |
```

## Minimal Setup (docker-compose.minimal.yml) - 90 MB Total
```
Service     | Memory  | Purpose                        | Features Lost
------------|---------|--------------------------------|---------------
Tracker     | 50 MB   | WebSocket only                 | No web UI, API
Redis       | 40 MB   | Live data only                 | No persistence
------------|---------|--------------------------------|---------------
TOTAL       | 90 MB   |                                | -61% memory
```

## Ultra-Minimal (options_tracker_minimal.py) - 50 MB Total
```
Service     | Memory  | Purpose                        | Features Lost
------------|---------|--------------------------------|---------------
Tracker     | 30 MB   | Bare minimum Python            | No batching optimization
Redis       | 20 MB   | Latest packet only             | No history at all
------------|---------|--------------------------------|---------------
TOTAL       | 50 MB   |                                | -78% memory
```

## What Each Setup Provides:

### Full Setup (230 MB)
✅ Web Dashboard at http://localhost:5001
✅ REST API at http://localhost:8000
✅ Historical data (24 hours)
✅ Telegram notifications
✅ Symbol auto-updates
✅ Health checks
✅ Full monitoring

### Minimal Setup (90 MB)
✅ Live WebSocket feed
✅ Latest data in Redis
✅ Telegram critical alerts
❌ No web interface
❌ No REST API
❌ No historical data
❌ No symbol updates

### Ultra-Minimal (50 MB)
✅ Pure live feed
✅ Latest packet only
❌ Nothing else

## Redis Storage Comparison:

### Full Setup
- Stores: All option fields (15+ fields)
- History: None (after optimization)
- Keys: ~2100 options
- Memory: 20-30 MB

### Minimal Setup  
- Stores: Essential fields (8 fields)
- History: None
- Keys: ~2100 options
- Memory: 10-15 MB

### Ultra-Minimal
- Stores: Critical fields (5-6 fields)
- History: None (latest only)
- Keys: ~2100 options
- Memory: 5-10 MB

## How to Run Each:

### Full Setup (current)
```bash
docker-compose up -d
```

### Minimal Setup
```bash
docker-compose -f docker-compose.minimal.yml up -d
```

### Ultra-Minimal
```bash
# Just Python + Redis
redis-server --maxmemory 50mb --maxmemory-policy allkeys-lru &
python3 options_tracker_minimal.py
```