import os
import pandas as pd
# Import necessary classes from the Alpaca SDK
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timezone

#Plotly for visualization
#https://plotly.com/python/candlestick-charts/ - documentation for using plotly library
import plotly.graph_objects as go

# API Documentation:
# https://alpaca.markets/sdks/python/market_data.html

# interact with dotenv to load environment variables
from dotenv import load_dotenv
#load dotenv
load_dotenv()

#assign api key and secret key from environment variables
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_API_SECRET')

#if api key or secret key is not found, raise an error // how does this work? 
if not API_KEY:
    raise ValueError("API_KEY not found in environment variables")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in environment variables")

# Initialize the Stock Historical Data Client
client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

request_params = StockBarsRequest(
    symbol_or_symbols=["AAPL", "MSFT"],
    timeframe=TimeFrame.Day,
    start=datetime(2025, 12, 15, tzinfo=timezone.utc),
    end=datetime(2025, 12, 21, tzinfo=timezone.utc),
)

bars = client.get_stock_bars(request_params)

# Convert the bars to a pandas DataFrame for easier manipulation
bars.df

# access bars as list - important to note that you must access by symbol key
# even for a single symbol request - models are agnostic to number of symbols
print(bars["AAPL"])
print(bars["MSFT"])

