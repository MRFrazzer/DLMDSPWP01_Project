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
    ideal_lookup_df: pd.DataFrame,                                                 # lookup DF with X + four ideals
    chosen_ideals: List[str],                                                      # names of chosen ideals
    tolerances: Dict[str, float],                                                  # per-ideal tolerance dict
    x_col: str = "X",                                                             # X column name
) -> Tuple[str, float]:                                                            # returns (IdealFuncNo, ΔY)
    """Assign one test point to the first ideal whose deviation is within tolerance.

    I compute |y - ideal(x)| for each chosen ideal, sort by deviation, and return
    the first one that meets its tolerance. If none do, I raise AssignmentRuleError.
    """  # function docstring
    row = ideal_lookup_df.loc[ideal_lookup_df[x_col] == x_value]                   # try exact X match
    if row.empty:                                                                  # if no exact match
        nearest_index = (ideal_lookup_df[x_col] - x_value).abs().idxmin()          # find closest X index
        row = ideal_lookup_df.loc[[nearest_index]]                                 # take that single row
    row = row.squeeze()                                                            # convert to Series for access
    deviations: List[Tuple[str, float]] = []                                       # collect (ideal_no, deviation)
    for ideal_number, ideal_col in enumerate(chosen_ideals, start=1):              # iterate chosen ideals
        deviation = abs(y_value - float(row[ideal_col]))                           # compute |y - ideal(x)|
        deviations.append((str(ideal_number), deviation))                          # append pair
    deviations.sort(key=lambda pair: pair[1])                                      # smallest deviation first
    for ideal_number, deviation in deviations:                                     # scan sorted deviations
        if deviation <= tolerances[ideal_number]:                                  # check against tolerance
            return ideal_number, deviation                                         # accept and return result
    raise AssignmentRuleError(                                                     # none fit → raise error
        f"No valid assignment for x={x_value}, y={y_value}; deviations={deviations}, tolerances={tolerances}"  # message
    )                                                                              # end raise

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
