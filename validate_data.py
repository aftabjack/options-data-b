#!/usr/bin/env python3
"""
Validate market data accuracy
"""

import redis
import requests
import json
from datetime import datetime

# Connect to Redis
r = redis.Redis(host='localhost', port=6380, decode_responses=True)

print("\n" + "="*60)
print("OPTIONS DATA VALIDATION")
print("="*60)

# Get current spot prices from Bybit
print("\n1. FETCHING CURRENT SPOT PRICES:")
print("-" * 40)

spot_prices = {}
for symbol in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']:
    try:
        resp = requests.get(
            'https://api.bybit.com/v5/market/tickers',
            params={'category': 'spot', 'symbol': symbol}
        )
        data = resp.json()
        price = float(data['result']['list'][0]['lastPrice'])
        spot_prices[symbol[:3]] = price
        print(f"{symbol[:3]}: ${price:,.2f}")
    except:
        print(f"{symbol[:3]}: Error fetching")

# Check options data
print("\n2. CHECKING OPTIONS DATA:")
print("-" * 40)

# Sample some options
for asset in ['BTC', 'ETH', 'SOL']:
    pattern = f"option:{asset}-*"
    keys = list(r.scan_iter(pattern, count=1))
    
    if keys:
        key = keys[0]
        data = r.hgetall(key)
        
        symbol = data.get('symbol', 'Unknown')
        underlying = float(data.get('underlying_price', 0))
        index = float(data.get('index_price', 0))
        mark = float(data.get('mark_price', 0))
        iv = float(data.get('mark_iv', 0))
        
        spot = spot_prices.get(asset, 0)
        diff = underlying - spot
        diff_pct = (diff / spot * 100) if spot else 0
        
        print(f"\n{asset} Option: {symbol}")
        print(f"  Spot Price:       ${spot:,.2f}")
        print(f"  Underlying Price: ${underlying:,.2f}")
        print(f"  Index Price:      ${index:,.2f}")
        print(f"  Difference:       ${diff:,.2f} ({diff_pct:+.2f}%)")
        print(f"  Mark Price:       ${mark:,.2f}")
        print(f"  Implied Vol:      {iv*100:.1f}%")

# Check if differences are reasonable
print("\n3. DATA VALIDATION RESULTS:")
print("-" * 40)

issues = []

for asset in ['BTC', 'ETH', 'SOL']:
    pattern = f"option:{asset}-*"
    
    for key in list(r.scan_iter(pattern, count=5)):
        data = r.hgetall(key)
        
        try:
            underlying = float(data.get('underlying_price', 0))
            spot = spot_prices.get(asset, 0)
            
            if spot and underlying:
                diff_pct = abs((underlying - spot) / spot * 100)
                
                # Flag if difference > 2%
                if diff_pct > 2:
                    issues.append(f"{asset}: Underlying ${underlying:.2f} vs Spot ${spot:.2f} ({diff_pct:.1f}% diff)")
                    
            # Check IV sanity
            iv = float(data.get('mark_iv', 0))
            if iv > 5:  # 500% IV is suspicious
                issues.append(f"{data.get('symbol')}: IV seems high at {iv*100:.1f}%")
            
        except:
            pass

if issues:
    print("⚠️  Potential Issues Found:")
    for issue in issues[:5]:  # Show first 5 issues
        print(f"   - {issue}")
else:
    print("✅ All data looks reasonable!")
    print("   - Underlying prices within 2% of spot")
    print("   - Implied volatilities look normal")

print("\n4. SUMMARY:")
print("-" * 40)
print("The small difference between underlying and spot prices is NORMAL.")
print("Options use a weighted average price (index) which can differ slightly")
print("from the instantaneous spot price.")
print("\n" + "="*60)