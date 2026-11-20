"""Collect closed OHLCV bars from an exchange via CCXT into Postgres."""
import argparse
import logging
import time

import ccxt

from bot.data.storage import init_db, insert_bars, latest_ts

log = logging.getLogger("collector")

BATCH_LIMIT = 720        # Kraken's maximum bars per request
BAR_CLOSE_BUFFER_S = 5   # wait a few seconds after a bar closes before fetching


def make_exchange(exchange_id):
    return getattr(ccxt, exchange_id)({"enableRateLimit": True})


def collect(exchange, symbol, timeframe):
    """Fetch every closed bar since the newest stored one and store it.

    Returns the number of bars processed (re-fetched duplicates are ignored by
    the database)."""
    tf_ms = exchange.parse_timeframe(timeframe) * 1000
    last = latest_ts(exchange.id, symbol, timeframe)
    since_ms = int(last.timestamp() * 1000) if last else None
    total = 0
    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=BATCH_LIMIT)
        now_ms = exchange.milliseconds()
        # the newest bar is still forming, so only keep bars that have closed
        closed = [bar for bar in batch if bar[0] + tf_ms <= now_ms]
        if not closed:
            break
        total += insert_bars(exchange.id, symbol, timeframe, closed)
        next_since = closed[-1][0] + tf_ms
        if since_ms is not None and next_since <= since_ms:
            break  # no progress, avoid looping forever
        since_ms = next_since
    return total


def seconds_until_next_bar(exchange, timeframe):
    tf_ms = exchange.parse_timeframe(timeframe) * 1000
    now_ms = exchange.milliseconds()
    next_close = (now_ms // tf_ms + 1) * tf_ms
    return (next_close - now_ms) / 1000 + BAR_CLOSE_BUFFER_S


def run(exchange_id, symbol, timeframe, once=False):
    exchange = make_exchange(exchange_id)
    init_db()
    while True:
        try:
            n = collect(exchange, symbol, timeframe)
            log.info("%s %s %s: processed %d bars", exchange_id, symbol, timeframe, n)
        except (ccxt.NetworkError, ccxt.ExchangeError) as e:
            log.warning("fetch failed (%s): %s", type(e).__name__, e)
            if once:
                raise
            time.sleep(30)
            continue
        if once:
            return
        wait = seconds_until_next_bar(exchange, timeframe)
        log.info("sleeping %.0fs until the next bar", wait)
        time.sleep(wait)


def main():
    parser = argparse.ArgumentParser(description="Collect OHLCV bars into Postgres")
    parser.add_argument("--exchange", default="kraken")
    parser.add_argument("--symbol", default="BTC/USD")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--once", action="store_true", help="fetch once and exit")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        run(args.exchange, args.symbol, args.timeframe, args.once)
    except KeyboardInterrupt:
        log.info("stopped")


if __name__ == "__main__":
    main()

# Call collector with:
#  python -m bot.data.collector --once    
