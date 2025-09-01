#!/bin/bash

# Bybit Options - Docker Startup Script

echo "======================================"
echo "Starting Bybit Options with Docker"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop first."
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp config/.env.example .env 2>/dev/null || echo "Using default .env"
fi

# Create necessary directories
mkdir -p logs

# Build images
echo ""
echo "Building Docker images..."
docker-compose build

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to start
echo ""
echo "Waiting for services to initialize..."
sleep 8

# Show comprehensive status using Python script
if [ -f scripts/check_status.py ]; then
    python3 scripts/check_status.py
else
    # Fallback to basic status if script not found
    echo ""
    echo "Checking service status..."
    docker-compose ps
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✅ Services Started!${NC}"
    echo "======================================"
    echo ""
    echo "📊 Access Points:"
    echo "  Web Dashboard: http://localhost:5001"
    echo "  Data API:      http://localhost:8000"
    echo "  API Docs:      http://localhost:8000/docs"
    echo "  Health Check:  http://localhost:8080/health"
    echo ""
    echo "📝 Useful Commands:"
    echo "  View logs:     docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart:       docker-compose restart"
    echo "  Check status:  python3 scripts/check_status.py"
fi

# Option to show logs
echo ""
read -t 5 -p "Show live logs? (y/N): " show_logs
if [[ "$show_logs" == "y" ]] || [[ "$show_logs" == "Y" ]]; then
    echo "Showing logs (press Ctrl+C to exit)..."
    echo "======================================"
    docker-compose logs -f --tail=20
fi