# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_mapping.py                                                               # module: assignment + persistence
# ──────────────────────────────────────────────────────────────────────────────
"""Assign test rows to the chosen ideals and store the results.

I keep a compact lookup (X + chosen ideals), pick the ideal with the smallest
deviation that is within tolerance, and append the results to `test_mapping`.
"""

from __future__ import annotations                                                # modern typing
from typing import Dict, List, Tuple                                               # explicit types
import pandas as pd                                                                # data handling
from sqlalchemy.engine import Engine                                               # engine type hint
from .dlmdsp_exceptions import AssignmentRuleError                                   # error when no assignment fits
import numpy as np  # used for fast, stable 1-D linear interpolation

def _interp_at_x(lookup_df: pd.DataFrame, x_col: str, y_col: str, x: float) -> float:
    """
    Return the ideal value y(x) by **linear interpolation** over the (X, ideal) grid.

    Behavior:
      • Sorts rows by X and drops duplicates/NaNs for a clean monotonic grid.
      • Uses numpy.interp for linear interpolation between the two bounding Xs.
      • If x is outside the grid, clamps to the nearest endpoint (np.interp default).
    
    Parameters
    ----------
    lookup_df : pd.DataFrame
        DataFrame that contains the X column and one ideal column (already filtered to chosen ideals).
    x_col : str
        Name of the X column (e.g., "X").
    y_col : str
        Name of the ideal column we want to interpolate (e.g., "Y42").
    x : float
        The test X value at which to evaluate/interpolate the ideal.

    Returns
    -------
    float
        Interpolated y value for the ideal at the given x.
    """
    # Keep only the two columns we need; drop any NaNs that would break interpolation
    s = lookup_df[[x_col, y_col]].dropna()

    # Sort by X to ensure a strictly increasing grid for interpolation
    s = s.sort_values(x_col)

    # If there are duplicate X values, keep the first occurrence to avoid ambiguity
    s = s[~s[x_col].duplicated(keep="first")]

    # Convert to NumPy arrays for np.interp
    xp = s[x_col].to_numpy(dtype=float)  # grid X values
    fp = s[y_col].to_numpy(dtype=float)  # corresponding ideal Y values

    if xp.size == 0:  # defensive check: empty grid would be a logic/data error
        raise ValueError(f"Empty interpolation grid for column {y_col!r}")

    # Linear interpolation; clamps to endpoints when x < min(xp) or x > max(xp)
    return float(np.interp(x, xp, fp))



def build_ideal_lookup(                                                           # keep only chosen ideals + X
    ideal_df: pd.DataFrame,                                                        # full ideal DataFrame
    chosen_ideals: List[str],                                                      # names of chosen ideal columns
    x_col: str = "X",                                                             # X column name
) -> pd.DataFrame:                                                                 # returns compact lookup DF
    """Return a small table with just X and the four chosen ideal columns."""
    columns_to_keep = [x_col] + chosen_ideals                                      # assemble columns
    return ideal_df[columns_to_keep].copy()                                        # return defensive copy


def assign_single_test_point(                                                     # assign one test point
    x_value: float,                                                                # test X value
    y_value: float,                                                                # test Y value
    ideal_lookup_df: pd.DataFrame,                                                 # lookup DF with X + chosen ideals
    chosen_ideals: List[str],                                                      # names of chosen ideal columns (order = 1..4)
    tolerances: Dict[str, float],                                                  # per-ideal tolerance dict: keys "1".."4"
    x_col: str = "X",                                                              # X column name
) -> Tuple[str, float]:                                                            # returns (IdealFuncNo, ΔY)
    """
    Assign one test point (x_value, y_value) to the **first** chosen ideal whose
    deviation is within its tolerance (ΔY <= tolerance). The ideal value at X is
    obtained by **linear interpolation** on the ideal grid.

    Steps:
      1) For each chosen ideal column, compute ideal_y(x) via linear interpolation.
      2) Compute deviation = |y_value - ideal_y|.
      3) Sort ideals by deviation (smallest first).
      4) Return the first (ideal_number, deviation) that satisfies its tolerance.
      5) If none satisfy, raise AssignmentRuleError (handled by caller).

    Returns
    -------
    (str, float)
        ideal_number (as "1".."4" matching the order of chosen_ideals), and ΔY.

    Raises
    ------
    AssignmentRuleError
        If no ideal satisfies the tolerance for this test point.
    """
    deviations: List[Tuple[str, float]] = []  # will hold pairs like ("1", 0.123)

    # Compute |y - ideal(x)| for each chosen ideal using interpolation
    for ideal_number, ideal_col in enumerate(chosen_ideals, start=1):
        # Interpolate the ideal at the test X value
        ideal_y = _interp_at_x(
            lookup_df=ideal_lookup_df,  # the compact table with X + chosen ideals
            x_col=x_col,                # name of the X column
            y_col=ideal_col,            # current ideal column (e.g., "Y42")
            x=x_value                   # test X value to evaluate at
        )

        # Absolute residual between test Y and the interpolated ideal value
        deviation = abs(y_value - ideal_y)

        # Store as ("1".."4", deviation) so it lines up with the tolerance dict keys
        deviations.append((str(ideal_number), float(deviation)))

    # Check the closest fits first
    deviations.sort(key=lambda pair: pair[1])  # smallest deviation first

    # Accept the first ideal whose deviation is within its tolerance band
    for ideal_number, deviation in deviations:
        if deviation <= float(tolerances[ideal_number]):  # spec: ΔY ≤ √2 × max|train residual|
            return ideal_number, deviation

    # If we get here, none of the four ideals passed the tolerance rule
    raise AssignmentRuleError(
        f"No valid assignment for x={x_value}, y={y_value}; "
        f"deviations={deviations}, tolerances={tolerances}"
    )


def stream_and_store_test_results(                                                # process all test rows
    test_df: pd.DataFrame,                                                         # test DataFrame
    ideal_lookup_df: pd.DataFrame,                                                 # compact ideal lookup
    chosen_ideals: List[str],                                                      # chosen ideal names
    tolerances: Dict[str, float],                                                  # tolerance dict
    engine: Engine,                                                                # database engine
    x_col: str = "X",                                                              # X column name
) -> None:                                                                         # writes to DB, returns None
    """Assign every test row and append the results to the `test_mapping` table.

    Accepted rows → DB table `test_mapping`.
    Rejected rows → CSV file `test_rejections.csv` with a human-readable reason.
    """
    output_rows: List[Dict[str, float | int]] = []                                 # buffer for accepted rows
    rejected_rows: List[Dict[str, float | str]] = []                               # buffer for rejected rows

    for _, test_row in test_df.iterrows():                                         # iterate test rows
        x_val = float(test_row[x_col])                                             # numeric X
        y_val = float(test_row["Y"])                                               # numeric Y
        try:
            ideal_number, deviation = assign_single_test_point(                    # attempt assignment
                x_value=x_val,
                y_value=y_val,
                ideal_lookup_df=ideal_lookup_df,
                chosen_ideals=chosen_ideals,
                tolerances=tolerances,
                x_col=x_col,
            )
            output_rows.append({                                                   # accepted → collect for DB
                "X": x_val,
                "Y": y_val,
                "DeltaY": float(deviation),
                "IdealFuncNo": int(ideal_number),
            })
        except AssignmentRuleError as e:                                           # unassigned → log + keep going
            print(f"[WARN] {e}")
            rejected_rows.append({
                "X": x_val,
                "Y": y_val,
                "reason": str(e),                                                  # keep full message for traceability
            })
            continue

    # Write accepted rows to DB (same as before)
    if output_rows:
        pd.DataFrame(output_rows).to_sql(
            "test_mapping", engine, if_exists="append", index=False
        )
        print(f"[INFO] wrote {len(output_rows)} accepted rows to table 'test_mapping'")

    # Write rejected rows to a CSV for inspection
    if rejected_rows:
        rej_path = "test_rejections.csv"                                           # saved in project working dir
        pd.DataFrame(rejected_rows).to_csv(rej_path, index=False)
        print(f"[INFO] saved {len(rejected_rows)} rejected rows to {rej_path}")
