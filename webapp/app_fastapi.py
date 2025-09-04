#!/usr/bin/env python3
"""
FastAPI Modular Options Web App with Dynamic Asset Management
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file

import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import redis.asyncio as redis
import httpx
import uvicorn

# FastAPI app initialization
app = FastAPI(title="Options Dashboard")

# Template configuration
templates = Jinja2Templates(directory="templates")

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Initialize Redis async client
redis_client = None

async def get_redis():
    """Get Redis connection"""
    global redis_client
    if not redis_client:
        redis_client = await redis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            decode_responses=True
        )
    return redis_client

# Pydantic models for request/response
class AssetRequest(BaseModel):
    symbol: str
    name: Optional[str] = None

class AssetManager:
    """Manages dynamic assets with persistence"""
    
    ASSETS_KEY = "config:assets"
    
    @classmethod
    def get_default_assets(cls):
        """Get default assets from environment or use hardcoded defaults"""
        assets_str = os.getenv('OPTION_ASSETS', 'BTC,ETH,SOL')
        assets_list = [a.strip() for a in assets_str.split(',')]
        
        default_names = {
            "BTC": "Bitcoin",
            "ETH": "Ethereum", 
            "SOL": "Solana",
            "MATIC": "Polygon",
            "ARB": "Arbitrum",
            "OP": "Optimism"
        }
        
        assets = {}
        for i, asset in enumerate(assets_list, 1):
            assets[asset] = {
                "name": default_names.get(asset, asset),
                "enabled": True,
                "order": i
            }
        
        return assets
    
    DEFAULT_ASSETS = property(lambda self: self.get_default_assets())
    
    @classmethod
    async def get_assets(cls) -> Dict:
        """Get all configured assets"""
        client = await get_redis()
        assets_json = await client.get(cls.ASSETS_KEY)
        if assets_json:
            return json.loads(assets_json)
        else:
            # Initialize with defaults from environment
            default_assets = cls.get_default_assets()
            await cls.save_assets(default_assets)
            return default_assets
    
    @classmethod
    async def save_assets(cls, assets: Dict) -> bool:
        """Save assets configuration"""
        try:
            client = await get_redis()
            await client.set(cls.ASSETS_KEY, json.dumps(assets))
            return True
        except Exception as e:
            print(f"Error saving assets: {e}")
            return False
    
    @classmethod
    async def add_asset(cls, symbol: str, name: str) -> Dict:
        """Add new asset"""
        assets = await cls.get_assets()
        
        # Check if already exists
        if symbol.upper() in assets:
            return {"error": f"Asset {symbol} already exists"}
        
        # Test if asset has options on Bybit
        if not await cls.test_asset(symbol):
            return {"error": f"No options found for {symbol} on Bybit"}
        
        # Add new asset
        assets[symbol.upper()] = {
            "name": name,
            "enabled": True,
            "order": len(assets) + 1,
            "added_date": datetime.now().isoformat()
        }
        
        await cls.save_assets(assets)
        
        # Update config files to make it permanent
        await cls.update_config_files(symbol.upper())
        
        return {"success": True, "message": f"Added {symbol} permanently to config"}
    
    @classmethod
    async def test_asset(cls, symbol: str) -> bool:
        """Test if asset has options on Bybit"""
        try:
            async with httpx.AsyncClient() as client:
                url = "https://api.bybit.com/v5/market/instruments-info"
                params = {
                    "category": "option",
                    "baseCoin": symbol.upper(),
                    "limit": 10
                }
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()
                
                if data.get("retCode") == 0:
                    items = data.get("result", {}).get("list", [])
                    # Check if we have at least 5 options to confirm it's a valid asset
                    return len(items) >= 5
                return False
        except Exception as e:
            print(f"Error testing asset {symbol}: {e}")
            return False
    
    @classmethod
    async def update_config_files(cls, symbol: str):
        """Update config files to include new asset permanently"""
        try:
            import re
            
            # Get current assets
            assets = await cls.get_assets()
            asset_list = ','.join(assets.keys())
            
            # Update docker-compose.yml
            docker_compose_path = Path(__file__).parent.parent / "docker-compose.yml"
            if docker_compose_path.exists():
                with open(docker_compose_path, 'r') as f:
                    content = f.read()
                
                # Update OPTION_ASSETS line
                pattern = r'(- OPTION_ASSETS=)[^\n]+'
                replacement = f'\\1{asset_list}'
                content = re.sub(pattern, replacement, content)
                
                with open(docker_compose_path, 'w') as f:
                    f.write(content)
            
            # Update .env file if exists
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('OPTION_ASSETS='):
                        lines[i] = f'OPTION_ASSETS={asset_list}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'OPTION_ASSETS={asset_list}\n')
                
                with open(env_path, 'w') as f:
                    f.writelines(lines)
            
            print(f"Updated config files with asset: {symbol}")
            return True
            
        except Exception as e:
            print(f"Error updating config files: {e}")
            return False
    
    @classmethod
    async def toggle_asset(cls, symbol: str) -> bool:
        """Enable/disable asset"""
        assets = await cls.get_assets()
        if symbol in assets:
            assets[symbol]["enabled"] = not assets[symbol]["enabled"]
            await cls.save_assets(assets)
            return True
        return False
    
    @classmethod
    async def remove_asset(cls, symbol: str) -> bool:
        """Remove asset (only if not default)"""
        assets = await cls.get_assets()
        default_assets = cls.get_default_assets()
        if symbol in assets and symbol not in default_assets:
            del assets[symbol]
            await cls.save_assets(assets)
            return True
        return False


class OptionsDataProvider:
    """Provides options data from Redis"""
    
    @staticmethod
    async def get_options_data(asset: str = "BTC", expiry: Optional[str] = None, 
                               option_type: Optional[str] = None, strike: Optional[str] = None) -> List[Dict]:
        """Get filtered options data"""
        client = await get_redis()
        
        # Get all option keys for the asset
        pattern = f"option:{asset}-*"
        keys = await client.keys(pattern)
        
        options_data = []
        # Process all keys, not just first 500
        for key in keys:
            try:
                # Get data from Redis
                data = await client.hgetall(key)
                if not data:
                    continue
                
                # Parse symbol
                symbol = key.replace("option:", "")
                parts = symbol.split("-")
                
                # Standardize expiry format if present
                if len(parts) > 1:
                    expiry_raw = parts[1]
                    # Standardize to 2-digit day format
                    import re
                    match = re.match(r'(\d{1,2})([A-Z]{3})(\d{2})', expiry_raw)
                    if match:
                        day, month, year = match.groups()
                        parts[1] = f"{int(day):02d}{month}{year}"
                
                # Filter by expiry if specified
                if expiry and expiry != "all":
                    if len(parts) > 1 and parts[1] != expiry:
                        continue
                
                # Filter by strike if specified
                if strike and strike != "all":
                    if len(parts) > 2 and parts[2] != strike:
                        continue
                
                # Filter by option type if specified
                if option_type and option_type != "all":
                    if option_type == "call" and not symbol.endswith("-C"):
                        continue
                    if option_type == "put" and not symbol.endswith("-P"):
                        continue
                
                # Format data for display
                options_data.append({
                    "symbol": symbol,
                    "expiry": parts[1] if len(parts) > 1 else "N/A",  # Already standardized above
                    "strike": parts[2] if len(parts) > 2 else "N/A",
                    "type": "Call" if "-C" in symbol else "Put",
                    "last_price": float(data.get("last_price", 0) or 0),
                    "mark_price": float(data.get("mark_price", 0) or 0),
                    "volume_24h": float(data.get("volume_24h", 0) or 0),
                    "open_interest": float(data.get("open_interest", 0) or 0),
                    "delta": float(data.get("delta", 0) or 0),
                    "gamma": float(data.get("gamma", 0) or 0),
                    "theta": float(data.get("theta", 0) or 0),
                    "vega": float(data.get("vega", 0) or 0),
                    "iv": float(data.get("mark_iv", 0) or 0),
                    "underlying": float(data.get("underlying_price", 0) or 0),
                    "index_price": float(data.get("index_price", 0) or 0)
                })
            except Exception as e:
                continue
        
        # Sort by volume
        options_data.sort(key=lambda x: x["volume_24h"], reverse=True)
        
        return options_data
    
    @staticmethod
    async def get_strikes(asset: str, expiry: Optional[str] = None) -> List[str]:
        """Get unique strike prices for an asset and expiry"""
        import re
        
        client = await get_redis()
        pattern = f"option:{asset}-*"
        
        keys = await client.keys(pattern)
        
        strikes = set()
        for key in keys:
            symbol = key.replace("option:", "")
            parts = symbol.split("-")
            
            # Standardize expiry in parts for filtering
            if len(parts) > 1:
                expiry_raw = parts[1]
                match = re.match(r'(\d{1,2})([A-Z]{3})(\d{2})', expiry_raw)
                if match:
                    day, month, year = match.groups()
                    parts[1] = f"{int(day):02d}{month}{year}"
            
            # Filter by expiry if specified
            if expiry and expiry != "all":
                if len(parts) > 1 and parts[1] != expiry:
                    continue
            
            # Add strike price
            if len(parts) > 2:
                strikes.add(parts[2])
        
        # Sort numerically
        return sorted(list(strikes), key=lambda x: float(x) if x.replace('.', '').isdigit() else 0)
    
    @staticmethod
    async def get_expiries(asset: str) -> List[str]:
        """Get unique expiry dates for an asset"""
        from datetime import datetime
        import re
        
        client = await get_redis()
        pattern = f"option:{asset}-*"
        keys = await client.keys(pattern)
        
        expiries = set()
        for key in keys:
            symbol = key.replace("option:", "")
            parts = symbol.split("-")
            if len(parts) > 1:
                expiry = parts[1]
                # Standardize format: ensure 2-digit day (e.g., 3SEP25 -> 03SEP25)
                match = re.match(r'(\d{1,2})([A-Z]{3})(\d{2})', expiry)
                if match:
                    day, month, year = match.groups()
                    standardized = f"{int(day):02d}{month}{year}"
                    expiries.add(standardized)
                else:
                    expiries.add(expiry)
        
        # Sort by actual date
        def parse_expiry(exp):
            try:
                match = re.match(r'(\d{2})([A-Z]{3})(\d{2})', exp)
                if match:
                    day, month, year = match.groups()
                    month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
                    return datetime(2000 + int(year), month_map.get(month, 1), int(day))
            except:
                pass
            return datetime(2099, 12, 31)  # Put invalid dates at end
        
        return sorted(list(expiries), key=parse_expiry)
    
    @staticmethod
    async def get_stats() -> Dict:
        """Get system statistics"""
        try:
            client = await get_redis()
            stats = await client.hgetall("stats:global")
            db_size = await client.dbsize()
            info = await client.info('memory')
            
            return {
                "total_symbols": db_size // 2,  # Rough estimate
                "messages_processed": int(stats.get("messages", 0)),
                "last_update": stats.get("last_update", "N/A"),
                "redis_memory": info.get('used_memory_human', 'N/A')
            }
        except:
            return {}


# ==================== ROUTES ====================

@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    await get_redis()

@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard"""
    assets = await AssetManager.get_assets()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets": assets
    })

@app.get("/filter", response_class=HTMLResponse)
async def filter_view(request: Request):
    """Simple filter view"""
    assets = await AssetManager.get_assets()
    return templates.TemplateResponse("simple_filter.html", {
        "request": request,
        "assets": assets
    })

@app.get("/chain", response_class=HTMLResponse)
async def options_chain(request: Request):
    """Options chain view"""
    assets = await AssetManager.get_assets()
    return templates.TemplateResponse("options_chain.html", {
        "request": request,
        "assets": assets
    })

@app.get("/api/assets")
async def get_assets():
    """Get all configured assets"""
    assets = await AssetManager.get_assets()
    return assets

@app.post("/api/assets/test")
async def test_asset(asset_request: AssetRequest):
    """Test if asset has options on Bybit"""
    symbol = asset_request.symbol.upper()
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol required")
    
    # Check if asset has options
    has_options = await AssetManager.test_asset(symbol)
    
    if has_options:
        return {"success": True, "message": f"{symbol} has options available", "symbol": symbol}
    else:
        return {"success": False, "message": f"No options found for {symbol}", "symbol": symbol}

@app.post("/api/assets/add")
async def add_asset(asset_request: AssetRequest):
    """Add new asset"""
    symbol = asset_request.symbol.upper()
    name = asset_request.name or symbol
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol required")
    
    result = await AssetManager.add_asset(symbol, name)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/assets/{symbol}/toggle")
async def toggle_asset(symbol: str):
    """Enable/disable asset"""
    success = await AssetManager.toggle_asset(symbol)
    return {"success": success}

@app.delete("/api/assets/{symbol}/remove")
async def remove_asset(symbol: str):
    """Remove asset"""
    success = await AssetManager.remove_asset(symbol)
    if success:
        return {"success": True}
    raise HTTPException(status_code=400, detail="Cannot remove default asset")

@app.get("/api/options/{asset}")
async def get_options(asset: str, expiry: str = "all", type: str = "all", strike: str = "all", 
                      limit: int = None, offset: int = 0):
    """Get options data for specific asset with optional pagination"""
    data = await OptionsDataProvider.get_options_data(asset, expiry, type, strike)
    
    # Apply pagination if limit is specified
    if limit:
        return {
            "total": len(data),
            "limit": limit,
            "offset": offset,
            "data": data[offset:offset + limit]
        }
    return data

@app.get("/api/strikes/{asset}")
async def get_strikes(asset: str, expiry: str = "all"):
    """Get available strikes for an asset and expiry"""
    strikes = await OptionsDataProvider.get_strikes(asset, expiry)
    return strikes

@app.get("/api/expiries/{asset}")
async def get_expiries(asset: str):
    """Get available expiries for an asset"""
    expiries = await OptionsDataProvider.get_expiries(asset)
    return expiries

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    stats = await OptionsDataProvider.get_stats()
    return stats

@app.get("/api/summary/{asset}")
async def get_summary(asset: str):
    """Get summary statistics for an asset"""
    import re
    from datetime import datetime
    
    client = await get_redis()
    pattern = f"option:{asset}-*"
    keys = await client.keys(pattern)
    
    # Count by type
    calls = sum(1 for k in keys if k.endswith("-C"))
    puts = sum(1 for k in keys if k.endswith("-P"))
    
    # Get unique expiries and standardize them
    expiries = set()
    for key in keys:
        parts = key.split("-")
        if len(parts) > 1:
            expiry_raw = parts[1]
            # Standardize to 2-digit day format
            match = re.match(r'(\d{1,2})([A-Z]{3})(\d{2})', expiry_raw)
            if match:
                day, month, year = match.groups()
                standardized = f"{int(day):02d}{month}{year}"
                expiries.add(standardized)
            else:
                expiries.add(expiry_raw)
    
    # Sort by actual date
    def parse_expiry(exp):
        try:
            match = re.match(r'(\d{2})([A-Z]{3})(\d{2})', exp)
            if match:
                day, month, year = match.groups()
                month_map = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
                return datetime(2000 + int(year), month_map.get(month, 1), int(day))
        except:
            pass
        return datetime(2099, 12, 31)
    
    return {
        "asset": asset,
        "total_options": len(keys),
        "calls": calls,
        "puts": puts,
        "expiries": sorted(list(expiries), key=parse_expiry),
        "expiry_count": len(expiries)
    }

@app.get("/api/stream")
async def stream():
    """Server-sent events for real-time updates"""
    async def event_generator():
        while True:
            # Get current stats
            stats = await OptionsDataProvider.get_stats()
            yield f"data: {json.dumps(stats)}\n\n"
            await asyncio.sleep(2)  # Update every 2 seconds
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == '__main__':
    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )