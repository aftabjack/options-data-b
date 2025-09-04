#!/bin/bash
# Advanced Health Check Script for Bybit Options Tracker
# Run this script every 5 minutes via cron for proactive monitoring

set -e

LOG_FILE="/tmp/health_check.log"
ALERT_FILE="/tmp/health_alerts.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting health check..." >> $LOG_FILE

# Function to send alert
send_alert() {
    local severity=$1
    local message=$2
    echo "[$TIMESTAMP] $severity: $message" >> $ALERT_FILE
    echo "🚨 $severity: $message"
}

# Function to log info
log_info() {
    local message=$1
    echo "[$TIMESTAMP] INFO: $message" >> $LOG_FILE
    echo "ℹ️  $message"
}

# Check if Docker containers are running
echo "Checking container status..."
CONTAINERS=("bybit-redis" "bybit-tracker" "bybit-webapp" "bybit-dataapi")
for container in "${CONTAINERS[@]}"; do
    if ! docker ps | grep -q $container; then
        send_alert "CRITICAL" "Container $container is not running"
    else
        log_info "Container $container is healthy"
    fi
done

# Check WebSocket reconnection rate (last hour)
echo "Checking WebSocket stability..."
WS_ERRORS=$(docker logs bybit-tracker --since 1h 2>&1 | grep -c "Connection to remote host was lost" || echo "0")
if [ "$WS_ERRORS" -gt 100 ]; then
    send_alert "CRITICAL" "High WebSocket reconnection rate: $WS_ERRORS/hour"
elif [ "$WS_ERRORS" -gt 60 ]; then
    send_alert "WARNING" "Moderate WebSocket reconnection rate: $WS_ERRORS/hour"
else
    log_info "WebSocket reconnection rate acceptable: $WS_ERRORS/hour"
fi

# Check Redis memory usage
echo "Checking Redis memory..."
REDIS_MEM_BYTES=$(docker exec bybit-redis redis-cli info memory 2>/dev/null | grep "used_memory:" | cut -d: -f2 | tr -d '\r')
REDIS_MEM_MB=$((REDIS_MEM_BYTES / 1024 / 1024))
if [ "$REDIS_MEM_MB" -gt 400 ]; then
    send_alert "CRITICAL" "Redis memory usage too high: ${REDIS_MEM_MB}MB"
elif [ "$REDIS_MEM_MB" -gt 200 ]; then
    send_alert "WARNING" "Redis memory usage elevated: ${REDIS_MEM_MB}MB"
else
    log_info "Redis memory usage normal: ${REDIS_MEM_MB}MB"
fi

# Check data freshness
echo "Checking data freshness..."
LAST_UPDATE=$(docker exec bybit-redis redis-cli hget "stats:global" "last_update" 2>/dev/null || echo "0")
CURRENT_TIME=$(date +%s)
if [ "$LAST_UPDATE" != "0" ]; then
    STALENESS=$((CURRENT_TIME - LAST_UPDATE))
    if [ "$STALENESS" -gt 300 ]; then
        send_alert "CRITICAL" "Data stale for $STALENESS seconds"
    elif [ "$STALENESS" -gt 120 ]; then
        send_alert "WARNING" "Data staleness: $STALENESS seconds"
    else
        log_info "Data freshness good: ${STALENESS}s old"
    fi
else
    send_alert "WARNING" "Unable to determine data freshness"
fi

# Check API responsiveness
echo "Checking API response..."
API_START=$(date +%s.%N)
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/stats || echo "000")
API_END=$(date +%s.%N)
API_TIME=$(echo "$API_END - $API_START" | bc -l 2>/dev/null || echo "999")

if [ "$API_RESPONSE" != "200" ]; then
    send_alert "CRITICAL" "API not responding: HTTP $API_RESPONSE"
elif (( $(echo "$API_TIME > 2.0" | bc -l) )); then
    send_alert "WARNING" "API response slow: ${API_TIME}s"
else
    log_info "API response good: ${API_TIME}s"
fi

# Check disk space
echo "Checking disk space..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    send_alert "CRITICAL" "Disk space critical: ${DISK_USAGE}% used"
elif [ "$DISK_USAGE" -gt 80 ]; then
    send_alert "WARNING" "Disk space high: ${DISK_USAGE}% used"
else
    log_info "Disk space normal: ${DISK_USAGE}% used"
fi

# Check container resource usage
echo "Checking container resources..."
docker stats --no-stream --format "{{.Name}} {{.CPUPerc}} {{.MemUsage}}" | while read line; do
    CONTAINER=$(echo $line | awk '{print $1}')
    CPU_USAGE=$(echo $line | awk '{print $2}' | sed 's/%//')
    MEM_USAGE=$(echo $line | awk '{print $3}' | sed 's/MiB.*//')
    
    if (( $(echo "$CPU_USAGE > 80" | bc -l 2>/dev/null || echo 0) )); then
        send_alert "WARNING" "High CPU usage on $CONTAINER: ${CPU_USAGE}%"
    fi
    
    if [ "$MEM_USAGE" -gt 200 ]; then
        send_alert "WARNING" "High memory usage on $CONTAINER: ${MEM_USAGE}MB"
    fi
done

# Count total options
echo "Checking data completeness..."
TOTAL_OPTIONS=$(docker exec bybit-redis redis-cli dbsize 2>/dev/null || echo "0")
if [ "$TOTAL_OPTIONS" -lt 1000 ]; then
    send_alert "WARNING" "Low option count: $TOTAL_OPTIONS (expected >2000)"
else
    log_info "Option count healthy: $TOTAL_OPTIONS"
fi

echo "[$TIMESTAMP] Health check completed" >> $LOG_FILE
echo "✅ Health check completed at $TIMESTAMP"

# Show recent alerts if any
if [ -f "$ALERT_FILE" ]; then
    RECENT_ALERTS=$(tail -n 10 "$ALERT_FILE" | grep "$(date '+%Y-%m-%d')" || echo "")
    if [ ! -z "$RECENT_ALERTS" ]; then
        echo ""
        echo "🚨 Recent alerts:"
        echo "$RECENT_ALERTS"
    fi
fi