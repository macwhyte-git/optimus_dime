"""Data loader: reads stored bars from the database into pandas DataFrames.

This is the READ side of the data layer. The collector and storage.py write
bars; everything that analyses them (backtester, strategies, paper broker)
reads them through here, so they all receive the same shape of data.

The loader reads no config files. The caller decides which exchanges, symbols,
timeframes and date range it wants and passes them in as arguments. Each of
the three can be a single value or a list.
"""

from collections.abc import Iterable
from datetime import datetime

import pandas as pd
from sqlalchemy import Select, select

from bot.data.storage import bars

# --- Section 1: the shape of the data we return -----------------------------

# The columns that say WHICH market a bar belongs to. They are returned in
# every DataFrame, even for a single market, so the shape never depends on
# what was asked for. Code that works for one symbol keeps working when
# someone passes two.
LABEL_COLUMNS = ["exchange", "symbol", "timeframe"]

# The column that becomes the DataFrame's index (its row labels). Time is the
# natural label for a bar, and it makes slicing by date and calculating
# rolling averages straightforward.
INDEX_COLUMN = "ts"

# The numeric columns, in the order they appear in the DataFrame.
VALUE_COLUMNS = ["open", "high", "low", "close", "volume"]

# Every column in the returned DataFrame, apart from the index.
OUTPUT_COLUMNS = [*LABEL_COLUMNS, *VALUE_COLUMNS]

# Check these names against the real table as soon as this module is imported.
# If storage.py ever changes (a column renamed, say) and these lists are not
# updated, we want an immediate, specific error here, not a vague failure later
# in the middle of a query. bars.c is the table's collection of columns.
_missing = [name for name in [INDEX_COLUMN, *OUTPUT_COLUMNS] if name not in bars.c.keys()]
if _missing:
    raise ImportError(
        f"loader.py expects these columns but the 'bars' table does not have them: "
        f"{', '.join(_missing)}"
    )

# --- Section 2: building the query ------------------------------------------

def _as_list(value, name: str) -> list[str]:
    """Accept one string or several, and always return a list of strings.

    "kraken"             -> ["kraken"]
    ["kraken", "bitstamp"] -> ["kraken", "bitstamp"]

    A string must be checked FIRST: in Python a string is itself a collection
    of characters, so treating "kraken" as a list would give ['k', 'r', 'a', ...].
    An empty list is rejected, because it would silently return no bars (or,
    worse, tempt someone to read it as "no filter, give me everything").
    Duplicates are dropped, keeping the order.
    """
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Iterable):
        items = list(value)
    else:
        raise TypeError(f"'{name}' must be a string or a list of strings, got {type(value).__name__}")

    if not items:
        raise ValueError(f"'{name}' needs at least one value; got an empty list")
    wrong = [item for item in items if not isinstance(item, str)]
    if wrong:
        raise TypeError(f"'{name}' must contain only strings, but got: {wrong}")

    return list(dict.fromkeys(items))  # dict keys are unique and keep their order


def _to_utc(value, name: str) -> datetime | None:
    """Turn a date into a timezone-aware UTC datetime, or None if not given.

    Accepts text ("2026-11-17", "2026-11-17 08:30"), a datetime, or a pandas
    Timestamp. A date with NO time zone is taken to be UTC, because that is
    how every timestamp in the database is stored. A date that DOES carry a
    zone is converted to UTC. Comparing like with like avoids bars being
    shifted by hours.
    """
    if value is None:
        return None
    try:
        ts = pd.Timestamp(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"'{name}' is not a date I can read: {value!r}") from e
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return ts.to_pydatetime()


def build_query(
    exchanges,
    symbols,
    timeframes,
    start=None,
    end=None,
) -> Select:
    """Build the SELECT that fetches bars for the requested markets and dates.

    Each of exchanges, symbols and timeframes can be one string or a list.
    A bar is returned if its exchange, symbol AND timeframe are each among the
    values requested. start is INCLUSIVE and end is EXCLUSIVE:

        start="2026-11-17", end="2026-11-18"  ->  every bar on the 17th, none on the 18th

    so consecutive ranges can be chained without a bar being counted twice or
    skipped. Leave start and/or end as None for no limit on that side.

    Nothing is executed here. We only describe the query, which lets us look
    at the SQL before it runs. Values reach the database as bound parameters,
    never pasted into the SQL text.
    """
    exchanges = _as_list(exchanges, "exchanges")
    symbols = _as_list(symbols, "symbols")
    timeframes = _as_list(timeframes, "timeframes")
    start_utc = _to_utc(start, "start")
    end_utc = _to_utc(end, "end")

    if start_utc and end_utc and start_utc >= end_utc:
        raise ValueError(f"'start' ({start_utc}) must be earlier than 'end' ({end_utc})")

    # The index column first, then the label and value columns, in a fixed
    # order, so every DataFrame the loader makes has the same layout.
    columns = [bars.c[name] for name in [INDEX_COLUMN, *OUTPUT_COLUMNS]]

    stmt = (
        select(*columns)
        .where(bars.c.exchange.in_(exchanges))      # exchange IN ('kraken', ...)
        .where(bars.c.symbol.in_(symbols))
        .where(bars.c.timeframe.in_(timeframes))
    )
    if start_utc is not None:
        stmt = stmt.where(bars.c.ts >= start_utc)   # start: inclusive
    if end_utc is not None:
        stmt = stmt.where(bars.c.ts < end_utc)      # end: exclusive

    # Group each market's bars together, oldest first within each market.
    return stmt.order_by(bars.c.exchange, bars.c.symbol, bars.c.timeframe, bars.c.ts)