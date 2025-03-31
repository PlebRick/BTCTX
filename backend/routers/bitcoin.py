from fastapi import APIRouter, HTTPException, Depends, Query
from ..services import bitcoin  # Adjust the import path if needed

router = APIRouter(
    tags=["Bitcoin"]
)

@router.get("/price", summary="Get current Bitcoin price in USD")
async def get_current_bitcoin_price():
    """
    Endpoint to retrieve the current Bitcoin price (USD).
    Leverages fallback logic in services/bitcoin.py.
    Raises HTTP 502 if all providers fail.
    """
    return await bitcoin.get_current_price()


@router.get("/price/history", summary="Get historical Bitcoin price (one date)")
async def get_historical_bitcoin_price(date: str):
    """
    Endpoint to retrieve Bitcoin price (USD) for a specific date.
    Format: YYYY-MM-DD
    
    If you only need multi‐day time‐series,
    you can remove or rename this single‐day route.
    """
    return await bitcoin.get_historical_price(date)


@router.get("/price/history/timeseries", summary="Get multi-day BTC price data")
async def get_btc_price_time_series(
    days: int = Query(7, ge=1, le=365, description="Number of days (1 to 365)")
):
    """
    Returns daily BTC prices for the last `days` days in USD, 
    suitable for line charts (time-series).
    
    The services/bitcoin.py should have get_time_series(days)
    that fetches from CoinGecko (fallback to Kraken, etc.).
    """
    return await bitcoin.get_time_series(days)
