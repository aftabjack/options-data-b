#!/bin/bash

# Bybit Options Health Check Script
# Quick health check for all services

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================"
echo "🏥 HEALTH CHECK - Bybit Options System"
echo "======================================"

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    exit 1
fi

# Check containers
echo ""
echo "📦 Container Status:"
for container in bybit-redis bybit-tracker bybit-webapp bybit-dataapi bybit-cron; do
    if docker ps | grep -q $container; then
        echo -e "  ${GREEN}✅ $container${NC}"
    else
        echo -e "  ${RED}❌ $container (not running)${NC}"
    fi
done

# Check Redis
echo ""
echo "💾 Redis Status:"
REDIS_STATUS=$(docker exec bybit-redis redis-cli ping 2>/dev/null)
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo -e "  ${GREEN}✅ Redis responding${NC}"
    KEYS=$(docker exec bybit-redis redis-cli dbsize 2>/dev/null | cut -d' ' -f2)
    echo "  • Keys in database: $KEYS"
else
    echo -e "  ${RED}❌ Redis not responding${NC}"
fi

# Check Data API
echo ""
echo "🌐 API Status:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Data API responding${NC}"
    
    # Get stats
    STATS=$(curl -s http://localhost:8000/health | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    s = d['stats']
    print(f'  • Total Options: {s[\"total_options\"]:,}')
    print(f'  • Messages: {s[\"messages_processed\"]:,}')
    print(f'  • BTC: {s[\"btc_options\"]} | ETH: {s[\"eth_options\"]} | SOL: {s[\"sol_options\"]}')
except:
    pass
" 2>/dev/null)
    
    if [ ! -z "$STATS" ]; then
        echo "$STATS"
    fi
else
    echo -e "  ${YELLOW}⚠️  Data API not responding${NC}"
fi

# Check WebApp
echo ""
echo "🖥️  WebApp Status:"
if curl -s http://localhost:5001 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Dashboard available${NC}"
    echo -e "  ${BLUE}→ http://localhost:5001${NC}"
else
    echo -e "  ${YELLOW}⚠️  Dashboard not responding${NC}"
fi

# Check tracker health endpoint
echo ""
echo "📡 Tracker Status:"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Tracker health endpoint responding${NC}"
else
    echo -e "  ${YELLOW}⚠️  Tracker health endpoint not responding${NC}"
    echo "  Note: Tracker may still be working even if health endpoint is down"
fi

# Resource usage
echo ""
echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6

echo ""
echo "======================================"
echo -e "${GREEN}Health check complete!${NC}"
echo ""
echo "Quick commands:"
echo "  • Full status:  python3 scripts/check_status.py"
echo "  • View logs:    docker-compose logs -f"
echo "  • Restart all:  docker-compose restart"
echo "======================================"