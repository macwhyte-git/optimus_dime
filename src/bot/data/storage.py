"""Storage layer: everything that talks to the PostgreSQL database.

Built with SQLAlchemy Core on top of the psycopg driver. Other modules import
functions from here and never touch the database directly.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine, make_url

# --- Section 1: settings ----------------------------------------------------

# Name of the environment variable that holds the database URL. Kept as a
# constant so a different database (for example a test one) can be used by
# pointing this at another variable, with no other code changes.
DB_URL_ENV_VAR = "DATABASE_URL"

# Read the .env file once, when this module is first imported, and copy its
# lines into the process environment so os.environ can see them.
load_dotenv()


# --- Section 2: engine ------------------------------------------------------

def _build_url() -> URL:
    """Read the database URL from the environment and make it psycopg 3 ready.

    A plain 'postgresql://' URL makes SQLAlchemy look for the older psycopg2
    driver, so that scheme is swapped for 'postgresql+psycopg://'.
    os.environ[...] raises KeyError if the variable is missing, which is
    deliberate: fail loudly rather than connect to nothing.
    """
    url = make_url(os.environ[DB_URL_ENV_VAR])
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the shared engine, creating it on the first call only.

    lru_cache(maxsize=1) remembers the result, so every later call returns the
    same engine (and therefore the same connection pool). The engine does not
    connect until it is first used. pool_pre_ping=True tests a pooled
    connection before handing it out, so a dropped connection is replaced
    instead of causing an error.
    """
    return create_engine(_build_url(), pool_pre_ping=True)