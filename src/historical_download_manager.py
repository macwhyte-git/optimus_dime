# This .py file is responsible for making a historical request to the API and returns it as a df.
# It does NOT do the following:
# - save the data to a file
# - store the data in any location
# - run any calculations on the data

# Import necessary classes from the Alpaca SDK
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timezone

from config.general_settings import (
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
)
class HistoricalDownloadManager:
    def __init__(self):

        self.client = StockHistoricalDataClient(
            ALPACA_API_KEY, 
            ALPACA_SECRET_KEY
        )

