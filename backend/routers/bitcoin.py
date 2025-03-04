from fastapi import APIRouter, HTTPException, Depends
from ..services import bitcoin  # Import the bitcoin service (adjust import based on your project structure)

router = APIRouter(
    prefix="/bitcoin",
    tags=["Bitcoin"]
)

@router.get("/price", summary="Get current Bitcoin price in USD")
async def get_current_bitcoin_price():
    """Endpoint to retrieve the current Bitcoin price (USD)."""
    # Delegate to service function. HTTPExceptions will propagate automatically if raised.
    return await bitcoin.get_current_price()

@router.get("/price/history", summary="Get historical Bitcoin price in USD")
async def get_historical_bitcoin_price(date: str):
    """Endpoint to retrieve Bitcoin price (USD) for a specific date (format: YYYY-MM-DD)."""
    return await bitcoin.get_historical_price(date)
