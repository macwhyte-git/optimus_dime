#Import trading parameters
from config.trading_parameters import (
    SYMBOL,
    BACKTEST_START,
    BACKTEST_END,
    TIMEFRAME
)

#Use alpaca.py from src/brokers to get historical prices and store them in a pandas dataframe
from src.brokers.alpaca import get_historical_prices
from src.data.database_repository import save_bars

df = get_historical_prices(
    symbol=SYMBOL,
    start=BACKTEST_START,
    end=BACKTEST_END,
    timeframe=TIMEFRAME
)

#print(df.head())
#print(f"Downloaded {len(df)} bars")

from src.data.database import Database
db = Database()
db.create_tables()
db.close()

save_bars(df)

print("Historical data saved.")