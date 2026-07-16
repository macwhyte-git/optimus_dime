import pandas as pd
from datetime import datetime, timezone

# Import necessary classes from the Alpaca SDK
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

#assign api key and secret key from environment variables
from config.general_settings import ( 
    ALPACA_API_KEY, 
    ALPACA_API_SECRET
)

#if api key or secret key is not found, raise an error // how does this work? 
if not ALPACA_API_KEY:
    raise ValueError(
        "API_KEY not found in general_settings.py variables"
    )
if not ALPACA_API_SECRET:
    raise ValueError(
        "API_SECRET not found in general_settings.py variables"
    )

# Initialize the Stock Historical Data Client
client = StockHistoricalDataClient(
    ALPACA_API_KEY, 
    ALPACA_API_SECRET
)

def get_historical_prices(
        symbol, 
        start, 
        end,
        timeframe
):

    request_params = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=timeframe,
        start=start,
        end=end,
    )

    bars = client.get_stock_bars(request_params)

# Convert the bars to a pandas DataFrame for easier manipulation
    df = bars.df

    return df
