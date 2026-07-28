from src.data.database_repository import get_bars
from config.trading_parameters import SYMBOL, BACKTEST_START, BACKTEST_END

df = get_bars(
    symbol=SYMBOL,
    start_timestamp=BACKTEST_START,
    end_timestamp=BACKTEST_END
)

print(df.head())
print(df.info())