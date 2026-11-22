"""Candlestick charts for bars loaded with bot.data.loader.

The functions here BUILD a Plotly figure and return it. They never show or
save it; whoever calls them decides that. This keeps them easy to test and
lets the same chart be shown in a browser, saved to a file, or have more
traces added to it.

Charts are interactive: zoom, pan, and hover over a candle to read its values.
"""

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