# Bybit Options Tracker - Comprehensive User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Installation Guide](#installation-guide)
4. [Configuration](#configuration)
5. [Using the Dashboard](#using-the-dashboard)
6. [API Documentation](#api-documentation)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

## Introduction

The Bybit Options Tracker is a real-time cryptocurrency options monitoring system that tracks BTC, ETH, and SOL options from Bybit exchange. It provides live data updates, comprehensive filtering, and detailed analytics through an intuitive web dashboard.

### Key Features
- **Real-time Data**: WebSocket connections for live options data
- **Multi-Asset Support**: Track BTC, ETH, and SOL options simultaneously
- **Smart Filtering**: Filter by expiry date, strike price, and option type
- **Greeks Display**: View Delta, Gamma, Theta, and Vega for each option
- **Performance Optimized**: Handles 2000+ options with minimal resource usage
- **Docker Containerized**: Easy deployment and scaling

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                     Bybit Exchange                       │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Options Tracker (Python)                    │
│  - Subscribes to 2000+ option symbols                    │
│  - Processes real-time ticker updates                    │
│  - Stores data in Redis with TTL                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Redis Database                          │
│  - In-memory storage for fast access                     │
│  - Hash structure for each option                        │
│  - 24-hour TTL for automatic cleanup                     │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┬──────────────┐
         ▼                       ▼              ▼
┌──────────────┐       ┌──────────────┐  ┌──────────────┐
│   Web App    │       │   Data API   │  │     Cron     │
│  (Port 5001) │       │  (Port 8000) │  │   Updater    │
└──────────────┘       └──────────────┘  └──────────────┘
```

### Docker Containers
1. **bybit-tracker**: WebSocket data collector
2. **bybit-redis**: Data storage
3. **bybit-webapp**: Web dashboard interface
4. **bybit-dataapi**: REST API endpoints
5. **bybit-cron**: Scheduled maintenance tasks

## Installation Guide

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- At least 2GB RAM available
- Ports 5001, 6380, and 8000 available

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/aftabjack/options-data-b.git
cd options-data-b
```

#### 2. Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Options to Track
OPTION_ASSETS=BTC,ETH,SOL

# WebSocket Settings
WS_SUBSCRIPTION_CHUNK_SIZE=10
WS_PING_INTERVAL=45
WS_PING_TIMEOUT=15

# Optional: Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

#### 3. Start the System
```bash
# Build and start all containers
docker-compose up -d

# Or use the provided script
./docker-start.sh
```

#### 4. Verify Installation
```bash
# Check container status
docker ps

# Check logs
docker logs bybit-tracker
docker logs bybit-webapp
```

#### 5. Access the Dashboard
Open your browser and navigate to: `http://localhost:5001`

## Configuration

### Modifying Tracked Assets
Edit `docker-compose.yml` to add or remove assets:
```yaml
environment:
  - OPTION_ASSETS=BTC,ETH,SOL,MATIC  # Add MATIC
```

### Adjusting Memory Usage
For low-memory systems, modify Redis configuration:
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### WebSocket Optimization
Adjust chunk size for stability vs speed:
```env
WS_SUBSCRIPTION_CHUNK_SIZE=10  # Lower = more stable
WS_SUBSCRIPTION_CHUNK_SIZE=50  # Higher = faster initial load
```

## Using the Dashboard

### Main Interface Components

#### 1. Asset Selector (Top Navigation)
- **BTC Button**: View Bitcoin options
- **ETH Button**: View Ethereum options  
- **SOL Button**: View Solana options
- Displays current index price and ATM strike

#### 2. Filter Controls
- **Expiry Dropdown**: Filter by expiration date
  - "All Expiries" shows everything
  - Dates sorted chronologically (2025 before 2026)
- **Type Filter**: Show Calls, Puts, or both
- **Search Box**: Find specific symbols or strikes

#### 3. Data Table Features

##### Column Descriptions:
- **Symbol**: Full option identifier (e.g., BTC-26DEC25-65000-C-USDT)
- **Type**: Call (green) or Put (red) badge
- **Strike**: Strike price in USD
- **Expiry**: Expiration date (DD-MMM-YY format)
- **Last**: Last traded price
- **Mark**: Mark price (fair value)
- **Volume**: 24-hour trading volume
- **OI**: Open Interest
- **Delta**: Price sensitivity (±0 to ±1)
- **Gamma**: Delta change rate
- **Theta**: Time decay (daily)
- **Vega**: Volatility sensitivity
- **IV**: Implied Volatility percentage
- **Underlying**: Current spot price

##### Table Controls:
- **Show Entries**: Display 10, 25, 50, 100, 250, 500, or All rows
- **Column Toggle**: Hide/show columns via settings
- **Sort**: Click any column header to sort
- **Pagination**: Navigate through pages at bottom

#### 4. Statistics Panel (Header)
- **Total Options**: Count of all tracked options
- **BTC/ETH/SOL Options**: Per-asset counts
- **Status Indicator**: Green = receiving data

### Common Use Cases

#### Finding At-The-Money Options
1. Look at the header for "ATM Strike" value
2. Use the search box to enter that strike price
3. View all options near the current spot price

#### Analyzing Specific Expiries
1. Click the Expiry dropdown
2. Select desired date (e.g., "26-DEC-25")
3. Table automatically filters to show only those options

#### Comparing Calls vs Puts
1. Use Type filter to select "Calls" or "Puts"
2. Sort by Volume to find most liquid options
3. Compare IV between calls and puts for skew analysis

#### Exporting Data
1. Select desired filters
2. Click "Show All" entries
3. Use browser print function to save as PDF
4. Or access API endpoint for JSON data

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### Get Options by Asset
```http
GET /api/options/{asset}
```
**Parameters:**
- `asset`: BTC, ETH, or SOL
- `expiry`: Optional - specific expiry or "all"
- `type`: Optional - "call", "put", or "all"
- `strike`: Optional - specific strike or "all"

**Example:**
```bash
curl http://localhost:8000/api/options/BTC?expiry=26DEC25&type=call
```

#### Get Available Expiries
```http
GET /api/expiries/{asset}
```
Returns list of available expiration dates for an asset.

#### Get Strike Prices
```http
GET /api/strikes/{asset}?expiry={expiry}
```
Returns available strikes for specific asset and expiry.

#### Get System Statistics
```http
GET /api/stats
```
Returns system metrics including option counts and memory usage.

#### Get Asset Summary
```http
GET /api/summary/{asset}
```
Returns detailed statistics for an asset including counts by type and expiry.

### Response Format
All endpoints return JSON:
```json
{
  "data": [...],
  "total": 814,
  "asset": "BTC"
}
```

## Monitoring & Maintenance

### Health Checks

#### Check System Status
```bash
# Container health
docker ps

# Redis memory usage
docker exec bybit-redis redis-cli info memory

# WebSocket connection status
docker logs bybit-tracker --tail 50
```

#### Monitor Resource Usage
```bash
# CPU and Memory per container
docker stats

# Disk usage
docker system df
```

### Regular Maintenance

#### Daily Tasks
1. Check logs for errors: `docker logs bybit-tracker --since 24h | grep ERROR`
2. Verify data freshness in dashboard
3. Monitor Redis memory usage

#### Weekly Tasks
1. Clear old logs: `docker-compose logs --tail 0`
2. Update symbol cache: Automatic via cron at 8:05 AM daily
3. Review error notifications if Telegram is configured

#### Monthly Tasks
1. Update Docker images: `docker-compose pull`
2. Clean unused Docker resources: `docker system prune`
3. Backup configuration files

### Scaling Considerations

#### Vertical Scaling
Increase container resources in docker-compose.yml:
```yaml
tracker:
  mem_limit: 512m
  cpus: 1.0
```

#### Horizontal Scaling
For high-availability:
1. Use Redis Cluster for data layer
2. Run multiple webapp instances with load balancer
3. Implement tracker failover mechanism

## Troubleshooting

### Common Issues and Solutions

#### WebSocket Connection Drops
**Symptoms:** Frequent "Connection to remote host was lost" errors

**Solutions:**
1. Reduce chunk size in options_tracker_production.py:
   ```python
   WS_SUBSCRIPTION_CHUNK_SIZE = 5  # Reduce from 10
   ```
2. Increase delays between subscriptions:
   ```python
   WS_SUBSCRIPTION_DELAY = 1.0  # Increase from 0.5
   ```
3. Restart tracker: `docker restart bybit-tracker`

#### No Data Showing in Dashboard
**Symptoms:** Empty tables, zero counts

**Checks:**
1. Verify Redis has data: `docker exec bybit-redis redis-cli dbsize`
2. Check tracker is running: `docker logs bybit-tracker --tail 100`
3. Verify webapp can connect to Redis: `docker logs bybit-webapp --tail 50`

**Solutions:**
1. Restart all services: `docker-compose restart`
2. Clear Redis and restart: 
   ```bash
   docker exec bybit-redis redis-cli FLUSHDB
   docker restart bybit-tracker
   ```

#### High Memory Usage
**Symptoms:** System slow, Redis using too much RAM

**Solutions:**
1. Reduce Redis memory limit in docker-compose.yml
2. Decrease data retention time in tracker:
   ```python
   pipe.expire(hash_key, 43200)  # 12 hours instead of 24
   ```
3. Track fewer symbols by limiting assets

#### Incorrect Expiry Dates Sorting
**Symptoms:** 2025 dates appearing after 2026 dates

**Solution:** Already fixed in latest version. Pull latest code:
```bash
git pull origin main
docker-compose build webapp
docker-compose up -d webapp
```

#### API Returns Empty Response
**Symptoms:** curl returns no data

**Checks:**
1. Verify port is correct (5001 for webapp, 8000 for API)
2. Check firewall settings
3. Verify container is running: `docker ps`

### Error Messages Guide

| Error | Meaning | Solution |
|-------|---------|----------|
| "Connection to remote host was lost" | WebSocket disconnected | Will auto-reconnect, check if persistent |
| "Redis connection failed" | Cannot connect to Redis | Check Redis container is running |
| "No symbols available" | Failed to fetch symbols | Check internet connection, Bybit API status |
| "JSONDecodeError" | Invalid API response | Check API endpoint URL and parameters |

### Getting Help

1. **Check Logs First:**
   ```bash
   docker-compose logs --tail 100
   ```

2. **System Information:**
   ```bash
   docker version
   docker-compose version
   git log --oneline -5
   ```

3. **Report Issues:**
   - GitHub Issues: https://github.com/aftabjack/options-data-b/issues
   - Include error messages, logs, and system info

## Advanced Features

### Custom Symbol Lists
Create custom symbol sets in `symbols_cache.json`:
```json
{
  "symbols": ["BTC-26DEC25-65000-C-USDT", ...],
  "custom_set": "high_volume_only"
}
```

### Data Export Automation
Use cron to export data periodically:
```bash
# Add to crontab
0 */6 * * * curl http://localhost:8000/api/options/BTC > /backup/btc_$(date +\%Y\%m\%d_\%H).json
```

### Performance Tuning
For systems with 8GB+ RAM:
```yaml
# docker-compose.yml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy volatile-lru
  
tracker:
  environment:
    - WS_SUBSCRIPTION_CHUNK_SIZE=50
    - BATCH_SIZE=200
```

## Security Considerations

1. **Network Security:**
   - Run behind reverse proxy (nginx/traefik) for production
   - Use SSL certificates for HTTPS
   - Restrict port access via firewall

2. **Data Security:**
   - Redis password protection for production
   - Regular backups of configuration
   - Monitor access logs

3. **API Rate Limiting:**
   - Implement rate limiting for public deployments
   - Use API keys for access control
   - Monitor for unusual activity patterns

---

*Last Updated: September 2025*
*Version: 2.0*