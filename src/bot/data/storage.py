"""Storage layer: everything that talks to the PostgreSQL database.

Built with SQLAlchemy Core on top of the psycopg driver. Other modules import
functions from here and never touch the database directly.
"""

import os
from datetime import datetime, timezone
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Double,
    MetaData,
    PrimaryKeyConstraint,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import URL, Engine, make_url

# --- Section 1: settings ----------------------------------------------------

# Name of the environment variable that holds the database URL. Kept as a
# constant so a different database (for example a test one) can be used by
# pointing this at another variable, with no other code changes.
DB_URL_ENV_VAR = "DATABASE_URL"

# Name of the table that stores price bars. Change it here to store bars
# somewhere else (for example a scratch table for experiments).
BARS_TABLE_NAME = "bars"

# Read the .env file once, when this module is first imported, and copy its
# lines into the process environment so os.environ can see them.
load_dotenv()


# --- Section 2: engine ------------------------------------------------------

def _build_url() -> URL:
    """Read the database URL from the environment and make it psycopg 3 ready.

    A plain 'postgresql://' URL makes SQLAlchemy look for the older psycopg2
    driver, so that scheme is swapped for 'postgresql+psycopg://'.
    os.environ[...] raises KeyError if the variable is missing, which is
    deliberate: fail loudly rather than connect to nothing.
    """
    url = make_url(os.environ[DB_URL_ENV_VAR])
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the shared engine, creating it on the first call only.

    lru_cache(maxsize=1) remembers the result, so every later call returns the
    same engine (and therefore the same connection pool). The engine does not
    connect until it is first used. pool_pre_ping=True tests a pooled
    connection before handing it out, so a dropped connection is replaced
    instead of causing an error.
    """
    return create_engine(_build_url(), pool_pre_ping=True)


# --- Section 3: table definition --------------------------------------------

# MetaData is a registry. Every Table below is attached to it, so a single
# call (create_all, in Section 4) can create all of them.
metadata = MetaData()

# One row per price bar. The same table holds any exchange, symbol and
# timeframe, because those three values are columns, not separate tables.
bars = Table(
    BARS_TABLE_NAME,
    metadata,
    Column("exchange", Text, nullable=False),
    Column("symbol", Text, nullable=False),
    Column("timeframe", Text, nullable=False),
    Column("ts", DateTime(timezone=True), nullable=False),  # bar open time, UTC
    Column("open", Double, nullable=False),
    Column("high", Double, nullable=False),
    Column("low", Double, nullable=False),
    Column("close", Double, nullable=False),
    Column("volume", Double, nullable=False),
    # Two rows can never share the same market and bar time. This is what lets
    # us re-insert overlapping bars safely. Postgres builds an index for it.
    PrimaryKeyConstraint("exchange", "symbol", "timeframe", "ts"),
)

# --- Section 4: creating the table ------------------------------------------

def init_db() -> None:
    """Create any tables defined above that do not exist yet.

    create_all first asks the database which tables exist, then creates only
    the missing ones, so it is safe to call on every start-up. It never alters
    or drops an existing table. The engine opens a connection, runs the
    statements in a transaction and commits.
    """
    metadata.create_all(get_engine())

    # --- Section 5: writing bars ------------------------------------------------

def _ohlcv_to_dicts(exchange: str, symbol: str, timeframe: str, ohlcv_rows) -> list[dict]:
    """Turn CCXT rows into dicts keyed by column name.

    A CCXT row is [ts_ms, open, high, low, close, volume]. The three labels
    (exchange, symbol, timeframe) are not in the row, so the caller passes
    them in. The millisecond timestamp becomes a timezone-aware UTC datetime.
    """
    return [
        {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "ts": datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
        }
        for row in ohlcv_rows
    ]


def insert_bars(exchange: str, symbol: str, timeframe: str, ohlcv_rows) -> int:
    """Store bars, skipping any that already exist. Returns how many were new.

    ON CONFLICT DO NOTHING makes this safe to repeat: a bar whose primary key
    already exists is ignored instead of raising an error. RETURNING sends
    back one row per bar that was really inserted, so counting them gives the
    number of new bars. engine.begin() opens a connection and a transaction,
    commits if the block succeeds and rolls back if it raises.
    """
    rows = _ohlcv_to_dicts(exchange, symbol, timeframe, ohlcv_rows)
    if not rows:
        return 0
    stmt = pg_insert(bars).on_conflict_do_nothing().returning(bars.c.ts)
    with get_engine().begin() as conn:
        result = conn.execute(stmt, rows)
        return len(result.all())