#!/bin/bash

# Bybit Options - Docker Information Script
# Shows detailed information about running containers and their access URLs

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo ""
echo "============================================================"
echo -e "${BLUE}🐳 BYBIT OPTIONS DOCKER STATUS${NC}"
echo "============================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    exit 1
fi

# Function to check container status
check_container() {
    local container=$1
    local name=$2
    local port=$3
    local url=$4
    
    if docker ps | grep -q "$container"; then
        # Get container stats
        stats=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemUsage}}" $container 2>/dev/null | head -1)
        cpu=$(echo $stats | awk '{print $1}')
        mem=$(echo $stats | awk '{print $2}')
        
        echo -e "${GREEN}✅ $name${NC}"
        echo -e "   Container: $container"
        echo -e "   Port:      $port"
        echo -e "   CPU:       $cpu"
        echo -e "   Memory:    $mem"
        if [ ! -z "$url" ]; then
            echo -e "   ${CYAN}URL:       $url${NC}"
        fi
    else
        echo -e "${RED}❌ $name${NC}"
        echo -e "   Container: $container (not running)"
    fi
    echo ""
}

# Check each container
echo -e "${BLUE}📦 CONTAINERS${NC}"
echo "------------------------------------------------------------"
check_container "bybit-tracker" "WebSocket Tracker" "N/A" ""
check_container "bybit-webapp" "Web Dashboard" "5001" "http://localhost:5001"
check_container "bybit-dataapi" "Data API" "8000" "http://localhost:8000"
check_container "bybit-redis" "Redis Database" "6380" ""
check_container "bybit-cron" "Cron Jobs" "N/A" ""

# Show network information
echo -e "${BLUE}🌐 NETWORK${NC}"
echo "------------------------------------------------------------"
if docker network ls | grep -q "bybit-network"; then
    echo -e "${GREEN}✅ Network: bybit-network${NC}"
    # Show connected containers
    connected=$(docker network inspect bybit-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null)
    if [ ! -z "$connected" ]; then
        echo -e "   Connected: $connected"
    fi
else
    echo -e "${RED}❌ Network: bybit-network not found${NC}"
fi
echo ""

# Show volume information
echo -e "${BLUE}💾 VOLUMES${NC}"
echo "------------------------------------------------------------"
if docker volume ls | grep -q "redis_data"; then
    size=$(docker volume inspect bybit-options-production_redis_data --format '{{.Mountpoint}}' 2>/dev/null | xargs du -sh 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ Redis Data Volume${NC}"
    echo -e "   Name: bybit-options-production_redis_data"
    if [ ! -z "$size" ]; then
        echo -e "   Size: $size"
    fi
else
    echo -e "${YELLOW}⚠️  Redis volume not found${NC}"
fi
echo ""

# Show access URLs from config
echo -e "${BLUE}🔗 ACCESS URLS${NC}"
echo "------------------------------------------------------------"

# Try to load URLs from config
if [ -f config_loader.py ]; then
    # Use Python to get URLs
    python3 -c "
from config_loader import config
urls = config.get_service_urls()
for service, info in urls.items():
    print(f'{service.upper()}:')
    print(f'  URL: {info[\"url\"]}')
    if info.get('docs'):
        print(f'  Docs: {info[\"docs\"]}')
" 2>/dev/null || {
    # Fallback to default URLs
    echo -e "${CYAN}Web Dashboard:${NC}     http://localhost:5001"
    echo -e "${CYAN}Data API:${NC}          http://localhost:8000"
    echo -e "${CYAN}API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${CYAN}Health Check:${NC}      http://localhost:8080/health"
}
else
    # Default URLs
    echo -e "${CYAN}Web Dashboard:${NC}     http://localhost:5001"
    echo -e "${CYAN}Data API:${NC}          http://localhost:8000"
    echo -e "${CYAN}API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${CYAN}Health Check:${NC}      http://localhost:8080/health"
fi
echo ""

# Show Docker Compose status
echo -e "${BLUE}📊 DOCKER COMPOSE STATUS${NC}"
echo "------------------------------------------------------------"
docker-compose ps
echo ""

# Show resource usage summary
echo -e "${BLUE}💻 RESOURCE USAGE SUMMARY${NC}"
echo "------------------------------------------------------------"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep -E "CONTAINER|bybit" || echo "No containers running"
echo ""

# Check Redis connectivity
echo -e "${BLUE}🔍 SERVICE HEALTH${NC}"
echo "------------------------------------------------------------"

# Test Redis
if docker exec bybit-redis redis-cli ping > /dev/null 2>&1; then
    keys=$(docker exec bybit-redis redis-cli dbsize 2>/dev/null | awk '{print $2}')
    echo -e "${GREEN}✅ Redis:${NC} Connected (Keys: $keys)"
else
    echo -e "${RED}❌ Redis:${NC} Not responding"
fi

# Test Web Dashboard
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 2>/dev/null | grep -q "200\|302"; then
    echo -e "${GREEN}✅ Web Dashboard:${NC} Accessible"
else
    echo -e "${YELLOW}⚠️  Web Dashboard:${NC} Not accessible"
fi

# Test API
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✅ Data API:${NC} Healthy"
else
    echo -e "${YELLOW}⚠️  Data API:${NC} Not responding"
fi
echo ""

# Show useful commands
echo -e "${BLUE}💡 USEFUL COMMANDS${NC}"
echo "------------------------------------------------------------"
echo "View logs:         docker-compose logs -f [service]"
echo "Restart service:   docker-compose restart [service]"
echo "Stop all:          ./docker-stop.sh"
echo "Start all:         ./docker-start.sh"
echo "Enter container:   docker exec -it [container] /bin/sh"
echo "Redis CLI:         docker exec -it bybit-redis redis-cli"
echo ""

# Show configuration status
echo -e "${BLUE}⚙️  CONFIGURATION${NC}"
echo "------------------------------------------------------------"
if [ -f config.yaml ]; then
    echo -e "${GREEN}✅ config.yaml found${NC}"
else
    echo -e "${YELLOW}⚠️  config.yaml not found (using defaults)${NC}"
fi

if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
else
    echo -e "${YELLOW}⚠️  .env file not found (using defaults)${NC}"
fi
echo ""

echo "============================================================"
echo -e "${GREEN}📈 Use 'docker-compose logs -f' to view live logs${NC}"
echo "============================================================"