#!/usr/bin/env python3
"""
System Status Display for Bybit Options Tracker
Shows comprehensive status information after Docker startup
"""

import json
import time
import sys
import subprocess
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def check_container_status():
    """Check if all containers are running"""
    try:
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                              capture_output=True, text=True)
        containers = result.stdout.strip().split('\n')
        
        required = ['bybit-redis', 'bybit-tracker', 'bybit-webapp', 'bybit-dataapi', 'bybit-cron']
        running = {c: c in containers for c in required}
        
        return running
    except:
        return {}

def get_health_data():
    """Get health data from API"""
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.json()
    except:
        return None

def format_number(num):
    """Format large numbers with commas"""
    try:
        return f"{int(num):,}"
    except:
        return "0"

def print_banner():
    """Print ASCII banner"""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  {Colors.BOLD}{Colors.WHITE}📈 BYBIT OPTIONS TRACKER - PRODUCTION SYSTEM 📈{Colors.END}{Colors.CYAN}            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)

def print_status():
    """Print comprehensive system status"""
    print_banner()
    
    # Check containers
    print(f"\n{Colors.BOLD}📦 CONTAINER STATUS:{Colors.END}")
    containers = check_container_status()
    
    if not containers:
        print(f"{Colors.RED}  ❌ Docker is not running or containers not found{Colors.END}")
        return False
    
    all_running = True
    for name, running in containers.items():
        if running:
            print(f"  {Colors.GREEN}✅ {name:<20} Running{Colors.END}")
        else:
            print(f"  {Colors.RED}❌ {name:<20} Not Running{Colors.END}")
            all_running = False
    
    if not all_running:
        print(f"\n{Colors.YELLOW}⚠️  Some containers are not running. Run: ./docker-start.sh{Colors.END}")
        return False
    
    # Wait for services to be ready
    print(f"\n{Colors.YELLOW}⏳ Waiting for services to initialize...{Colors.END}")
    time.sleep(5)
    
    # Get health data
    health = get_health_data()
    
    if health and health.get('status') == 'healthy':
        stats = health.get('stats', {})
        
        print(f"\n{Colors.BOLD}📊 DATA COLLECTION STATUS:{Colors.END}")
        print(f"  {Colors.GREEN}✅ System Status: HEALTHY{Colors.END}")
        print(f"  • Total Options: {Colors.CYAN}{format_number(stats.get('total_options', 0))}{Colors.END}")
        print(f"  • BTC Options: {Colors.WHITE}{stats.get('btc_options', 0)}{Colors.END}")
        print(f"  • ETH Options: {Colors.WHITE}{stats.get('eth_options', 0)}{Colors.END}")
        print(f"  • SOL Options: {Colors.WHITE}{stats.get('sol_options', 0)}{Colors.END}")
        print(f"  • Messages Processed: {Colors.CYAN}{format_number(stats.get('messages_processed', 0))}{Colors.END}")
        
        # Calculate processing rate
        time.sleep(2)
        health2 = get_health_data()
        if health2:
            stats2 = health2.get('stats', {})
            msg1 = stats.get('messages_processed', 0)
            msg2 = stats2.get('messages_processed', 0)
            rate = (msg2 - msg1) / 2
            if rate > 0:
                print(f"  • Processing Rate: {Colors.GREEN}{rate:.0f} msg/sec{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Data API is still initializing...{Colors.END}")
    
    # Print access points
    print(f"\n{Colors.BOLD}🌐 ACCESS POINTS:{Colors.END}")
    print(f"  • Web Dashboard: {Colors.BLUE}http://localhost:5001{Colors.END}")
    print(f"  • Data API:      {Colors.BLUE}http://localhost:8000{Colors.END}")
    print(f"  • API Docs:      {Colors.BLUE}http://localhost:8000/docs{Colors.END}")
    print(f"  • Health Check:  {Colors.BLUE}http://localhost:8080/health{Colors.END}")
    
    # Print commands
    print(f"\n{Colors.BOLD}📝 USEFUL COMMANDS:{Colors.END}")
    print(f"  • View logs:     {Colors.WHITE}docker-compose logs -f{Colors.END}")
    print(f"  • Stop services: {Colors.WHITE}docker-compose down{Colors.END}")
    print(f"  • Restart:       {Colors.WHITE}docker-compose restart{Colors.END}")
    print(f"  • Check status:  {Colors.WHITE}python scripts/check_status.py{Colors.END}")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTEM IS RUNNING SUCCESSFULLY!{Colors.END}")
    print(f"{Colors.CYAN}{'═' * 64}{Colors.END}\n")
    
    return True

if __name__ == "__main__":
    try:
        success = print_status()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Status check interrupted{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error checking status: {e}{Colors.END}")
        sys.exit(1)