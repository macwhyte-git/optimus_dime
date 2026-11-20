import os
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv

load_dotenv()

SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
    exchange   TEXT             NOT NULL,
    symbol     TEXT             NOT NULL,
    timeframe  TEXT             NOT NULL,
    ts         TIMESTAMPTZ      NOT NULL,   -- bar open time, UTC
    open       DOUBLE PRECISION NOT NULL,
    high       DOUBLE PRECISION NOT NULL,
    low        DOUBLE PRECISION NOT NULL,
    close      DOUBLE PRECISION NOT NULL,
    volume     DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (exchange, symbol, timeframe, ts)
);
"""


def get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)


def insert_bars(exchange, symbol, timeframe, ohlcv_rows):
    """ohlcv_rows: CCXT rows of [ts_ms, open, high, low, close, volume]."""
    data = [
        (
            exchange,
            symbol,
            timeframe,
            datetime.fromtimestamp(r[0] / 1000, tz=timezone.utc),
            *r[1:6],
        )
        for r in ohlcv_rows
    ]
    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO bars
                (exchange, symbol, timeframe, ts, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            data,
        )
    return len(data)


def latest_ts(exchange, symbol, timeframe):
    """Open time of the newest stored bar, or None if there are none yet."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT max(ts) FROM bars "
            "WHERE exchange = %s AND symbol = %s AND timeframe = %s",
            (exchange, symbol, timeframe),
        ).fetchone()
    return row[0]