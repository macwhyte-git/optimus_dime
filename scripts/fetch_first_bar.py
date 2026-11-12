import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoTradesRequest

load_dotenv(override=True)

client = CryptoHistoricalDataClient(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
)

# The 19:35 bar covers 19:35:00 to 19:40:00 UTC
start = datetime(2026, 11, 12, 19, 35, tzinfo=timezone.utc)
end = datetime(2026, 11, 12, 19, 40, tzinfo=timezone.utc)

request = CryptoTradesRequest(
    symbol_or_symbols="BTC/USD",
    start=start,
    end=end,
)

trades = client.get_crypto_trades(request).df

print(trades)
print()
print("Trades in window:", len(trades))

if len(trades) > 0:
    print("Open :", trades["price"].iloc[0])
    print("High :", trades["price"].max())
    print("Low  :", trades["price"].min())
    print("Close:", trades["price"].iloc[-1])
    print("Volume:", trades["size"].sum())