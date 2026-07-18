import sqlite3
import pandas as pd

DATABASE = "data/trading_data.db"

# Connect to database
connection = sqlite3.connect(DATABASE)

# Read table into dataframe
df = pd.read_sql(
    "SELECT * FROM stock_bars",
    connection
)

connection.close()

# Inspect data
print(df.head())
print()
print(df.info())