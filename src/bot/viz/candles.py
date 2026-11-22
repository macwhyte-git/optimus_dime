"""Candlestick charts for bars loaded with bot.data.loader.

The functions here BUILD a Plotly figure and return it. They never show or
save it; whoever calls them decides that. This keeps them easy to test and
lets the same chart be shown in a browser, saved to a file, or have more
traces added to it.

Charts are interactive: zoom, pan, and hover over a candle to read its values.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from bot.data.loader import LABEL_COLUMNS, VALUE_COLUMNS

# --- Section 1: settings ----------------------------------------------------

# Candle colours. Style choices live here, in one place, so changing the look
# of every chart means editing a line or two. They are also function arguments
# later, so a single chart can override them.
UP_COLOR = "#26a69a"      # a bar that closed higher than it opened (green)
DOWN_COLOR = "#ef5350"    # a bar that closed lower than it opened (red)

# How the figure's height is shared between the candle panel (top) and the
# volume panel (bottom). The two numbers add up to 1.
ROW_HEIGHTS = [0.75, 0.25]

# Overall chart height in pixels. Width is left to fill the browser window.
DEFAULT_HEIGHT = 700

# Plotly "template": the overall theme (background, grid, fonts).
# "plotly_white" is a plain light theme; "plotly_dark" is the dark one.
DEFAULT_TEMPLATE = "plotly_white"

# The columns a chart needs from the DataFrame. Imported from the loader
# instead of retyped, so if the loader's columns ever change, this follows.
REQUIRED_COLUMNS = list(VALUE_COLUMNS)   # open, high, low, close, volume

# Check the template name now. A typo here would otherwise only show up as an
# obscure error the first time a chart is drawn. pio.templates is Plotly's
# registry of available themes.
if DEFAULT_TEMPLATE not in pio.templates:
    raise ImportError(
        f"candles.py: unknown Plotly template '{DEFAULT_TEMPLATE}'. "
        f"Available: {', '.join(pio.templates)}"
    )

# --- Section 2: checking and preparing the data -----------------------------

# The most candles one chart will draw. Plotly slows down well beyond this,
# and a chart this dense is unreadable anyway. To plot more, chart a shorter
# window or a coarser timeframe. Callers can override it with an argument.
MAX_CANDLES = 20_000


def prepare_bars(df: pd.DataFrame, max_candles: int = MAX_CANDLES) -> pd.DataFrame:
    """Check that a DataFrame can be drawn as one candle chart, and clean it.

    Accepts the output of load_bars() (one market) or one piece from
    split_by_market(). Returns a NEW DataFrame with only the five value
    columns, sorted by time, with a timezone-free UTC index. The original is
    never changed.

    Raises a clear error, saying what to fix, if:
      - it is not a DataFrame, or it is empty
      - the index is not made of times
      - a needed column is missing
      - it holds more than one market (split it first)
      - there are duplicate timestamps
      - there are more than max_candles bars
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(df).__name__}")
    if df.empty:
        raise ValueError("No bars to plot: the DataFrame is empty")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(
            "The DataFrame's index must be times (a DatetimeIndex). "
            "load_bars() returns it that way; did the index get reset?"
        )

    missing = [name for name in REQUIRED_COLUMNS if name not in df.columns]
    if missing:
        raise ValueError(f"The DataFrame is missing columns: {', '.join(missing)}")

    # One market per chart. The label columns are only present on the output
    # of load_bars(); pieces from split_by_market() do not have them. Where
    # they are present, drop_duplicates() keeps one row per distinct market,
    # so more than one row left over means several markets are mixed together.
    labels = [name for name in LABEL_COLUMNS if name in df.columns]
    if labels:
        markets = df[labels].drop_duplicates()
        if len(markets) > 1:
            raise ValueError(
                f"The DataFrame holds {len(markets)} different markets, but one chart "
                f"shows one. Split it first with split_by_market()."
            )

    if len(df) > max_candles:
        raise ValueError(
            f"{len(df)} bars is more than the {max_candles} limit. "
            f"Plot a shorter window (the start and end arguments of load_bars) "
            f"or a coarser timeframe."
        )

    out = df[REQUIRED_COLUMNS].copy()   # a copy, so the caller's DataFrame is untouched
    out = out.sort_index()
    if out.index.has_duplicates:
        raise ValueError("Duplicate timestamps in the index: each bar must have a unique time")

    # Convert to plain UTC times with no zone attached. Plotly can be ambiguous
    # about timezone-aware timestamps, and plain UTC removes any doubt about
    # what time the chart is showing. An index with no zone is taken to be UTC.
    if out.index.tz is not None:
        out.index = out.index.tz_convert("UTC").tz_localize(None)
    return out


def describe_market(df: pd.DataFrame) -> str:
    """A short label for a chart title, such as 'kraken BTC/USD 5m'.

    Built from the exchange, symbol and timeframe columns of a DataFrame from
    load_bars(). Returns an empty string if the DataFrame has no label
    columns (a piece from split_by_market(), say) or is empty, so the caller
    can supply its own title.
    """
    if df.empty or not all(name in df.columns for name in LABEL_COLUMNS):
        return ""
    first = df[LABEL_COLUMNS].iloc[0]
    return " ".join(str(first[name]) for name in LABEL_COLUMNS)