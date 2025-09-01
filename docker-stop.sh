#!/bin/bash

# Bybit Options - Docker Stop Script

echo "======================================"
echo "Stopping Bybit Options Docker Services"
echo "======================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Stop all services
echo "Stopping services..."
docker-compose down

# Optional: Remove volumes (uncomment if you want to clear data)
# echo "Removing volumes..."
# docker-compose down -v

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo "To restart, run: ./docker-start.sh"