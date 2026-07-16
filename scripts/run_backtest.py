from config.trading_parameters import (
    SYMBOL,
    BACKTEST_START,
    BACKTEST_END,
    TIMEFRAME
)

from src.brokers.alpaca import get_historical_prices

df = get_historical_prices(
    symbol=SYMBOL,
    start=BACKTEST_START,
    end=BACKTEST_END,
    timeframe=TIMEFRAME
)

print(df.head())