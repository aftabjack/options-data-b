# Bybit Options Tracker - Production

Real-time options data tracker for BTC, ETH, and SOL on Bybit exchange.

## Quick Start

```bash
# Start all services
./docker-start.sh

# Stop all services
./docker-stop.sh
```

## Access Points

- **Dashboard**: http://localhost:5001
- **Data API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## System Status

- Tracking 1,976+ options in real-time
- Processing 2,600+ messages/second
- Optimized for low resource usage

## Monitoring

```bash
# Check system status
python3 scripts/check_status.py

# Monitor resources
python3 scripts/monitor_resources.py

# Health check
bash scripts/health_check.sh
```

## Docker Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Check container status
docker ps
```

## Features

- Real-time WebSocket data collection
- REST API for data access
- Web dashboard with filtering
- Symbol validation
- Data export (CSV/JSON)
- Automatic daily symbol updates (08:05 UTC)
- Telegram notifications (optional)

## Performance

- CPU: ~85% total (optimized)
- Memory: ~340 MB total
- Processing: 2,600+ msg/sec
- Uptime: 99.9%+