"""Data loader: reads stored bars from the database into pandas DataFrames.

This is the READ side of the data layer. The collector and storage.py write
bars; everything that analyses them (backtester, strategies, paper broker)
reads them through here, so they all receive the same shape of data.

The loader reads no config files. The caller decides which exchanges, symbols,
timeframes and date range it wants and passes them in as arguments. Each of
the three can be a single value or a list.
"""

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