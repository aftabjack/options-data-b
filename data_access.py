#!/usr/bin/env python3
"""
Redis Data Access Module for Bybit Options
Provides clean interface to access options data from other scripts
"""

from dotenv import load_dotenv
load_dotenv()

import os
import redis
import json
import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import numpy as np

class OptionsDataAccess:
    """Clean interface for accessing options data from Redis"""
    
    def __init__(self, host: str = None, port: int = None, db: int = None):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=host or os.getenv('REDIS_HOST', 'localhost'),
            port=port or int(os.getenv('REDIS_PORT', 6379)),
            db=db or int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        
    def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    # ==================== Basic Data Access ====================
    
    def get_option(self, symbol: str) -> Dict:
        """Get single option data by symbol"""
        data = self.redis_client.hgetall(f"option:{symbol}")
        if data:
            # Convert string values to appropriate types
            return self._parse_option_data(data)
        return {}
    
    def get_all_symbols(self, asset: str = None) -> List[str]:
        """Get all option symbols, optionally filtered by asset"""
        pattern = f"option:{asset}-*" if asset else "option:*"
        keys = self.redis_client.keys(pattern)
        return [key.replace("option:", "") for key in keys]
    
    def get_options_by_asset(self, asset: str) -> List[Dict]:
        """Get all options for a specific asset (BTC, ETH, SOL)"""
        symbols = self.get_all_symbols(asset)
        options = []
        for symbol in symbols:
            data = self.get_option(symbol)
            if data:
                options.append(data)
        return options
    
    def get_options_by_expiry(self, expiry: str, asset: str = None) -> List[Dict]:
        """Get all options for a specific expiry date"""
        all_symbols = self.get_all_symbols(asset)
        options = []
        for symbol in all_symbols:
            if f"-{expiry}-" in symbol:
                data = self.get_option(symbol)
                if data:
                    options.append(data)
        return options
    
    def get_options_by_strike(self, strike: float, asset: str = None) -> List[Dict]:
        """Get all options for a specific strike price"""
        all_symbols = self.get_all_symbols(asset)
        options = []
        strike_str = str(int(strike))
        for symbol in all_symbols:
            if f"-{strike_str}-" in symbol:
                data = self.get_option(symbol)
                if data:
                    options.append(data)
        return options
    
    # ==================== Advanced Queries ====================
    
    def get_atm_options(self, asset: str, num_strikes: int = 5) -> List[Dict]:
        """Get at-the-money options (closest strikes to spot price)"""
        options = self.get_options_by_asset(asset)
        if not options:
            return []
        
        # Get underlying price
        spot_price = self._get_spot_price(options)
        if not spot_price:
            return []
        
        # Sort by distance from spot
        for opt in options:
            try:
                strike = self._extract_strike(opt['symbol'])
                opt['distance_from_spot'] = abs(strike - spot_price)
            except:
                opt['distance_from_spot'] = float('inf')
        
        options.sort(key=lambda x: x['distance_from_spot'])
        return options[:num_strikes * 2]  # Calls and puts
    
    def get_high_volume_options(self, min_volume: float = 100000, asset: str = None) -> List[Dict]:
        """Get options with high trading volume"""
        options = self.get_options_by_asset(asset) if asset else self.get_all_options()
        return [opt for opt in options if opt.get('volume_24h', 0) >= min_volume]
    
    def get_high_iv_options(self, min_iv: float = 1.0, asset: str = None) -> List[Dict]:
        """Get options with high implied volatility"""
        options = self.get_options_by_asset(asset) if asset else self.get_all_options()
        return [opt for opt in options if opt.get('mark_iv', 0) >= min_iv]
    
    def get_all_options(self) -> List[Dict]:
        """Get all options data"""
        symbols = self.get_all_symbols()
        options = []
        for symbol in symbols:
            data = self.get_option(symbol)
            if data:
                options.append(data)
        return options
    
    # ==================== DataFrame Export ====================
    
    def to_dataframe(self, options: List[Dict] = None) -> pd.DataFrame:
        """Convert options data to pandas DataFrame"""
        if options is None:
            options = self.get_all_options()
        
        if not options:
            return pd.DataFrame()
        
        df = pd.DataFrame(options)
        
        # Parse symbol components
        if 'symbol' in df.columns:
            df['asset'] = df['symbol'].apply(lambda x: x.split('-')[0] if '-' in x else '')
            df['expiry'] = df['symbol'].apply(lambda x: x.split('-')[1] if len(x.split('-')) > 1 else '')
            df['strike'] = df['symbol'].apply(lambda x: self._extract_strike(x))
            df['type'] = df['symbol'].apply(lambda x: 'Call' if x.endswith('-C') else 'Put')
        
        # Convert timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df
    
    def export_to_csv(self, filename: str, asset: str = None):
        """Export options data to CSV file"""
        options = self.get_options_by_asset(asset) if asset else self.get_all_options()
        df = self.to_dataframe(options)
        df.to_csv(filename, index=False)
        return len(df)
    
    def export_to_json(self, filename: str, asset: str = None):
        """Export options data to JSON file"""
        options = self.get_options_by_asset(asset) if asset else self.get_all_options()
        with open(filename, 'w') as f:
            json.dump(options, f, indent=2, default=str)
        return len(options)
    
    # ==================== Greeks Analysis ====================
    
    def get_greeks_summary(self, asset: str) -> Dict:
        """Get summary statistics of Greeks for an asset"""
        options = self.get_options_by_asset(asset)
        if not options:
            return {}
        
        df = self.to_dataframe(options)
        
        return {
            'delta': {
                'mean': df['delta'].mean() if 'delta' in df else 0,
                'std': df['delta'].std() if 'delta' in df else 0,
                'min': df['delta'].min() if 'delta' in df else 0,
                'max': df['delta'].max() if 'delta' in df else 0
            },
            'gamma': {
                'mean': df['gamma'].mean() if 'gamma' in df else 0,
                'max': df['gamma'].max() if 'gamma' in df else 0
            },
            'theta': {
                'total': df['theta'].sum() if 'theta' in df else 0,
                'mean': df['theta'].mean() if 'theta' in df else 0
            },
            'vega': {
                'total': df['vega'].sum() if 'vega' in df else 0,
                'mean': df['vega'].mean() if 'vega' in df else 0
            }
        }
    
    # ==================== Real-time Monitoring ====================
    
    def get_recent_updates(self, seconds: int = 60) -> List[Dict]:
        """Get options updated in the last N seconds"""
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - seconds
        
        options = self.get_all_options()
        recent = []
        for opt in options:
            if opt.get('timestamp', 0) >= cutoff_time:
                recent.append(opt)
        
        return sorted(recent, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    def monitor_option(self, symbol: str) -> Dict:
        """Get real-time monitoring data for a specific option"""
        data = self.get_option(symbol)
        if not data:
            return {}
        
        # Add calculated fields
        data['spread'] = data.get('ask_price', 0) - data.get('bid_price', 0)
        data['spread_pct'] = (data['spread'] / data.get('mark_price', 1)) * 100 if data.get('mark_price') else 0
        
        return data
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict:
        """Get overall system statistics"""
        stats = self.redis_client.hgetall("stats:global")
        db_size = self.redis_client.dbsize()
        
        return {
            'total_options': len(self.get_all_symbols()),
            'total_keys': db_size,
            'btc_options': len(self.get_all_symbols('BTC')),
            'eth_options': len(self.get_all_symbols('ETH')),
            'sol_options': len(self.get_all_symbols('SOL')),
            'messages_processed': int(stats.get('messages', 0)),
            'last_update': stats.get('last_update', 'N/A')
        }
    
    # ==================== Helper Methods ====================
    
    def _parse_option_data(self, data: Dict) -> Dict:
        """Parse option data with type conversion"""
        parsed = {'symbol': data.get('symbol', '')}
        
        # Float fields
        float_fields = [
            'last_price', 'mark_price', 'index_price', 'mark_iv',
            'underlying_price', 'bid_price', 'ask_price', 'open_interest',
            'volume_24h', 'turnover_24h', 'delta', 'gamma', 'theta', 'vega',
            'bid_size', 'ask_size', 'bid_iv', 'ask_iv'
        ]
        
        for field in float_fields:
            if field in data:
                try:
                    parsed[field] = float(data[field])
                except (ValueError, TypeError):
                    parsed[field] = 0.0
        
        # Timestamp
        if 'timestamp' in data:
            try:
                parsed['timestamp'] = float(data['timestamp'])
            except:
                parsed['timestamp'] = 0
        
        return parsed
    
    def _extract_strike(self, symbol: str) -> float:
        """Extract strike price from symbol"""
        try:
            parts = symbol.split('-')
            if len(parts) >= 3:
                return float(parts[2])
        except:
            pass
        return 0.0
    
    def _get_spot_price(self, options: List[Dict]) -> Optional[float]:
        """Get underlying spot price from options"""
        for opt in options:
            if 'underlying_price' in opt and opt['underlying_price'] > 0:
                return opt['underlying_price']
        return None


# ==================== Convenience Functions ====================

def quick_access():
    """Quick access function for interactive use"""
    return OptionsDataAccess()

def get_btc_options():
    """Shortcut to get all BTC options"""
    da = OptionsDataAccess()
    return da.get_options_by_asset('BTC')

def get_eth_options():
    """Shortcut to get all ETH options"""
    da = OptionsDataAccess()
    return da.get_options_by_asset('ETH')

def get_sol_options():
    """Shortcut to get all SOL options"""
    da = OptionsDataAccess()
    return da.get_options_by_asset('SOL')

def export_all_to_csv(filename: str = 'options_data.csv'):
    """Export all options to CSV"""
    da = OptionsDataAccess()
    count = da.export_to_csv(filename)
    print(f"Exported {count} options to {filename}")
    return count