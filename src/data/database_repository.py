# src/data/repository.py

import pandas as pd
from src.data.database import Database

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

    df["volume"] = df["volume"].astype("Int64")
    df["trade_count"] = df["trade_count"].astype("Int64")

    return df

def save_bars(df):

#Converts floats in the data to integers to avoid issues with sqlite3 database
    df = prepare_bars(df)

    db = Database()

    df.to_sql(
        "stock_bars",
        db.conn,
        if_exists="append",
        index=False
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