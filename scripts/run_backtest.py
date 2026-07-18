import pandas as pd
from src.data.database import Database
from src.data.database_repository import save_bars

#Import trading parameters
from config.trading_parameters import (
    SYMBOL,
    BACKTEST_START,
    BACKTEST_END,
    TIMEFRAME
)

#Use alpaca.py from src/brokers to get historical prices and store them in a pandas dataframe
from src.brokers.alpaca import get_historical_prices

df = get_historical_prices(
    symbol=SYMBOL,
    start=BACKTEST_START,
    end=BACKTEST_END,
    timeframe=TIMEFRAME
)

#Get the high-level information about the dataframe and print the first 5 rows
print(df.info())
print(df.head())

#Store the dataframe in a sqlite database using the Database class from src/data/database.py
db = Database()

db.create_tables()

save_bars(df)

db.commit()
db.close()