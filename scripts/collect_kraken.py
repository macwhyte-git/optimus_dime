from bot.data.kraken import fetch_bars
from bot.data.storage import get_connection, init_db, load_bars, save_bars

SOURCE = "kraken"
SYMBOL = "BTC/USD"        # how we label it in our database
KRAKEN_PAIR = "XBTUSD"    # how Kraken names it
TIMEFRAME_MIN = 5

conn = get_connection()
init_db(conn)

df = fetch_bars(KRAKEN_PAIR, TIMEFRAME_MIN)
inserted = save_bars(conn, df, SOURCE, SYMBOL, TIMEFRAME_MIN)

print(f"Fetched {len(df)} finished bars, {inserted} were new")
print()
print(load_bars(conn, SOURCE, SYMBOL, TIMEFRAME_MIN, limit=5))

conn.close()