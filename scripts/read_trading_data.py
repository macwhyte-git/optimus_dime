import sqlite3
import pandas as pd

DATABASE = "data/trading_data.db"

connection = sqlite3.connect(DATABASE)

# 1. Check what tables exist
tables = pd.read_sql(
    """
    SELECT name 
    FROM sqlite_master 
    WHERE type='table'
    """,
    connection
)

print("\nTABLES:")
print(tables)


# 2. Inspect stock bars
print("\nSTOCK BARS:")
stock_bars = pd.read_sql(
    """
    SELECT *
    FROM stock_bars
    LIMIT 5
    """,
    connection
)

print(stock_bars)

print("\nSTOCK BARS INFO:")
print(stock_bars.info())


# 3. Check row count
count = pd.read_sql(
    """
    SELECT COUNT(*) AS row_count
    FROM stock_bars
    """,
    connection
)

print("\nROW COUNT:")
print(count)


# 4. Inspect trades table
print("\nTRADES:")
trades = pd.read_sql(
    """
    SELECT *
    FROM trades
    LIMIT 5
    """,
    connection
)

print(trades)


connection.close()