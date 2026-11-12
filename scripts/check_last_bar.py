from bot.data.kraken import fetch_bars
from bot.data.storage import get_connection, load_bars

stored = load_bars(get_connection(), "kraken", "BTC/USD", 5)
fresh = fetch_bars("XBTUSD", 5)

ts = stored.index.max()
print("Newest stored bar:", ts)
print()
print("Stored in database:")
print(stored.loc[ts])
print()
print("Kraken now:")
print(fresh.loc[ts])
print()
print("Match:", stored.loc[ts].equals(fresh.loc[ts]))