#!/usr/bin/env python3
"""
REST API for Bybit Options Data Access
Provides HTTP endpoints for querying options data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
import uvicorn
import os
import io
from datetime import datetime
from data_access import OptionsDataAccess
import pandas as pd
import json

# Initialize FastAPI app
app = FastAPI(
    title="Bybit Options Data API",
    description="REST API for accessing Bybit options data from Redis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data access
da = OptionsDataAccess()

# ==================== Health Check ====================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Bybit Options Data API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "options": "/api/options/{symbol}",
            "assets": "/api/assets/{asset}",
            "export": "/api/export"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = da.test_connection()
    stats = da.get_stats() if redis_ok else {}
    
    return {
        "status": "healthy" if redis_ok else "unhealthy",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

# ==================== Data Query Endpoints ====================

@app.get("/api/options/{symbol}")
async def get_option(symbol: str):
    """Get single option by symbol"""
    data = da.get_option(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"Option {symbol} not found")
    return data

@app.get("/api/assets/{asset}")
async def get_asset_options(
    asset: str,
    expiry: Optional[str] = None,
    min_volume: Optional[float] = 0,
    min_iv: Optional[float] = 0
):
    """Get all options for an asset with optional filters"""
    # Get base data
    if expiry:
        options = da.get_options_by_expiry(expiry, asset)
    else:
        options = da.get_options_by_asset(asset)
    
    # Apply filters
    if min_volume > 0:
        options = [o for o in options if o.get('volume_24h', 0) >= min_volume]
    
    if min_iv > 0:
        options = [o for o in options if o.get('mark_iv', 0) >= min_iv]
    
    return {
        "asset": asset,
        "count": len(options),
        "filters": {
            "expiry": expiry,
            "min_volume": min_volume,
            "min_iv": min_iv
        },
        "data": options
    }

@app.get("/api/symbols")
async def get_symbols(asset: Optional[str] = None):
    """Get all available symbols"""
    symbols = da.get_all_symbols(asset)
    return {
        "count": len(symbols),
        "asset": asset or "all",
        "symbols": symbols
    }

@app.get("/api/expiries/{asset}")
async def get_expiries(asset: str):
    """Get all expiry dates for an asset"""
    all_symbols = da.get_all_symbols(asset)
    expiries = set()
    
    for symbol in all_symbols:
        parts = symbol.split('-')
        if len(parts) > 1:
            expiries.add(parts[1])
    
    return {
        "asset": asset,
        "count": len(expiries),
        "expiries": sorted(list(expiries))
    }

@app.get("/api/strikes/{asset}")
async def get_strikes(asset: str, expiry: Optional[str] = None):
    """Get all strikes for an asset and optional expiry"""
    symbols = da.get_all_symbols(asset)
    strikes = set()
    
    for symbol in symbols:
        if expiry and expiry not in symbol:
            continue
        parts = symbol.split('-')
        if len(parts) > 2:
            try:
                strikes.add(float(parts[2]))
            except:
                pass
    
    return {
        "asset": asset,
        "expiry": expiry,
        "count": len(strikes),
        "strikes": sorted(list(strikes))
    }

# ==================== Analysis Endpoints ====================

@app.get("/api/atm/{asset}")
async def get_atm_options(asset: str, num_strikes: int = 5):
    """Get at-the-money options"""
    options = da.get_atm_options(asset, num_strikes)
    return {
        "asset": asset,
        "num_strikes": num_strikes,
        "count": len(options),
        "data": options
    }

@app.get("/api/high-volume")
async def get_high_volume(min_volume: float = 100000, asset: Optional[str] = None):
    """Get high volume options"""
    options = da.get_high_volume_options(min_volume, asset)
    return {
        "min_volume": min_volume,
        "asset": asset or "all",
        "count": len(options),
        "data": options
    }

@app.get("/api/high-iv")
async def get_high_iv(min_iv: float = 1.0, asset: Optional[str] = None):
    """Get high implied volatility options"""
    options = da.get_high_iv_options(min_iv, asset)
    return {
        "min_iv": min_iv,
        "asset": asset or "all",
        "count": len(options),
        "data": options
    }

@app.get("/api/greeks/{asset}")
async def get_greeks(asset: str):
    """Get Greeks summary for an asset"""
    summary = da.get_greeks_summary(asset)
    return {
        "asset": asset,
        "summary": summary
    }

@app.get("/api/recent")
async def get_recent_updates(seconds: int = 60):
    """Get recently updated options"""
    recent = da.get_recent_updates(seconds)
    return {
        "seconds": seconds,
        "count": len(recent),
        "data": recent
    }

# ==================== Export Endpoints ====================

@app.get("/api/export/csv")
async def export_csv(asset: Optional[str] = None):
    """Export options data as CSV"""
    options = da.get_options_by_asset(asset) if asset else da.get_all_options()
    df = da.to_dataframe(options)
    
    # Create CSV in memory
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    # Return as download
    response = StreamingResponse(
        io.BytesIO(stream.getvalue().encode()),
        media_type="text/csv"
    )
    filename = f"{asset or 'all'}_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response

@app.get("/api/export/json")
async def export_json(asset: Optional[str] = None):
    """Export options data as JSON"""
    options = da.get_options_by_asset(asset) if asset else da.get_all_options()
    
    # Return as download
    response = StreamingResponse(
        io.BytesIO(json.dumps(options, default=str, indent=2).encode()),
        media_type="application/json"
    )
    filename = f"{asset or 'all'}_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response

# ==================== Statistics Endpoints ====================

@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    stats = da.get_stats()
    return stats

@app.get("/api/summary")
async def get_summary():
    """Get overall market summary"""
    all_options = da.get_all_options()
    df = da.to_dataframe(all_options)
    
    if df.empty:
        return {"error": "No data available"}
    
    summary = {
        "total_options": len(df),
        "assets": {
            "BTC": len(df[df['asset'] == 'BTC']) if 'asset' in df else 0,
            "ETH": len(df[df['asset'] == 'ETH']) if 'asset' in df else 0,
            "SOL": len(df[df['asset'] == 'SOL']) if 'asset' in df else 0
        },
        "volume": {
            "total_24h": float(df['volume_24h'].sum()) if 'volume_24h' in df else 0,
            "average": float(df['volume_24h'].mean()) if 'volume_24h' in df else 0
        },
        "open_interest": {
            "total": float(df['open_interest'].sum()) if 'open_interest' in df else 0,
            "average": float(df['open_interest'].mean()) if 'open_interest' in df else 0
        },
        "implied_volatility": {
            "mean": float(df['mark_iv'].mean()) if 'mark_iv' in df else 0,
            "min": float(df['mark_iv'].min()) if 'mark_iv' in df else 0,
            "max": float(df['mark_iv'].max()) if 'mark_iv' in df else 0
        }
    }
    
    return summary

# ==================== Custom Query Endpoint ====================

@app.post("/api/query")
async def custom_query(
    asset: Optional[str] = None,
    expiry: Optional[str] = None,
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
    option_type: Optional[str] = None,
    min_volume: Optional[float] = None,
    min_iv: Optional[float] = None,
    limit: Optional[int] = 100
):
    """Custom query with multiple filters"""
    # Start with all options or filtered by asset
    options = da.get_options_by_asset(asset) if asset else da.get_all_options()
    
    # Apply filters
    filtered = []
    for opt in options:
        # Expiry filter
        if expiry and expiry not in opt.get('symbol', ''):
            continue
        
        # Strike filter
        try:
            strike = float(opt.get('symbol', '').split('-')[2])
            if min_strike and strike < min_strike:
                continue
            if max_strike and strike > max_strike:
                continue
        except:
            pass
        
        # Type filter
        if option_type:
            if option_type.upper() == 'CALL' and not opt.get('symbol', '').endswith('-C'):
                continue
            if option_type.upper() == 'PUT' and not opt.get('symbol', '').endswith('-P'):
                continue
        
        # Volume filter
        if min_volume and opt.get('volume_24h', 0) < min_volume:
            continue
        
        # IV filter
        if min_iv and opt.get('mark_iv', 0) < min_iv:
            continue
        
        filtered.append(opt)
    
    # Apply limit
    filtered = filtered[:limit] if limit else filtered
    
    return {
        "filters": {
            "asset": asset,
            "expiry": expiry,
            "min_strike": min_strike,
            "max_strike": max_strike,
            "option_type": option_type,
            "min_volume": min_volume,
            "min_iv": min_iv
        },
        "count": len(filtered),
        "limit": limit,
        "data": filtered
    }

# ==================== WebSocket for Real-time Updates ====================

from fastapi import WebSocket
import asyncio

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Get recent updates
            recent = da.get_recent_updates(5)
            
            if recent:
                await websocket.send_json({
                    "type": "update",
                    "timestamp": datetime.now().isoformat(),
                    "count": len(recent),
                    "data": recent[:10]  # Send max 10 items
                })
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except Exception as e:
        await websocket.close()

if __name__ == "__main__":
    port = int(os.getenv('DATA_API_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)