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

# --- Section 3: the candlestick chart ---------------------------------------

def candle_figure(
    df: pd.DataFrame,
    title: str | None = None,
    show_volume: bool = True,
    height: int = DEFAULT_HEIGHT,
    template: str = DEFAULT_TEMPLATE,
    up_color: str = UP_COLOR,
    down_color: str = DOWN_COLOR,
    max_candles: int = MAX_CANDLES,
) -> go.Figure:
    """Build an interactive candlestick chart, with a volume panel underneath.

    'df' is the output of load_bars() for ONE market (or one piece from
    split_by_market()). The figure is RETURNED, not shown or saved, so the
    caller decides what to do with it, and more traces can be added to it.

    title        chart title. If None, one is built from the data: the market
                 (for example 'kraken BTC/USD 5m') and the time range in UTC.
    show_volume  False gives a candles-only chart using the full height.
    height       chart height in pixels (the width fills the window).
    template     a Plotly theme name, for example 'plotly_white' or 'plotly_dark'.
    up_color / down_color   candle colours for bars that closed higher / lower.
    max_candles  refuse to draw more bars than this (see prepare_bars).
    """
    # Validate the arguments first, so a mistake fails with a clear message
    # instead of an obscure Plotly error.
    if template not in pio.templates:
        raise ValueError(f"Unknown template '{template}'. Available: {', '.join(pio.templates)}")
    if not isinstance(height, (int, float)) or height <= 0:
        raise ValueError(f"height must be a positive number of pixels, got {height!r}")

    # Check and clean the data. This raises a clear error if it cannot be drawn.
    data = prepare_bars(df, max_candles=max_candles)

    # The default title: the market, then the period covered (times are UTC).
    if title is None:
        label = describe_market(df) or "Candlestick chart"
        start, end = data.index[0], data.index[-1]
        title = f"{label} | {start:%Y-%m-%d %H:%M} to {end:%Y-%m-%d %H:%M} UTC"

    # One column of panels. shared_xaxes=True links the time axes, so zooming
    # or panning one panel moves the other with it. row_heights splits the
    # height between candles and volume; with no volume panel there is one row.
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.03, row_heights=ROW_HEIGHTS,
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # Row 1: the candles. Each candle has a body (open to close) and wicks
    # (low to high). Hovering shows all four prices.
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["open"], high=data["high"], low=data["low"], close=data["close"],
            increasing_line_color=up_color, increasing_fillcolor=up_color,
            decreasing_line_color=down_color, decreasing_fillcolor=down_color,
            name="Price",
        ),
        row=1, col=1,
    )

    # Row 2: volume, one bar per candle, coloured to match its candle. A bar
    # that closed at or above its open counts as 'up' here. (In the candle
    # panel Plotly applies its own rule, so a rare bar where close equals open
    # might differ in colour between the two panels.)
    if show_volume:
        bar_colors = [
            up_color if close >= open_ else down_color
            for open_, close in zip(data["open"], data["close"])
        ]
        fig.add_trace(
            go.Bar(x=data.index, y=data["volume"], marker_color=bar_colors, name="Volume"),
            row=2, col=1,
        )

    # Layout. The range slider (a small overview strip under the chart) is off:
    # it takes space from the volume panel, and dragging to zoom is enough.
    # The legend is hidden because the panels are labelled by their axes.
    fig.update_layout(
        title=title,
        template=template,
        height=height,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",    # one hover box listing every panel at that time
        margin=dict(l=60, r=30, t=70, b=50),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    # The time axis sits on the bottom panel. The times are UTC (see prepare_bars).
    fig.update_xaxes(title_text="Time (UTC)", row=2 if show_volume else 1, col=1)

    return fig

# --- Section 4: overlays (lines and markers) --------------------------------

# Colours for overlay lines, used in turn when the caller does not pick one.
OVERLAY_COLORS = ["#1f77b4", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2"]

# How a buy and a sell look. A little darker than the candle colours so they
# stand out when drawn on top of the candles.
BUY_STYLE = {"name": "Buy", "symbol": "triangle-up", "color": "#1b5e20"}
SELL_STYLE = {"name": "Sell", "symbol": "triangle-down", "color": "#b71c1c"}

# The Plotly marker shapes and line styles these functions accept. Checking
# against a list gives a clear error for a typo, instead of Plotly silently
# drawing a default shape.
MARKER_SYMBOLS = {
    "circle", "square", "diamond", "cross", "x", "star",
    "triangle-up", "triangle-down", "triangle-left", "triangle-right",
}
LINE_DASHES = {"solid", "dot", "dash", "longdash", "dashdot"}


def _check_figure(fig: go.Figure) -> None:
    """Make sure 'fig' came from candle_figure(), whose first trace is the candles."""
    if not isinstance(fig, go.Figure) or len(fig.data) == 0 or fig.data[0].type != "candlestick":
        raise ValueError("Expected a figure made by candle_figure(): its first trace must be the candlesticks")


def _plain_utc(index: pd.Index) -> pd.DatetimeIndex:
    """Return a time index as plain UTC with no zone attached, matching the
    candles. A time index with no zone is taken to be UTC. Raises if the index
    is not made of times."""
    if not isinstance(index, pd.DatetimeIndex):
        raise ValueError("The index must be times (a DatetimeIndex), such as the one load_bars() returns")
    return index.tz_convert("UTC").tz_localize(None) if index.tz is not None else index


def _enable_legend(fig: go.Figure) -> None:
    """Show a legend, top right, for the overlays. The candle and volume traces
    are left out of it, since the panels are already labelled."""
    for trace in fig.data:
        if trace.type in ("candlestick", "bar"):
            trace.showlegend = False
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )


def add_line(
    fig: go.Figure,
    series: pd.Series,
    name: str,
    color: str | None = None,
    width: float = 1.5,
    dash: str = "solid",
) -> go.Figure:
    """Draw a line on the candle panel, for example a moving average.

    'series' is a pandas Series indexed by time, such as
    df["close"].rolling(12).mean(). Missing values (a moving average has none
    for its first bars) are skipped. 'name' labels it in the legend and in the
    hover box. If 'color' is None, the next colour in OVERLAY_COLORS is used.

    Changes 'fig' in place and also returns it.
    """
    _check_figure(fig)
    if not isinstance(series, pd.Series):
        raise TypeError(f"Expected a pandas Series, got {type(series).__name__}")
    if dash not in LINE_DASHES:
        raise ValueError(f"Unknown dash '{dash}'. Use one of: {', '.join(sorted(LINE_DASHES))}")

    clean = series.dropna().sort_index()
    if clean.empty:
        raise ValueError(f"'{name}' has no values to draw (all of them are missing)")
    x = _plain_utc(clean.index)
    if x.has_duplicates:
        raise ValueError(f"'{name}' has duplicate timestamps; a line needs one value per time")

    # Pick a colour from the palette, one per line already on the chart.
    if color is None:
        existing = sum(1 for t in fig.data if t.type == "scatter" and t.mode == "lines")
        color = OVERLAY_COLORS[existing % len(OVERLAY_COLORS)]

    fig.add_trace(
        go.Scatter(x=x, y=clean.to_numpy(), mode="lines", name=name,
                   line=dict(color=color, width=width, dash=dash)),
        row=1, col=1,   # the candle panel
    )
    _enable_legend(fig)
    return fig


def add_markers(
    fig: go.Figure,
    points: pd.Series,
    name: str,
    symbol: str = "circle",
    color: str = "#1f77b4",
    size: int = 11,
    hover_text: list[str] | None = None,
) -> go.Figure:
    """Mark moments on the candle panel, for example where a strategy bought.

    'points' is a Series of PRICES indexed by the TIMES of the events. The
    price says how high on the chart the marker sits. For example, the closing
    price at each moment a condition is true:

        buys = df["close"][fast_ma > slow_ma]

    'hover_text' is an optional list, one text per point, shown on hover. Points
    with a missing price are skipped, along with their text. Several markers at
    the same time are allowed.

    Raises an error if every marker lies outside the time range of the candles,
    which nearly always means a timezone mistake or the wrong market.

    Changes 'fig' in place and also returns it.
    """
    _check_figure(fig)
    if not isinstance(points, pd.Series):
        raise TypeError(f"Expected a pandas Series, got {type(points).__name__}")
    if symbol not in MARKER_SYMBOLS:
        raise ValueError(f"Unknown marker symbol '{symbol}'. Use one of: {', '.join(sorted(MARKER_SYMBOLS))}")
    if hover_text is not None and len(hover_text) != len(points):
        raise ValueError(f"hover_text has {len(hover_text)} entries but there are {len(points)} points")

    # Keep the points that have a price. A positional mask (not a label lookup)
    # keeps the hover texts aligned even when two events share a timestamp.
    keep = points.notna().to_numpy()
    if not keep.any():
        raise ValueError(f"'{name}' has no points to draw (all of them are missing)")
    x = _plain_utc(points.index[keep])
    y = points.to_numpy()[keep]
    texts = [t for t, k in zip(hover_text, keep) if k] if hover_text is not None else None

    # A guard against a common mistake: markers that fall entirely outside the
    # period the chart covers. The candles are always the first trace.
    candle_times = pd.DatetimeIndex(fig.data[0].x)
    if x.max() < candle_times.min() or x.min() > candle_times.max():
        raise ValueError(
            f"All '{name}' markers fall outside the chart "
            f"({candle_times.min()} to {candle_times.max()} UTC). "
            f"Check the timezone and that the data is for the same market."
        )

    marker_trace = go.Scatter(
        x=x, y=y, mode="markers", name=name,
        marker=dict(symbol=symbol, color=color, size=size, line=dict(width=1, color="white")),
    )
    if texts is not None:
        marker_trace.hovertext = texts
        marker_trace.hoverinfo = "text"
    fig.add_trace(marker_trace, row=1, col=1)
    _enable_legend(fig)
    return fig


def add_buy_sell(fig: go.Figure, buys: pd.Series | None = None, sells: pd.Series | None = None) -> go.Figure:
    """Mark buys (green up-triangles) and sells (red down-triangles).

    'buys' and 'sells' are Series of prices indexed by the time of each event;
    give either or both. A convenience wrapper around add_markers().
    """
    if buys is None and sells is None:
        raise ValueError("Give at least one of buys or sells")
    if buys is not None:
        add_markers(fig, buys, **BUY_STYLE)
    if sells is not None:
        add_markers(fig, sells, **SELL_STYLE)
    return fig