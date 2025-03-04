import httpx
from datetime import datetime, date as date_cls, timezone
from fastapi import HTTPException

# API endpoints for primary and backup services
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
COINGECKO_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date}"  # date in DD-MM-YYYY format
KRAKEN_TICKER_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440&since={since}"
COINDESK_CURRENT_URL = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
COINDESK_HISTORICAL_URL = "https://api.coindesk.com/v1/bpi/historical/close.json?start={date}&end={date}"

async def get_current_price():
    """Fetch the current Bitcoin price in USD, with failover to Kraken and CoinDesk."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Try CoinGecko API for current price
        try:
            resp = await client.get(COINGECKO_PRICE_URL)
        except Exception:
            resp = None
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                # CoinGecko simple price returns {"bitcoin": {"usd": <price>}}
                price = data["bitcoin"]["usd"]
                if price is not None:
                    return {"USD": price}
            except Exception:
                # Parsing failure or unexpected format
                pass

        # 2. If CoinGecko failed, try Kraken API for current price
        try:
            resp = await client.get(KRAKEN_TICKER_URL)
        except Exception:
            resp = None
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                # Kraken returns error list; ensure it's empty for success&#8203;:contentReference[oaicite:5]{index=5}
                if data.get("error") == []:
                    result = data.get("result")
                    if result:
                        # The key for BTC/USD pair (e.g. "XXBTZUSD") contains the price in "c"
                        pair = next(iter(result))
                        price_str = result[pair]["c"][0]  # last trade price (string)
                        price = float(price_str)
                        return {"USD": price}
            except Exception:
                pass

        # 3. If Kraken failed, try CoinDesk API for current price
        try:
            resp = await client.get(COINDESK_CURRENT_URL)
        except Exception:
            resp = None
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                # CoinDesk current price returns JSON with bpi.USD.rate_float&#8203;:contentReference[oaicite:6]{index=6}
                price = data["bpi"]["USD"]["rate_float"]
                if price is not None:
                    return {"USD": price}
            except Exception:
                pass

    # If all APIs failed, raise an HTTP 502 Bad Gateway
    raise HTTPException(
        status_code=502,
        detail="Unable to retrieve current Bitcoin price from CoinGecko, Kraken, or backup API."
    )

async def get_historical_price(date: str):
    """Fetch the historical Bitcoin price (USD) for a given date (YYYY-MM-DD), with failover."""
    # Validate date format
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    # Disallow future dates
    if target_date > date_cls.today():
        raise HTTPException(status_code=400, detail="Date cannot be in the future.")

    # Format dates for each API
    coingecko_date = target_date.strftime("%d-%m-%Y")  # CoinGecko requires DD-MM-YYYY
    coindesk_date = target_date.strftime("%Y-%m-%d")   # CoinDesk uses YYYY-MM-DD

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Try CoinGecko API for historical price
        try:
            resp = await client.get(COINGECKO_HISTORY_URL.format(date=coingecko_date))
        except Exception:
            resp = None
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                # CoinGecko history returns price under market_data.current_price.usd&#8203;:contentReference[oaicite:7]{index=7}
                market_data = data.get("market_data")
                if market_data and "current_price" in market_data:
                    price = market_data["current_price"].get("usd")
                    if price is not None:
                        return {"USD": price}
            except Exception:
                pass

        # 2. If CoinGecko failed, try Kraken API for historical price (daily OHLC)
        # Prepare Unix timestamp for the target date at 00:00:00 UTC
        dt_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        timestamp = int(dt_start.timestamp())
        try:
            resp = await client.get(KRAKEN_OHLC_URL.format(since=timestamp))
        except Exception:
            resp = None
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                if data.get("error") == []:
                    result = data.get("result")
                    if result:
                        pair = next(iter(result))  # e.g., "XXBTZUSD"
                        ohlc_data = result.get(pair, [])
                        # Each OHLC entry: [time, open, high, low, close, vwap, volume, count]&#8203;:contentReference[oaicite:8]{index=8}
                        for entry in ohlc_data:
                            if len(entry) >= 5 and int(entry[0]) == timestamp:
                                # Use the open price at 00:00 UTC of that day
                                price = float(entry[1])
                                return {"USD": price}
                        # If exact timestamp not found, use the first entry's open as fallback
                        if ohlc_data:
                            price = float(ohlc_data[0][1])
                            return {"USD": price}
            except Exception:
                pass

        # 3. If Kraken failed, try CoinDesk API for historical price
        try:
            resp = await client.get(COINDESK_HISTORICAL_URL.format(date=coindesk_date))
        except Exception:
            resp = None
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                # CoinDesk historical returns a 'bpi' dict of dates to prices&#8203;:contentReference[oaicite:9]{index=9}
                bpi = data.get("bpi", {})
                # Get the price for the target date key
                if coindesk_date in bpi:
                    price = bpi[coindesk_date]
                    if price is not None:
                        return {"USD": price}
            except Exception:
                pass

    # If all sources fail, return an HTTP 502 error
    raise HTTPException(
        status_code=502,
        detail="Unable to retrieve Bitcoin price for the given date from CoinGecko, Kraken, or backup API."
    )
