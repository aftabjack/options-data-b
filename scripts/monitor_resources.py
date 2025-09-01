#!/usr/bin/env python3
"""
Resource Monitor for Bybit Options System
Shows real-time resource usage and optimization suggestions
"""

import subprocess
import time
import json
import sys
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def get_container_stats():
    """Get container statistics"""
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', '{{json .}}'],
            capture_output=True,
            text=True
        )
        
        stats = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                data = json.loads(line)
                if 'bybit' in data['Name']:
                    # Parse CPU percentage
                    cpu = float(data['CPUPerc'].rstrip('%'))
                    
                    # Parse memory
                    mem_parts = data['MemUsage'].split(' / ')
                    mem_used = mem_parts[0]
                    
                    # Parse memory percentage
                    mem_perc = float(data['MemPerc'].rstrip('%'))
                    
                    stats[data['Name']] = {
                        'cpu': cpu,
                        'memory': mem_used,
                        'mem_percent': mem_perc,
                        'net_io': data['NetIO']
                    }
        
        return stats
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {}

def get_color_for_cpu(cpu):
    """Get color based on CPU usage"""
    if cpu < 30:
        return Colors.GREEN
    elif cpu < 70:
        return Colors.YELLOW
    else:
        return Colors.RED

def get_color_for_memory(mem_percent):
    """Get color based on memory usage"""
    if mem_percent < 2:
        return Colors.GREEN
    elif mem_percent < 5:
        return Colors.YELLOW
    else:
        return Colors.RED

def print_optimization_suggestions(stats):
    """Print optimization suggestions based on current usage"""
    print(f"\n{Colors.BOLD}💡 OPTIMIZATION SUGGESTIONS:{Colors.END}")
    
    suggestions_made = False
    
    for container, data in stats.items():
        if 'tracker' in container and data['cpu'] > 50:
            print(f"\n{Colors.YELLOW}⚠️  {container} - High CPU Usage ({data['cpu']:.1f}%){Colors.END}")
            print(f"  Suggestions:")
            print(f"  • Increase WS_PING_INTERVAL (current: 30s, suggested: 45s)")
            print(f"  • Increase BATCH_SIZE (current: 100, suggested: 200)")
            print(f"  • Increase WS_RECONNECT_DELAY to reduce reconnection attempts")
            print(f"  • Use optimized tracker: {Colors.CYAN}options_tracker_optimized.py{Colors.END}")
            suggestions_made = True
        
        if data['mem_percent'] > 3:
            print(f"\n{Colors.YELLOW}⚠️  {container} - High Memory Usage ({data['mem_percent']:.1f}%){Colors.END}")
            print(f"  Suggestions:")
            print(f"  • Add memory limits in docker-compose.yml")
            print(f"  • Reduce WRITE_QUEUE_SIZE")
            print(f"  • Clear Redis keys periodically")
            suggestions_made = True
    
    if not suggestions_made:
        print(f"{Colors.GREEN}  ✅ System is running efficiently!{Colors.END}")
        print(f"  All containers are within optimal resource limits.")

def monitor_resources(duration=None):
    """Monitor resources continuously or for specified duration"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          RESOURCE MONITOR - Bybit Options System            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    start_time = time.time()
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Clear screen for continuous monitoring
            if iteration > 1:
                print("\033[H\033[J", end='')  # Clear screen
                print(f"{Colors.CYAN}{Colors.BOLD}")
                print("╔══════════════════════════════════════════════════════════════╗")
                print("║          RESOURCE MONITOR - Bybit Options System            ║")
                print("╚══════════════════════════════════════════════════════════════╝")
                print(f"{Colors.END}")
            
            # Get current stats
            stats = get_container_stats()
            
            if not stats:
                print(f"{Colors.RED}Unable to get container statistics{Colors.END}")
                break
            
            # Print timestamp
            print(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─' * 64}")
            
            # Print header
            print(f"\n{Colors.BOLD}{'Container':<20} {'CPU':<10} {'Memory':<15} {'Mem %':<10} {'Network I/O':<20}{Colors.END}")
            print(f"{'─' * 80}")
            
            # Calculate totals
            total_cpu = 0
            total_mem_percent = 0
            
            # Print each container
            for container_name in sorted(stats.keys()):
                data = stats[container_name]
                
                # Get colors
                cpu_color = get_color_for_cpu(data['cpu'])
                mem_color = get_color_for_memory(data['mem_percent'])
                
                # Format name
                short_name = container_name.replace('bybit-', '')
                
                # Print row
                print(f"{short_name:<20} "
                      f"{cpu_color}{data['cpu']:>6.1f}%{Colors.END}    "
                      f"{data['memory']:<15} "
                      f"{mem_color}{data['mem_percent']:>6.1f}%{Colors.END}    "
                      f"{data['net_io']:<20}")
                
                total_cpu += data['cpu']
                total_mem_percent += data['mem_percent']
            
            # Print totals
            print(f"{'─' * 80}")
            total_color = get_color_for_cpu(total_cpu)
            print(f"{Colors.BOLD}{'TOTAL':<20} "
                  f"{total_color}{total_cpu:>6.1f}%{Colors.END}    "
                  f"{'─':<15} "
                  f"{get_color_for_memory(total_mem_percent)}{total_mem_percent:>6.1f}%{Colors.END}{Colors.END}")
            
            # Print optimization suggestions
            print_optimization_suggestions(stats)
            
            # Print controls
            print(f"\n{Colors.CYAN}Press Ctrl+C to stop monitoring{Colors.END}")
            
            # Check duration
            if duration and (time.time() - start_time) >= duration:
                break
            
            # Wait before next update
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitoring stopped{Colors.END}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor resource usage of Bybit Options System')
    parser.add_argument('-t', '--time', type=int, help='Monitor for specified seconds')
    parser.add_argument('-o', '--once', action='store_true', help='Show stats once and exit')
    
    args = parser.parse_args()
    
    if args.once:
        monitor_resources(duration=1)
    else:
        monitor_resources(duration=args.time)

if __name__ == "__main__":
    main()