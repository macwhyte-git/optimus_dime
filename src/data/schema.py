
INSERT_STOCK_BAR = """
INSERT OR IGNORE INTO stock_bars (
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    trade_count,
    vwap
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

CREATE_STOCK_BARS_TABLE = """
CREATE TABLE IF NOT EXISTS stock_bars (
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER,
    trade_count INTEGER,
    vwap REAL,

    PRIMARY KEY(symbol, timestamp)
);
"""

CREATE_TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,

    symbol TEXT NOT NULL,

    entry_timestamp TEXT NOT NULL,
    entry_price REAL NOT NULL,

    exit_timestamp TEXT,
    exit_price REAL,

    quantity REAL NOT NULL,

    pnl REAL
);
"""
SCHEMA = [
    CREATE_STOCK_BARS_TABLE, 
    CREATE_TRADES_TABLE
    ]