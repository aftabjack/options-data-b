#!/usr/bin/env python3
"""
Comprehensive Error Checking Script for Bybit Options Production
Checks for configuration, syntax, and runtime issues
"""

import os
import sys
import yaml
import json
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def check_python_syntax():
    """Check all Python files for syntax errors"""
    print_header("PYTHON SYNTAX CHECK")
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    errors = []
    for file in python_files:
        try:
            with open(file, 'r') as f:
                compile(f.read(), file, 'exec')
            print(f"{GREEN}✅{RESET} {file}")
        except SyntaxError as e:
            errors.append(f"{file}: {e}")
            print(f"{RED}❌{RESET} {file}: {e}")
    
    return len(errors) == 0

def check_yaml_files():
    """Check all YAML files for syntax errors"""
    print_header("YAML SYNTAX CHECK")
    
    yaml_files = ['config.yaml', 'docker-compose.yml']
    errors = []
    
    for file in yaml_files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    yaml.safe_load(f)
                print(f"{GREEN}✅{RESET} {file} is valid")
            except yaml.YAMLError as e:
                errors.append(f"{file}: {e}")
                print(f"{RED}❌{RESET} {file}: {e}")
        else:
            print(f"{YELLOW}⚠️{RESET}  {file} not found")
    
    return len(errors) == 0

def check_docker_config():
    """Check Docker configuration"""
    print_header("DOCKER CONFIGURATION CHECK")
    
    issues = []
    
    # Check docker-compose.yml
    if os.path.exists('docker-compose.yml'):
        with open('docker-compose.yml', 'r') as f:
            try:
                config = yaml.safe_load(f)
                services = config.get('services', {})
                
                required_services = ['redis', 'tracker', 'webapp', 'dataapi']
                for service in required_services:
                    if service in services:
                        print(f"{GREEN}✅{RESET} Service '{service}' configured")
                    else:
                        issues.append(f"Missing service: {service}")
                        print(f"{RED}❌{RESET} Missing service: {service}")
                        
            except Exception as e:
                issues.append(f"docker-compose.yml: {e}")
    else:
        issues.append("docker-compose.yml not found")
    
    return len(issues) == 0

def check_websocket_config():
    """Check WebSocket configuration for common issues"""
    print_header("WEBSOCKET CONFIGURATION CHECK")
    
    issues = []
    
    # Check environment variables and config
    config_file = 'config.yaml'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            ws_config = config.get('websocket', {})
            
            ping_interval = ws_config.get('ping_interval', 45)
            ping_timeout = ws_config.get('ping_timeout', 15)
            
            if ping_interval <= ping_timeout:
                issues.append(f"ping_interval ({ping_interval}) must be > ping_timeout ({ping_timeout})")
                print(f"{RED}❌{RESET} WebSocket: ping_interval must be > ping_timeout")
            else:
                print(f"{GREEN}✅{RESET} WebSocket: ping settings OK (interval={ping_interval}, timeout={ping_timeout})")
            
            batch_size = ws_config.get('batch_size', 200)
            if batch_size < 50:
                print(f"{YELLOW}⚠️{RESET}  Small batch_size ({batch_size}) may impact performance")
            else:
                print(f"{GREEN}✅{RESET} Batch size: {batch_size} (optimal)")
    
    return len(issues) == 0

def check_redis_config():
    """Check Redis configuration"""
    print_header("REDIS CONFIGURATION CHECK")
    
    config_file = 'config.yaml'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            redis_config = config.get('redis', {})
            
            print(f"{GREEN}✅{RESET} Redis host: {redis_config.get('host', 'redis')}")
            print(f"{GREEN}✅{RESET} Redis port: {redis_config.get('port', 6379)}")
            print(f"{GREEN}✅{RESET} Redis DB: {redis_config.get('db', 0)}")
            
            if redis_config.get('password'):
                print(f"{GREEN}✅{RESET} Redis password is set")
            else:
                print(f"{YELLOW}⚠️{RESET}  Redis password not set (OK for local)")
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("DEPENDENCIES CHECK")
    
    required = {
        'redis': '5.0.1',
        'pybit': '5.6.2',
        'requests': '2.31.0',
        'yaml': '6.0.1',  # pyyaml
        'dotenv': '1.0.0'  # python-dotenv
    }
    
    package_names = {
        'yaml': 'pyyaml',
        'dotenv': 'python-dotenv',
        'redis': 'redis',
        'pybit': 'pybit',
        'requests': 'requests'
    }
    
    missing = []
    for module, version in required.items():
        try:
            __import__(module)
            package_name = package_names.get(module, module)
            print(f"{GREEN}✅{RESET} {package_name} installed")
        except ImportError:
            package_name = package_names.get(module, module)
            missing.append(package_name)
            print(f"{RED}❌{RESET} {package_name} not installed (required: {version})")
    
    if missing:
        print(f"\n{YELLOW}Install missing packages:{RESET}")
        print(f"pip3 install {' '.join(missing)}")
    
    return len(missing) == 0

def check_file_permissions():
    """Check file permissions"""
    print_header("FILE PERMISSIONS CHECK")
    
    scripts = ['docker-start.sh', 'docker-stop.sh', 'docker-info.sh']
    issues = []
    
    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"{GREEN}✅{RESET} {script} is executable")
            else:
                issues.append(f"{script} is not executable")
                print(f"{RED}❌{RESET} {script} is not executable")
                print(f"  Fix: chmod +x {script}")
        else:
            print(f"{YELLOW}⚠️{RESET}  {script} not found")
    
    return len(issues) == 0

def check_environment():
    """Check environment configuration"""
    print_header("ENVIRONMENT CHECK")
    
    env_file = '.env'
    env_example = '.env.example'
    
    if os.path.exists(env_file):
        print(f"{GREEN}✅{RESET} .env file exists")
        
        # Check for important variables
        with open(env_file, 'r') as f:
            content = f.read()
            if 'WEBAPP_PORT' in content:
                print(f"{GREEN}✅{RESET} Service ports configured")
            if 'TELEGRAM_API_ID' in content and 'TELEGRAM_API_ID=' not in content:
                print(f"{GREEN}✅{RESET} Telegram configured")
    else:
        print(f"{YELLOW}⚠️{RESET}  .env file not found")
        if os.path.exists(env_example):
            print(f"  Create one: cp {env_example} .env")
    
    return True

def check_logs_directory():
    """Check logs directory"""
    print_header("LOGS DIRECTORY CHECK")
    
    if os.path.exists('logs'):
        if os.access('logs', os.W_OK):
            print(f"{GREEN}✅{RESET} logs/ directory exists and is writable")
        else:
            print(f"{RED}❌{RESET} logs/ directory is not writable")
            return False
    else:
        print(f"{YELLOW}⚠️{RESET}  logs/ directory not found (will be created)")
        os.makedirs('logs', exist_ok=True)
        print(f"{GREEN}✅{RESET} Created logs/ directory")
    
    return True

def main():
    """Run all checks"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}BYBIT OPTIONS PRODUCTION - ERROR CHECK{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    all_checks = [
        ("Python Syntax", check_python_syntax),
        ("YAML Files", check_yaml_files),
        ("Docker Config", check_docker_config),
        ("WebSocket Config", check_websocket_config),
        ("Redis Config", check_redis_config),
        ("Dependencies", check_dependencies),
        ("File Permissions", check_file_permissions),
        ("Environment", check_environment),
        ("Logs Directory", check_logs_directory)
    ]
    
    results = {}
    for name, check_func in all_checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"{RED}Error in {name}: {e}{RESET}")
            results[name] = False
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{name:20} {status}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}✅ ALL CHECKS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}System is ready for deployment!{RESET}")
    else:
        print(f"{YELLOW}⚠️  SOME CHECKS FAILED ({passed}/{total}){RESET}")
        print(f"Please fix the issues above before deployment.")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())