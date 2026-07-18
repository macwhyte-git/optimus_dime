# src/data/repository.py

import pandas as pd
from src.data.database import Database


def save_bars(df):

    db = Database()

    df.to_sql(
    "stock_bars", #table name
    db.conn, #connection
    if_exists="replace", #append or replace
    index=True,
    index_label=["symbol", "timestamp"]
    )

    db.commit()
    db.close()


def get_bars(symbol):

    db = Database()

    query = """
    SELECT *
    FROM stock_bars
    WHERE symbol = ?
    ORDER BY timestamp
    """

    df = pd.read_sql(
        query,
        db.conn,
        params=(symbol,)
    )

    db.close()

    return df