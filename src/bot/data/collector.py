"""Collect closed OHLCV bars from an exchange via CCXT into Postgres.

Which exchange, symbol and timeframe to collect (and how the collector
behaves) comes from config/collector.yaml, never from this code. To change
what is collected, change the config and restart.
"""

import logging

from bot.config import load_config, require_keys

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