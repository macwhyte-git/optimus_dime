from bot.data.loader import load_bars, find_gaps

# 1. Ask for bars: exchange, symbol, timeframe, and optionally a start date.
df = load_bars("kraken", "BTC/USD", "5m", start="2026-11-20")

# 2. Look at what came back.
print(df.shape)         # (number of rows, number of columns)
print(df.head())        # the first 5 rows
print(df.tail(3))       # the last 3 rows

# 3. Use it: a 12-bar (one hour) moving average of the close price.
df["avg_1h"] = df["close"].rolling(12).mean()
print(df[["close", "avg_1h"]].tail())

# 4. Check the data quality.
gaps = find_gaps(df)
print("no gaps" if gaps.empty else gaps)