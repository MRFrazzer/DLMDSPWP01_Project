# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_database.py                                                             # module: DB helpers
# ──────────────────────────────────────────────────────────────────────────────
"""Small helpers for SQLite I/O with SQLAlchemy.

I use SQLite to park intermediate and final tables so I can query and visualize
results outside the runtime (training, ideal, test_mapping).
"""

from pathlib import Path                                                           # file path type
import pandas as pd                                                                # DataFrame operations
from sqlalchemy import create_engine                                               # engine factory
from sqlalchemy.engine import Engine                                               # engine type hint


def create_sqlite_engine(sqlite_path: Path) -> Engine:                            # build SQLite engine
    """Create a SQLAlchemy engine that points to a SQLite file."""
    return create_engine(f"sqlite:///{sqlite_path.as_posix()}", echo=False)       # create engine with quiet logging


def write_dataframe(df: pd.DataFrame, table_name: str, engine: Engine) -> None:   # write DataFrame to table
    """Write a DataFrame to a SQLite table, replacing any existing table."""
    df.to_sql(table_name, engine, if_exists="replace", index=False)               # replace existing table
