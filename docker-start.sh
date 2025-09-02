#!/bin/bash

# Bybit Options - Docker Startup Script with Config Support

echo "======================================"
echo "Starting Bybit Options with Docker"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop first."
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if config.yaml exists
if [ ! -f config.yaml ]; then
    echo -e "${YELLOW}⚠️  config.yaml not found, using defaults${NC}"
fi

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

# Show access URLs using Python config loader
echo ""
if [ -f config_loader.py ]; then
    python3 config_loader.py
else
    # Fallback display if config loader not available
    echo "======================================"
    echo -e "${GREEN}✅ Services Started!${NC}"
    echo "======================================"
    echo ""
    echo -e "${BLUE}📊 ACCESS URLS${NC}"
    echo "======================================"
    echo -e "${CYAN}Web Dashboard:${NC}    http://localhost:5001"
    echo -e "${CYAN}Data API:${NC}         http://localhost:8000"
    echo -e "${CYAN}API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${CYAN}Health Check:${NC}     http://localhost:8080/health"
    echo ""
    echo -e "${BLUE}📝 USEFUL COMMANDS${NC}"
    echo "======================================"
    echo "View logs:        docker-compose logs -f"
    echo "Check status:     python3 scripts/check_status.py"
    echo "Monitor resources: python3 scripts/monitor_resources.py"
    echo "Stop services:    ./docker-stop.sh"
    echo "Restart:          docker-compose restart"
fi

# Check service health
echo ""
echo -e "${BLUE}🔍 Checking Services...${NC}"
echo "======================================"

# Check if services are running
check_service() {
    service=$1
    port=$2
    
    if docker-compose ps | grep -q "$service.*Up"; then
        echo -e "${GREEN}✅ $service is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service is not running${NC}"
        return 1
    fi
}

# Check each service
check_service "bybit-tracker" "N/A"
check_service "bybit-webapp" "5001"
check_service "bybit-dataapi" "8000"
check_service "redis" "6379"

# Check Redis connectivity
echo ""
echo -e "${BLUE}🔗 Testing Connections...${NC}"
echo "======================================"

# Test Redis
if docker exec redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not responding yet${NC}"
fi

# Test Web Dashboard
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 | grep -q "200\|302"; then
    echo -e "${GREEN}✅ Web Dashboard is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Web Dashboard not ready yet${NC}"
fi

# Test API
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo -e "${GREEN}✅ Data API is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Data API not ready yet${NC}"
fi

# Show quick stats
echo ""
echo -e "${BLUE}📈 Quick Stats${NC}"
echo "======================================"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep bybit || true

# Custom domain reminder
if [ -f config.yaml ] && grep -q "domains:" config.yaml; then
    echo ""
    echo -e "${YELLOW}💡 TIP: Configure custom domains in config.yaml${NC}"
fi

# Final message
echo ""
echo "======================================"
echo -e "${GREEN}🚀 SYSTEM READY!${NC}"
echo "======================================"
echo -e "Open your browser and navigate to:"
echo -e "${CYAN}• Dashboard: http://localhost:5001${NC}"
echo -e "${CYAN}• API Docs:  http://localhost:8000/docs${NC}"
echo ""

# Option to show logs
read -t 10 -p "Show live logs? (y/N): " show_logs
if [[ "$show_logs" == "y" ]] || [[ "$show_logs" == "Y" ]]; then
    echo ""
    echo "Showing logs (press Ctrl+C to exit)..."
    echo "======================================"
    docker-compose logs -f --tail=20
fi