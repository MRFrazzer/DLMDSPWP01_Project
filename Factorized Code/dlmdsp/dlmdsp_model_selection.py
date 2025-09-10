# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_model_selection.py                                                       # module: model selection
# ──────────────────────────────────────────────────────────────────────────────
"""Pick the closest ideal for each training series and compute tolerances.

- choose_best_ideal_columns: For each Yk in training, I pick the ideal Yj with
  the smallest RMSE over the shared X grid.
- compute_tolerances: I set a per-ideal tolerance as sqrt(2) times the maximum
  absolute residual on the training grid.
"""

from __future__ import annotations                                                # modern typing
from typing import Dict, Optional                                                  # explicit types
import pandas as pd                                                                # data handling
from .dlmdsp_exceptions import DLMDSPError                                          # custom safety error


def _root_mean_square_error(a: pd.Series, b: pd.Series) -> float:                 # compute RMSE between two series
    """Return RMSE between two aligned series."""
    differences = a.values - b.values                                             # vector of differences
    return float((differences ** 2).mean() ** 0.5)                                 # sqrt(mean(square))


def choose_best_ideal_columns(                                                    # select best ideal per training Y
    training_df: pd.DataFrame,                                                     # training data with X,Y1..Y4
    ideal_df: pd.DataFrame,                                                        # ideal data with X,Y1..Y50
    x_col: str = "X",                                                             # name of X column
) -> Dict[str, str]:                                                               # returns mapping training→ideal
    """Map each training column (Y1..Y4) to the ideal column with the lowest RMSE.

    I join on X, compare each training Yk with each ideal Yj, and keep the j that
    minimizes RMSE for that k.
    """  # function docstring
    merged = pd.merge(training_df, ideal_df, on=x_col, how="inner", suffixes=("", "_ideal"))  # align on X
    training_targets = [c for c in training_df.columns if c != x_col]              # list of training Ys
    ideal_targets = [c for c in ideal_df.columns if c != x_col]                    # list of ideal Ys
    best_map: Dict[str, str] = {}                                                  # result mapping
    for training_col in training_targets:                                          # loop over each training Y
        best_ideal_name: Optional[str] = None                                      # track best ideal name
        best_rmse = float("inf")                                                  # start with infinity
        for ideal_col in ideal_targets:                                            # evaluate each ideal column
            merged_name = f"{ideal_col}_ideal" if ideal_col in training_targets else ideal_col  # resolve col name
            rmse_value = _root_mean_square_error(merged[training_col], merged[merged_name])      # compute RMSE
            if rmse_value < best_rmse:                                             # keep the smallest RMSE
                best_rmse = rmse_value                                             # update best RMSE
                best_ideal_name = ideal_col                                        # update best ideal name
        if best_ideal_name is None:                                                # guard against no selection
            raise DLMDSPError(f"Could not select an ideal for {training_col}.")   # raise clear error
        best_map[training_col] = best_ideal_name                                   # store best ideal for this Y
    return best_map                                                                # return mapping


def compute_tolerances(                                                           # compute tolerances per ideal
    training_df: pd.DataFrame,                                                     # training data
    ideal_df: pd.DataFrame,                                                        # ideal data
    best_map: Dict[str, str],                                                      # mapping training→ideal
    x_col: str = "X",                                                             # X column name
    scale: float = 2 ** 0.5,                                                       # sqrt(2) multiplier
) -> Dict[str, float]:                                                             # returns dict '1'..'4'→tolerance
    """Compute tolerance per ideal as: scale * max_abs(training - ideal).

    I merge on X, compute the max absolute residual for each chosen pair, and
    multiply by sqrt(2) (or the provided scale). The result is keyed by "1".."4"
    to match the assignment numbering.
    """  # function docstring
    merged = pd.merge(training_df, ideal_df, on=x_col, how="inner", suffixes=("", "_ideal"))  # align on X
    training_targets = [c for c in training_df.columns if c != x_col]              # list training Ys
    tolerances: Dict[str, float] = {}                                              # output dictionary
    for ideal_number, (training_col, ideal_col) in enumerate(best_map.items(), start=1):  # keep numbering
        merged_name = f"{ideal_col}_ideal" if ideal_col in training_targets else ideal_col  # resolve col name
        max_abs_residual = (merged[training_col] - merged[merged_name]).abs().max()        # max |residual|
        tolerances[str(ideal_number)] = float(scale * max_abs_residual)            # tolerance = sqrt(2)*max
    return tolerances                                                              # return tolerances
