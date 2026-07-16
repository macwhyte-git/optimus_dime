from datetime import datetime, timezone
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit    

# note to self that this is very specific to alapca parameters, and config values should be simple. 
# I should convert to simple values asap and have src/alapaca.py interpret and convert them.

SYMBOL = "AAPL"

BACKTEST_START = datetime(
    2026,
    7,
    1,
    14,
    30,
    tzinfo=timezone.utc    
)

BACKTEST_END = datetime(
    2026,
    7,
    1,
    21,
    0,
    tzinfo=timezone.utc
)

TIMEFRAME = TimeFrame(
    5,
    TimeFrameUnit.Minute
)  

# Options: '1Min', '5Min', '15Min', '1H', '1D'
# Options: 'Minute', 'Hour', 'Day'
