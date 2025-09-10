"""
app_api.py — tiny shim layer for tests

This module presents a small, stable surface that the test suite calls into,
while delegating the actual work to the `dlmdsp` package. I’m keeping the
original behavior and function names the tests expect, just wiring them up
to the package implementation.

Exposed functions:
- load_training_data(path)
- load_ideals(path)
- load_test_data(path)
- select_best_ideals(training_df, ideal_df, x_col="X")
- compute_tolerances(training, ideal, mapping, x_col="X", scale=sqrt(2))
- map_points_to_tolerance(test_df, ideals_df, chosen_ideals, tolerances, x_col="X")
"""

from __future__ import annotations            # allow forward annotations on older Python versions
import pandas as pd                           # DataFrame type and utilities
from pathlib import Path                      # cross-platform filesystem paths

# Pull the public API from the `dlmdsp` package.                         # (comment)
from dlmdsp import (                                                     # re-exported by dlmdsp/__init__.py
    TrainingCsvLoader,                                                   # loader for training.csv (X + Y1..Y4)
    IdealCsvLoader,                                                      # loader for ideal.csv (X + Y1..Y50)
    TestCsvLoader,                                                       # loader for test.csv (X + Y)
    choose_best_ideal_columns,                                           # pick best ideal Yj per training Yk (min RMSE)
    compute_tolerances as _compute_tolerances,                           # tolerance calculator (sqrt(2) * max abs residual)
    build_ideal_lookup,                                                  # compact lookup: X + chosen ideals
    assign_single_test_point,                                            # assign one test point within tolerance
    AssignmentRuleError,                                                 # raised if no ideal fits within tolerance
)


def load_training_data(path: str | Path) -> pd.DataFrame:
    """Read and validate the training CSV (expects X and exactly Y1..Y4)."""
    return TrainingCsvLoader(Path(path)).load()   # normalize path → loader → DataFrame


def load_ideals(path: str | Path) -> pd.DataFrame:
    """Read and validate the ideal CSV (expects X and exactly Y1..Y50)."""
    return IdealCsvLoader(Path(path)).load()      # normalize path → loader → DataFrame


def load_test_data(path: str | Path) -> pd.DataFrame:
    """Read and validate the test CSV (expects columns X and Y)."""
    return TestCsvLoader(Path(path)).load()       # normalize path → loader → DataFrame


# alias without changing behavior
# Keep the old exported name that the tests import.
# Our package function is called `choose_best_ideal_columns`, but tests expect
# `select_best_ideals`. This one-line alias preserves that public name.
select_best_ideals = choose_best_ideal_columns  # alias for test compatibility


def compute_tolerances(
    *,                         # make all parameters keyword-only for clarity
    training,                  # pandas.DataFrame: training set with columns X and Y1..Y4
    ideal,                     # pandas.DataFrame: ideal set with columns X and Y1..Y50
    mapping,                   # dict[str, str]: {"Y1": "Yk", ...} chosen ideal for each training Y
    x_col: str = "X",          # name of the shared X column (default "X")
    scale: float = 2**0.5,     # multiplier applied to the max residual (default sqrt(2))
):
    """
    Compatibility shim that forwards to the package's `compute_tolerances`.

    This wrapper exists because the tests call `compute_tolerances(training=..., ideal=..., mapping=...)`,
    while the package function expects the names `training_df`, `ideal_df`, and `best_map`.
    Nothing else changes—this simply renames the arguments and passes them along.

    Parameters
    ----------
    training : pandas.DataFrame
        Training data with columns ``X`` and ``Y1..Y4``.
    ideal : pandas.DataFrame
        Ideal data with columns ``X`` and ``Y1..Y50`` on the same X grid.
    mapping : dict[str, str]
        Mapping from each training column (e.g., "Y1") to the chosen ideal column (e.g., "Y17").
    x_col : str, optional
        Name of the shared X column; defaults to ``"X"``.
    scale : float, optional
        Tolerance multiplier; defaults to ``sqrt(2)``.

    Returns
    -------
    dict[str, float]
        Dictionary keyed by ideal number ("1".."4") with the tolerance value for each chosen ideal.
    """
    # Call the real implementation, renaming parameters to what it expects.
    return _compute_tolerances(
        training_df=training,   # forward the training DataFrame
        ideal_df=ideal,         # forward the ideal DataFrame
        best_map=mapping,       # forward the training→ideal mapping
        x_col=x_col,            # forward the X column name
        scale=scale,            # forward the multiplier
    )


def map_points_to_tolerance(
    test_df: pd.DataFrame,
    ideals_df: pd.DataFrame,
    chosen_ideals: list[str],
    tolerances: dict[str, float],
    x_col: str = "X",
) -> pd.DataFrame:
    """Return DataFrame with [X, Y, DeltaY, IdealFuncNo]; DeltaY is signed."""
    import numpy as np

    lookup = build_ideal_lookup(ideals_df, chosen_ideals, x_col=x_col)  # X + chosen ideals
    rows: list[dict] = []

    for _, r in test_df.iterrows():
        x = float(r[x_col])
        y = float(r["Y"])
        try:
            # Try to assign this test point to one of the four ideals.
            ideal_no, _ = assign_single_test_point(
                x_value=x,
                y_value=y,
                ideal_lookup_df=lookup,
                chosen_ideals=chosen_ideals,
                tolerances=tolerances,
                x_col=x_col,
            )

            # Map "1".."4" to the actual chosen ideal column name.
            col = chosen_ideals[int(ideal_no) - 1]

            # Nearest-X behavior (same as before).
            idx = (lookup[x_col] - x).abs().idxmin()
            ideal_y = float(lookup.loc[idx, col])

            # Signed residual.
            rows.append({x_col: x, "Y": y, "DeltaY": float(y - ideal_y), "IdealFuncNo": ideal_no})

        except AssignmentRuleError:
            # Unassigned rows carry NaNs for DeltaY and IdealFuncNo.
            rows.append({x_col: x, "Y": y, "DeltaY": np.nan, "IdealFuncNo": np.nan})

    return pd.DataFrame(rows)
