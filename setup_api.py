#!/usr/bin/env python3
"""
Setup script to configure Bybit API credentials in .env file
"""

import os
from pathlib import Path

def setup_api_credentials():
    """Interactive setup for API credentials"""
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("Creating .env file from .env.example...")
        example_file = Path('.env.example')
        if example_file.exists():
            env_content = example_file.read_text()
            env_file.write_text(env_content)
        else:
            print("Error: .env.example not found!")
            return
    
    print("\n" + "="*60)
    print("BYBIT API CONFIGURATION SETUP")
    print("="*60)
    print("\nNote: For options data, you typically don't need API keys")
    print("as the WebSocket streams are public. However, if you have")
    print("API credentials, you can add them for future features.\n")
    
    # Ask for testnet preference
    use_testnet = input("Do you want to use TESTNET? (y/N): ").lower().strip() == 'y'
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add Bybit configuration
    config_found = False
    updated_lines = []
    
    for line in lines:
        if line.startswith('BYBIT_TESTNET='):
            updated_lines.append(f'BYBIT_TESTNET={str(use_testnet).lower()}\n')
            config_found = True
        elif line.startswith('BYBIT_API_URL='):
            if use_testnet:
                updated_lines.append('BYBIT_API_URL=https://api-testnet.bybit.com/v5/market/instruments-info\n')
            else:
                updated_lines.append('BYBIT_API_URL=https://api.bybit.com/v5/market/instruments-info\n')
        elif line.startswith('BYBIT_API_KEY='):
            api_key = input("Enter your Bybit API Key (or press Enter to skip): ").strip()
            updated_lines.append(f'BYBIT_API_KEY={api_key}\n')
        elif line.startswith('BYBIT_API_SECRET='):
            api_secret = input("Enter your Bybit API Secret (or press Enter to skip): ").strip()
            updated_lines.append(f'BYBIT_API_SECRET={api_secret}\n')
        else:
            updated_lines.append(line)
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("\n" + "="*60)
    print("CONFIGURATION COMPLETE!")
    print("="*60)
    print(f"\n✅ Network: {'TESTNET' if use_testnet else 'MAINNET'}")
    print(f"✅ API URL: {'https://api-testnet.bybit.com' if use_testnet else 'https://api.bybit.com'}")
    print("\nTo apply changes, restart the Docker containers:")
    print("  docker-compose down && docker-compose up -d")
    print("\n" + "="*60)

if __name__ == "__main__":
    setup_api_credentials()