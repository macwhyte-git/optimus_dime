"""Draw an interactive candle chart of stored bars and open it in the browser.

What to draw (market, timeframe, how far back, moving averages, the look of the
chart) comes from config/viz.yaml. Which PERIOD to draw can be set per run.

Usage (from the project root, venv active):
    python scripts/plot_candles.py                             last N hours (see config)
    python scripts/plot_candles.py --start 2026-11-20 --end 2026-11-21
    python scripts/plot_candles.py --end "2026-11-21 12:00"    N hours up to that moment
    python scripts/plot_candles.py --config config/other.yaml  use a different settings file
    python scripts/plot_candles.py --no-open                   save the chart but do not open it

Dates and times without a time zone are taken to be UTC. --end is exclusive.
"""

import argparse

import pandas as pd

from bot.config import load_config, require_keys
from bot.data.loader import find_gaps, load_bars
from bot.viz.candles import add_line, candle_figure, describe_market, save_and_open

# --- Settings ---------------------------------------------------------------

DEFAULT_CONFIG = "viz"

REQUIRED_SETTINGS = [
    "exchange", "symbol", "timeframe", "lookback_hours", "moving_averages",
    "show_volume", "height", "template", "include_plotlyjs",
]


def load_settings(config=DEFAULT_CONFIG) -> dict:
    """Read the chart settings and check them, so a mistake fails here with a
    clear message and not halfway through drawing."""
    settings = load_config(config)
    require_keys(settings, REQUIRED_SETTINGS, source=str(config))

    # bool is a kind of int in Python, so exclude it explicitly: 'true' is not
    # a sensible number of hours.
    hours = settings["lookback_hours"]
    if isinstance(hours, bool) or not isinstance(hours, (int, float)) or hours <= 0:
        raise ValueError(f"lookback_hours must be a positive number, got {hours!r}")

    averages = settings["moving_averages"]
    if not isinstance(averages, list) or any(
        isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in averages
    ):
        raise ValueError(f"moving_averages must be a list of whole numbers of 1 or more, got {averages!r}")

    if not isinstance(settings["show_volume"], bool):
        raise ValueError(f"show_volume must be true or false, got {settings['show_volume']!r}")
    return settings


# --- Command line -----------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw an interactive candle chart")
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="settings file: a name (viz) or a path to a .yaml file (default: %(default)s)")
    parser.add_argument("--start", help="first bar to include, for example 2026-11-20 (UTC)")
    parser.add_argument("--end", help="stop BEFORE this moment, for example 2026-11-21 12:00 (UTC)")
    parser.add_argument("--no-open", action="store_true", help="save the chart without opening a browser")
    return parser.parse_args(argv)


def to_utc(value: str) -> pd.Timestamp:
    """Read a date or time typed on the command line as a UTC timestamp. Text
    with no time zone is taken to be UTC; text with one is converted."""
    try:
        ts = pd.Timestamp(value)
    except (ValueError, TypeError) as e:
        raise SystemExit(f"'{value}' is not a date I can read. Try 2026-11-20 or '2026-11-20 08:30'.") from e
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


# --- The script -------------------------------------------------------------

def main(argv=None) -> None:
    args = parse_args(argv)
    settings = load_settings(args.config)

    # Work out the period. An explicit --start wins. Otherwise count back
    # 'lookback_hours' from --end, or from now if there is no --end.
    end = to_utc(args.end) if args.end else None
    if args.start:
        start = to_utc(args.start)
    else:
        anchor = end if end is not None else pd.Timestamp.now(tz="UTC")
        start = anchor - pd.Timedelta(hours=settings["lookback_hours"])

    df = load_bars(settings["exchange"], settings["symbol"], settings["timeframe"], start=start, end=end)
    if df.empty:
        raise SystemExit(
            f"No bars found for {settings['exchange']} {settings['symbol']} {settings['timeframe']} "
            f"from {start:%Y-%m-%d %H:%M} UTC. Is the collector running, and does the data cover that period?"
        )

    fig = candle_figure(
        df,
        show_volume=settings["show_volume"],
        height=settings["height"],
        template=settings["template"],
    )

    # One line per moving average. A window longer than the data has no values
    # to draw, so say so and move on, instead of failing.
    for n in settings["moving_averages"]:
        average = df["close"].rolling(n).mean()
        if average.dropna().empty:
            print(f"skipped MA {n}: only {len(df)} bars, so it has no values yet")
            continue
        add_line(fig, average, f"MA {n}")

    # Tell the user if the data has holes, because an average across a hole is
    # quietly wrong.
    gaps = find_gaps(df)
    if gaps.empty:
        print(f"{len(df)} bars, no gaps")
    else:
        print(f"WARNING: {len(gaps)} gap(s), {int(gaps['missing_bars'].sum())} bars missing in this period:")
        print(gaps[["last_bar_before", "first_bar_after", "missing_bars"]].head(5).to_string(index=False))

    path = save_and_open(
        fig, describe_market(df),
        open_browser=not args.no_open,
        include_plotlyjs=settings["include_plotlyjs"],
    )
    print(f"saved: {path}")


if __name__ == "__main__":
    main()