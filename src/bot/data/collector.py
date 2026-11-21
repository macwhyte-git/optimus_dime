"""Collect closed OHLCV bars from an exchange via CCXT into Postgres.

Which exchange, symbol and timeframe to collect (and how the collector
behaves) comes from config/collector.yaml, never from this code. To change
what is collected, change the config and restart.
"""

import difflib
import logging

import ccxt

from bot.config import load_config, require_keys
from bot.data.storage import insert_bars, latest_ts

# --- Section 1: loading settings --------------------------------------------

# A named logger, so log lines are labelled "collector". The level and format
# are applied later, in main(), from the config file. Creating the logger here
# only gives every function in this file one logger to write to.
log = logging.getLogger("collector")

# The config file used when the caller does not name one: config/collector.yaml.
DEFAULT_CONFIG = "collector"

# Settings the collector cannot run without. Listing them here (and checking
# them at start-up) turns a typo in the YAML into one clear message, instead
# of a KeyError that surfaces halfway through a run.
REQUIRED_SETTINGS = [
    "exchange",
    "symbol",
    "timeframe",
    "bar_close_buffer_s",
    "retry_delay_s",
    "enable_rate_limit",
    "logging",
]

# Facts about the exchange that the collector needs from exchanges.yaml.
REQUIRED_EXCHANGE_FACTS = ["batch_limit"]


def load_settings(config=DEFAULT_CONFIG) -> dict:
    """Return everything this run needs, in one dictionary.

    Reads the collector's own config, then looks up the facts for the exchange
    it names in exchanges.yaml and attaches them under "exchange_facts". The
    rest of the collector receives this dictionary (or values from it) as
    arguments, rather than reading files itself. That keeps each function
    simple to test: hand it a small made-up dictionary.

    'config' is either a job name ("collector") or a path to a YAML file; the
    loader accepts both.
    """
    settings = load_config(config)
    require_keys(settings, REQUIRED_SETTINGS, source=str(config))
    require_keys(settings["logging"], ["level", "format"], source=f"{config} (logging)")

    # The exchange named in the collector config must have an entry in
    # exchanges.yaml. Checking now gives a clear error at start-up, listing
    # the known exchanges, rather than a confusing failure later.
    exchanges = load_config("exchanges")
    name = settings["exchange"]
    if name not in exchanges:
        raise ValueError(
            f"Exchange '{name}' (from {config}) has no entry in exchanges.yaml. "
            f"Known exchanges: {', '.join(exchanges)}"
        )
    facts = exchanges[name]
    require_keys(facts, REQUIRED_EXCHANGE_FACTS, source=f"exchanges.yaml ({name})")

    # Return a NEW dictionary instead of changing 'settings' in place, so the
    # loaded config is never silently modified.
    return {**settings, "exchange_facts": facts}

# --- Section 2: creating the exchange object --------------------------------

def make_exchange(exchange_id: str, enable_rate_limit: bool) -> ccxt.Exchange:
    """Return a CCXT exchange object for the exchange named in the config.

    ccxt.exchanges is CCXT's list of every exchange id it supports. Checking
    against it first lets us fail with a clear message (and a spelling
    suggestion) instead of an obscure AttributeError.

    getattr(ccxt, exchange_id) looks up the class ccxt.kraken (or ccxt.coinbase,
    and so on) from a string. That lookup is what lets the exchange be chosen
    by a config value instead of by editing code.

    enableRateLimit makes CCXT pace its own requests so we stay inside the
    exchange's limits. (The camelCase spelling is CCXT's, not ours.)
    """
    if exchange_id not in ccxt.exchanges:
        hint = difflib.get_close_matches(exchange_id, ccxt.exchanges, n=3)
        suggestion = f" Did you mean: {', '.join(hint)}?" if hint else ""
        raise ValueError(f"'{exchange_id}' is not a CCXT exchange id.{suggestion}")

    exchange = getattr(ccxt, exchange_id)({"enableRateLimit": enable_rate_limit})

    # The collector only fetches bars. Not every exchange supports that, so
    # check now. exchange.has is a dictionary of what the exchange can do; the
    # value can be True, False or "emulated", so test for truthiness.
    if not exchange.has.get("fetchOHLCV"):
        raise ValueError(f"Exchange '{exchange_id}' does not support fetching OHLCV bars.")

    return exchange

# --- Section 3: fetching and storing bars -----------------------------------

def collect(exchange: ccxt.Exchange, symbol: str, timeframe: str, batch_limit: int) -> int:
    """Fetch every closed bar since the newest stored one and store it.

    Returns the number of NEW bars stored (bars we already had don't count).

    Every value comes in as an argument, including batch_limit, so this
    function reads no files and no globals. Network errors are deliberately
    NOT caught here: whoever calls this decides what a failure means (retry,
    give up, ...). That keeps the function simple and the policy in one place.
    """
    # ccxt gives the timeframe in seconds; bar open times are in milliseconds,
    # so convert once and compare like with like.
    tf_ms = exchange.parse_timeframe(timeframe) * 1000

    # Where did we get to? latest_ts returns None if we have nothing yet, and
    # then since_ms stays None, which tells the exchange "give me the most
    # recent bars". Otherwise we restart AT the newest stored bar. Re-fetching
    # that one bar is harmless (the database ignores duplicates) and means we
    # can't skip a bar by being off by one.
    last = latest_ts(exchange.id, symbol, timeframe)
    since_ms = int(last.timestamp() * 1000) if last else None

    total_new = 0
    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=batch_limit)
        now_ms = exchange.milliseconds()

        # The newest bar is still forming, so its high, low, close and volume
        # are partial. A bar is closed once its open time plus one bar length
        # is no later than now. Storing a forming bar would put wrong data in
        # the history, so only closed bars go in.
        closed = [bar for bar in batch if bar[0] + tf_ms <= now_ms]
        if not closed:
            break  # nothing new: we are caught up

        new = insert_bars(exchange.id, symbol, timeframe, closed)
        total_new += new
        log.debug("fetched %d bars, %d closed, %d new", len(batch), len(closed), new)

        # Next fetch starts one bar after the last closed bar we saw. If that
        # point has not moved forward, the exchange is handing us the same
        # data again, so stop instead of looping forever.
        next_since = closed[-1][0] + tf_ms
        if since_ms is not None and next_since <= since_ms:
            break
        since_ms = next_since

    return total_new