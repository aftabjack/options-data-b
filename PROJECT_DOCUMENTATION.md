# Bybit Options Tracker - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Features Implemented](#features-implemented)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [API Endpoints](#api-endpoints)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Enhancements Made](#enhancements-made)
10. [Performance Optimizations](#performance-optimizations)
11. [Future Improvements](#future-improvements)

---

## Project Overview

### Purpose
A real-time options data tracking system for Bybit cryptocurrency options, providing live market data, Greeks calculations, and a web-based dashboard for monitoring and analysis.

### Key Capabilities
- Real-time WebSocket connection to Bybit options market
- Redis-based data storage for high-performance access
- FastAPI web application with responsive dashboard
- Docker support for containerized deployment
- Telegram notifications for alerts
- Column visibility customization
- GUI configuration system

### Technology Stack
- **Backend**: Python 3.9+
- **WebSocket**: pybit library for Bybit API
- **Database**: Redis (in-memory data store)
- **Web Framework**: FastAPI
- **Frontend**: Bootstrap 5, jQuery, DataTables
- **Containerization**: Docker & Docker Compose
- **Notifications**: Telegram (telethon)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Bybit Exchange                        │
│                    (WebSocket API)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Options Tracker (Python)                      │
│  - WebSocket client (pybit)                             │
│  - Data processing & batching                           │
│  - Error recovery & reconnection                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Redis Database                          │
│  - In-memory storage                                    │
│  - Key-value structure                                  │
│  - TTL management                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│             FastAPI Web Application                      │
│  - REST API endpoints                                   │
│  - Server-sent events (SSE)                            │
│  - Static file serving                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Web Dashboard (HTML/JS)                     │
│  - Real-time data display                              │
│  - Column visibility controls                           │
│  - Filtering & sorting                                  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Data Collection**: WebSocket receives real-time options data from Bybit
2. **Processing**: Data is parsed, validated, and formatted
3. **Storage**: Processed data stored in Redis with appropriate TTL
4. **API Access**: FastAPI reads from Redis and serves to frontend
5. **Display**: Dashboard renders data with real-time updates

---

## Core Components

### 1. Options Tracker (`options_tracker_production.py`)
**Purpose**: Main data collection service

**Key Features**:
- WebSocket connection management
- Automatic reconnection with exponential backoff
- Batch processing for efficiency
- Symbol management (BTC, ETH, SOL options)
- Error recovery mechanisms
- Statistics tracking

**Configuration**:
```python
BATCH_SIZE = 200
BATCH_TIMEOUT = 2.0
WS_PING_INTERVAL = 45
WS_PING_TIMEOUT = 15
MAX_RECONNECT_ATTEMPTS = 10
```

### 2. Web Application (`webapp/app_fastapi.py`)
**Purpose**: REST API and web interface

**Key Features**:
- Asset management (add/remove/toggle assets)
- Options data filtering
- Real-time statistics
- Server-sent events for live updates
- Static file serving

**Routes**:
- `/` - Main dashboard
- `/api/options/{asset}` - Get options data
- `/api/expiries/{asset}` - Get available expiries
- `/api/strikes/{asset}` - Get available strikes
- `/api/stats` - System statistics
- `/api/stream` - SSE stream

### 3. Dashboard (`webapp/templates/dashboard.html`)
**Purpose**: User interface for data visualization

**Key Features**:
- DataTables integration for sorting/pagination
- Column visibility toggles
- Real-time data updates
- Mobile responsive design
- Dark theme
- Auto-refresh capability

### 4. Redis Data Structure
**Key Patterns**:
```
option:{symbol} → Hash with option data
stats:global → System statistics
config:assets → Asset configuration
```

**Data Fields**:
- `symbol`, `expiry`, `strike`, `type`
- `last_price`, `mark_price`, `volume_24h`
- `open_interest`, `delta`, `gamma`, `theta`, `vega`
- `iv`, `underlying_price`, `timestamp`

---

## Features Implemented

### 1. Column Visibility Toggle
**Description**: Allow users to show/hide table columns

**Implementation**:
- Dropdown menu with checkboxes
- localStorage persistence
- Reset functionality
- Mobile optimization

**Usage**:
```javascript
// Toggle column visibility
optionsTable.column(columnIndex).visible(isVisible);

// Save preferences
localStorage.setItem('optionsTableColumns', JSON.stringify(visibility));
```

### 2. GUI Configuration System
**Description**: JSON-based configuration for UI customization

**Configuration File**: `webapp/static/gui_config.json`

**Features**:
- Default column visibility
- Display formats (currency, percentage, etc.)
- Presets (Trader View, Greeks Focus, etc.)
- Color schemes
- Auto-refresh settings

**Example Configuration**:
```json
{
  "column_settings": {
    "columns": [
      {
        "id": 0,
        "field": "symbol",
        "visible": true,
        "format": "text"
      }
    ]
  }
}
```

### 3. Error Recovery System
**Description**: Robust error handling and recovery

**Features**:
- Automatic WebSocket reconnection
- Redis connection retry logic
- Graceful shutdown handling
- Error logging and monitoring

### 4. Docker Support
**Description**: Containerized deployment

**Components**:
- `docker-compose.yml` - Multi-container orchestration
- `Dockerfile` - Application container
- `Dockerfile.webapp` - Web app container
- `Dockerfile.cron` - Scheduled tasks

**Usage**:
```bash
docker-compose up -d
```

---

## Installation & Setup

### Prerequisites
```bash
# System requirements
- Python 3.9+
- Redis server
- Node.js (for frontend assets)
- Docker (optional)
```

### Local Installation

#### 1. Clone Repository
```bash
git clone https://github.com/aftabjack/options-data-b
cd options-data-b
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env file:
# REDIS_HOST=localhost (for local)
# REDIS_HOST=redis (for Docker)
```

#### 4. Start Services
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Options Tracker
python options_tracker_production.py

# Terminal 3: Start Web App
cd webapp
python app_fastapi.py
```

#### 5. Access Dashboard
Open browser: http://localhost:5001

### Docker Installation

#### 1. Build and Start
```bash
docker-compose up -d
```

#### 2. Check Status
```bash
docker-compose ps
docker-compose logs -f
```

#### 3. Stop Services
```bash
docker-compose down
```

---

## Configuration

### Environment Variables (.env)
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Tracker Settings
BATCH_SIZE=100
BATCH_TIMEOUT=5.0
CLEAR_DB_ON_START=false
OPTION_ASSETS=BTC,ETH,SOL

# Web Application
WEB_PORT=5001
AUTO_REFRESH_INTERVAL=5000

# Telegram Notifications (Optional)
ENABLE_NOTIFICATIONS=false
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_NOTIFICATION_CHANNEL=

# Performance
WS_PING_INTERVAL=20
WS_PING_TIMEOUT=10
WS_RECONNECT_DELAY=5
WS_MAX_RECONNECT_ATTEMPTS=10
```

### GUI Configuration (gui_config.json)
```json
{
  "gui_settings": {
    "default_page_size": 25,
    "sort_column": 6,
    "sort_direction": "desc",
    "auto_refresh": {
      "enabled": true,
      "interval": 5000
    }
  }
}
```

---

## API Endpoints

### Options Data
```http
GET /api/options/{asset}
Query Parameters:
  - expiry: string (optional)
  - type: "call" | "put" | "all"
  - strike: string (optional)

Response: Array of option objects
```

### Expiries
```http
GET /api/expiries/{asset}
Response: ["3SEP25", "4SEP25", "5SEP25", ...]
```

### Strikes
```http
GET /api/strikes/{asset}
Query Parameters:
  - expiry: string (optional)

Response: ["90000", "95000", "100000", ...]
```

### Statistics
```http
GET /api/stats
Response: {
  "total_symbols": 1850,
  "messages_processed": 50000,
  "last_update": "2025-09-02T12:00:00",
  "redis_memory": "2.5MB"
}
```

### Server-Sent Events
```http
GET /api/stream
Response: text/event-stream
data: {"total_symbols": 1850, ...}
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Redis Connection Error
**Error**: `redis.exceptions.ConnectionError: Error 8 connecting to redis:6379`

**Cause**: Docker hostname vs localhost mismatch

**Solution**:
```bash
# For local development
REDIS_HOST=localhost python app_fastapi.py

# Or modify .env
REDIS_HOST=localhost
```

#### 2. WebSocket Connection Issues
**Error**: `WebSocket connection failed: Connection is already closed`

**Possible Causes**:
- Network interruption
- API rate limiting
- Invalid credentials

**Solutions**:
- Check internet connection
- Verify Bybit API status
- Review rate limits
- Check WebSocket parameters

#### 3. No Data Displayed
**Symptoms**: Empty tables in dashboard

**Checks**:
```bash
# Check if tracker is running
ps aux | grep options_tracker

# Check Redis data
redis-cli keys "option:*"

# Check logs
tail -f logs/tracker.log
```

#### 4. Module Import Errors
**Error**: `ModuleNotFoundError: No module named 'telethon'`

**Solution**:
```bash
pip install telethon
# Or install all requirements
pip install -r requirements.txt
```

#### 5. Port Already in Use
**Error**: `[Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :5001

# Kill process
kill -9 <PID>

# Or use different port
python app_fastapi.py --port 5002
```

---

## Enhancements Made

### 1. Column Visibility Feature
- **Added**: Dropdown menu with checkboxes for each column
- **Benefit**: Users can customize their view
- **Storage**: Preferences saved in localStorage

### 2. GUI Configuration System
- **Added**: JSON-based configuration file
- **Benefit**: Easy customization without code changes
- **Features**: Presets, formats, color schemes

### 3. Error Recovery Improvements
- **Added**: Exponential backoff for reconnections
- **Benefit**: More robust connection handling
- **Implementation**: Smart retry logic with max attempts

### 4. Mobile Responsiveness
- **Added**: Responsive design adjustments
- **Benefit**: Usable on phones and tablets
- **Features**: Adaptive column display, touch-friendly controls

### 5. Performance Optimizations
- **Batch Processing**: Reduced Redis operations
- **Connection Pooling**: Improved Redis performance
- **Data Caching**: Reduced API calls
- **Virtual Scrolling**: Better handling of large datasets

---

## Performance Optimizations

### 1. Batch Processing
```python
# Before: Individual Redis writes
for data in messages:
    redis.hset(key, data)

# After: Batched pipeline
pipeline = redis.pipeline()
for data in batch:
    pipeline.hset(key, data)
pipeline.execute()
```

### 2. Connection Pooling
```python
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    socket_keepalive=True
)
```

### 3. Data Compression
- Removed unnecessary fields
- Optimized data types
- Implemented TTL for old data

### 4. Frontend Optimization
- Lazy loading for large datasets
- Virtual scrolling in tables
- Debounced search/filter inputs
- Minimized DOM manipulations

---

## Future Improvements

### 1. Planned Features
- [ ] Historical data storage and analysis
- [ ] Advanced charting (candlesticks, Greeks over time)
- [ ] Strategy backtesting framework
- [ ] Risk management dashboard
- [ ] Multi-user support with authentication
- [ ] Email notifications alongside Telegram
- [ ] Export functionality (CSV, Excel, PDF)
- [ ] API rate limit monitoring
- [ ] Automated trading integration
- [ ] Machine learning price predictions

### 2. Technical Improvements
- [ ] Migrate to PostgreSQL for historical data
- [ ] Implement GraphQL API
- [ ] Add WebSocket for frontend updates
- [ ] Kubernetes deployment manifests
- [ ] Prometheus/Grafana monitoring
- [ ] Unit and integration tests
- [ ] CI/CD pipeline
- [ ] Load balancing for multiple instances
- [ ] Data compression for storage efficiency
- [ ] Implement caching layer (Redis + PostgreSQL)

### 3. UI/UX Enhancements
- [ ] Dark/Light theme toggle
- [ ] Customizable dashboards
- [ ] Drag-and-drop column reordering
- [ ] Advanced filtering UI
- [ ] Keyboard shortcuts
- [ ] Full-screen mode
- [ ] Multi-language support
- [ ] Tutorial/onboarding flow
- [ ] Custom alerts configuration UI
- [ ] Mobile app (React Native)

---

## Development Commands

### Useful Commands
```bash
# Check Redis data
redis-cli
> keys option:*
> hgetall option:BTC-3SEP25-100000-C

# Monitor logs
tail -f webapp/app.log

# Test API endpoints
curl http://localhost:5001/api/options/BTC
curl http://localhost:5001/api/stats

# Clean Redis
redis-cli flushdb

# Check memory usage
redis-cli info memory

# Docker commands
docker-compose logs tracker
docker-compose restart webapp
docker exec -it redis redis-cli
```

### Development Workflow
1. Make changes to code
2. Test locally
3. Build Docker image
4. Test in container
5. Push to GitHub
6. Deploy to production

---

## Security Considerations

### Current Implementation
- Environment variables for sensitive data
- No hardcoded credentials
- Redis password support (optional)
- Input validation on API endpoints
- CORS configuration for web security

### Recommended Improvements
- [ ] Add API authentication (JWT tokens)
- [ ] Implement rate limiting
- [ ] Add SSL/TLS certificates
- [ ] Encrypt sensitive data in Redis
- [ ] Add request validation middleware
- [ ] Implement user roles and permissions
- [ ] Add audit logging
- [ ] Regular security updates
- [ ] Penetration testing
- [ ] DDoS protection

---

## Monitoring & Logging

### Current Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

### Log Locations
- Tracker logs: Console output
- Web app logs: Console output
- Redis logs: `/var/log/redis/redis-server.log`

### Monitoring Metrics
- Total symbols tracked
- Messages processed per second
- WebSocket connection status
- Redis memory usage
- API response times
- Error rates

---

## Contributing

### Code Style
- Python: PEP 8
- JavaScript: ESLint standard
- HTML/CSS: Bootstrap conventions

### Testing
```bash
# Run tests (when implemented)
pytest tests/

# Check code style
flake8 .
black --check .
```

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit PR

---

## License & Credits

### License
[Specify your license]

### Credits
- Bybit API for market data
- pybit library for WebSocket client
- FastAPI for web framework
- Redis for data storage
- Bootstrap for UI components
- DataTables for table functionality

---

## Support & Contact

### Getting Help
1. Check this documentation
2. Review troubleshooting guide
3. Check GitHub issues
4. Contact maintainers

### Reporting Issues
When reporting issues, include:
- Error messages
- Steps to reproduce
- Environment details
- Log files

---

## Appendix

### A. Redis Data Schema
```
Key: option:{symbol}
Type: Hash
Fields:
  - symbol: string
  - expiry: string
  - strike: string
  - type: "Call" | "Put"
  - last_price: float
  - mark_price: float
  - volume_24h: float
  - open_interest: float
  - delta: float
  - gamma: float
  - theta: float
  - vega: float
  - iv: float
  - underlying_price: float
  - timestamp: float
TTL: 3600 seconds
```

### B. WebSocket Message Format
```json
{
  "topic": "tickers.option",
  "type": "snapshot",
  "data": {
    "symbol": "BTC-3SEP25-100000-C",
    "lastPrice": "1234.56",
    "markPrice": "1235.00",
    "volume24h": "10000",
    "openInterest": "5000",
    "delta": "0.5",
    "gamma": "0.0001",
    "theta": "-10.5",
    "vega": "25.3",
    "markIv": "0.65",
    "underlyingPrice": "100000"
  }
}
```

### C. Environment File Template
```bash
# Copy this to .env and fill in values

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Tracker Configuration
CLEAR_DB_ON_START=false
BATCH_SIZE=100
BATCH_TIMEOUT=5.0
SYMBOL_CACHE_TTL=86400
OPTION_ASSETS=BTC,ETH,SOL

# Web Application
WEB_PORT=5001
AUTO_REFRESH_INTERVAL=5000

# Telegram Notifications
ENABLE_NOTIFICATIONS=false
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_NOTIFICATION_CHANNEL=

# Performance Settings
WS_PING_INTERVAL=20
WS_PING_TIMEOUT=10
WS_RECONNECT_DELAY=5
WS_MAX_RECONNECT_ATTEMPTS=10

# Logging
LOG_LEVEL=INFO
STATS_INTERVAL=30
```

---

*Documentation Version: 1.0.0*  
*Last Updated: September 2, 2025*  
*Author: Bybit Options Tracker Development Team*