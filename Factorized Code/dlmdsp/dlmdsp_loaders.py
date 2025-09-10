# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_loaders.py                                                              # module: CSV loaders
# ──────────────────────────────────────────────────────────────────────────────
"""CSV loaders with simple, explicit checks.

Each loader reads a CSV into a DataFrame and verifies the columns we rely on.
- Training: X and exactly Y1..Y4
- Ideal:    X and exactly Y1..Y50
- Test:     X and Y
"""

from __future__ import annotations                                                # allow modern typing in older Python
from dataclasses import dataclass                                                 # lightweight containers with type hints
from pathlib import Path                                                          # OS-agnostic file paths
from typing import Union                                                           # for PathLike alias
import pandas as pd                                                               # main table library
from .dlmdsp_exceptions import DataShapeMismatchError                               # custom error for validation

PathLike = Union[str, Path]                                                       # alias: string or Path


@dataclass                                                                         # decorate simple data holder
class BaseCsvLoader:                                                               # common loader ensuring X column
    """Load a CSV file and make sure the X column is there.

    Parameters
    ----------
    path : pathlib.Path
        Location of the CSV file.
    x_col : str, default "X"
        Name of the X column to require.
    """  # class docstring

    path: Path                                                                     # path to the CSV file
    x_col: str = "X"                                                              # expected name of X column

    def load(self) -> pd.DataFrame:                                               # read and validate CSV
        """Read the CSV and confirm the X column exists.

        Returns
        -------
        pandas.DataFrame
            The loaded table, if validation passes.

        Raises
        ------
        DataShapeMismatchError
            If the X column is missing.
        """  # function docstring
        df = pd.read_csv(self.path)                                                # load CSV into DataFrame
        if self.x_col not in df.columns:                                           # ensure required X exists
            raise DataShapeMismatchError(                                          # raise clear error if missing
                f"Missing '{self.x_col}' in {self.path}. Found columns: {list(df.columns)}"  # message with columns
            )                                                                      # end raise
        return df                                                                  # return validated DataFrame


class TrainingCsvLoader(BaseCsvLoader):                                            # loader for training set
    """Load the training set and enforce X + four Y columns (Y1..Y4)."""          # class docstring

    def load(self) -> pd.DataFrame:                                               # override load to add Y-count check
        """Return the training DataFrame and check the Y-column count.

        Raises
        ------
        DataShapeMismatchError
            If there aren’t exactly four Y columns.
        """  # function docstring
        df = super().load()                                                        # do base load + X check
        y_columns = [c for c in df.columns if c != self.x_col]                     # collect all non-X columns
        if len(y_columns) != 4:                                                    # must be exactly Y1..Y4
            raise DataShapeMismatchError(                                          # raise precise count error
                f"Training must have exactly 4 Y columns; got {len(y_columns)} -> {y_columns}"  # message
            )                                                                      # end raise
        return df                                                                  # return validated training DF


class IdealCsvLoader(BaseCsvLoader):                                               # loader for ideal set
    """Load the ideal set and enforce X + fifty Y columns (Y1..Y50)."""           # class docstring

    def load(self) -> pd.DataFrame:                                               # override for 50-column check
        """Return the ideal DataFrame and check the Y-column count.

        Raises
        ------
        DataShapeMismatchError
            If there aren’t exactly fifty Y columns.
        """  # function docstring
        df = super().load()                                                        # base load + X check
        y_columns = [c for c in df.columns if c != self.x_col]                     # list of ideal columns
        if len(y_columns) != 50:                                                   # enforce exactly 50
            preview = y_columns[:10]                                               # small preview for debugging
            raise DataShapeMismatchError(                                          # raise with helpful details
                f"Ideal must have exactly 50 Y columns; got {len(y_columns)}. First 10: {preview}"  # message
            )                                                                      # end raise
        return df                                                                  # return validated ideal DF


class TestCsvLoader(BaseCsvLoader):                                                # loader for test set
    """Load the test set and check for X and Y columns."""                        # class docstring

    def load(self) -> pd.DataFrame:                                               # override to ensure Y present
        """Return the test DataFrame and check that the Y column exists.

        Raises
        ------
        DataShapeMismatchError
            If the Y column is missing.
        """  # function docstring
        df = super().load()                                                        # base load + X check
        if "Y" not in df.columns:                                                 # ensure Y exists
            raise DataShapeMismatchError("Test data must contain a 'Y' column.")  # raise clear error
        return df                                                                  # return validated test DF


def load_training_csv(path: PathLike) -> pd.DataFrame:                            # helper: path→training DF
    """Convenience wrapper to load a training CSV from a path."""
    return TrainingCsvLoader(Path(path)).load()                                    # normalize path then load


def load_ideal_csv(path: PathLike) -> pd.DataFrame:                               # helper: path→ideal DF
    """Convenience wrapper to load an ideal CSV from a path."""
    return IdealCsvLoader(Path(path)).load()                                       # normalize path then load


def load_test_csv(path: PathLike) -> pd.DataFrame:                                # helper: path→test DF
    """Convenience wrapper to load a test CSV from a path."""
    return TestCsvLoader(Path(path)).load()                                        # normalize path then load
