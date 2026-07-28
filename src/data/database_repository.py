# src/data/repository.py

import pandas as pd
from src.data.database import Database
from src.data.schema import INSERT_STOCK_BAR

#Prepare the dataframe for saving to the database by ensuring that the required columns are present and that the data types are correct
def prepare_bars(df):

    df = df.reset_index()

    required_columns = [
        "symbol",
        "timestamp",
        "open",
        "high",
        "low",
        "close"
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["timestamp"] = df["timestamp"].astype(str)
    df["volume"] = df["volume"].fillna(0).astype(int)
    df["trade_count"] = df["trade_count"].fillna(0).astype(int)

    return df

def save_bars(df):

#Converts floats in the data to integers to avoid issues with sqlite3 database
    df = prepare_bars(df)
    #temp QA code starts
    print(df.dtypes)
    print(type(df["timestamp"].iloc[0]))
    print(df.head())
    #temp QA code ends
    db = Database()

    cursor = db.cursor()

    inserted = 0

    for row in df.itertuples(index=False):

        cursor.execute(
            INSERT_STOCK_BAR,
            (
                row.symbol,
                row.timestamp,
                row.open,
                row.high,
                row.low,
                row.close,
                row.volume,
                row.trade_count,
                row.vwap,
            )
        )
        inserted += cursor.rowcount
    db.commit()
    print(f"Inserted {inserted} new bars.")
    db.close()

def get_bars(symbol, start_timestamp=None, end_timestamp=None):

    db = Database()

    query = """
    SELECT *
    FROM stock_bars
    WHERE symbol = ?
    """
    
    params = [symbol]

    if start_timestamp:
        query += "\nAND timestamp >= ?"
        params.append(start_timestamp)

    if end_timestamp:
        query += "\nAND timestamp <= ?"
        params.append(end_timestamp)

    query += "\nORDER BY timestamp"
    
    df = pd.read_sql(
    query,
    db.conn,
    params=params
    )

    db.close()

    return df