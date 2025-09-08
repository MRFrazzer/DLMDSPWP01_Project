# app_api.py  (tiny shim)
import pandas as pd
from pathlib import Path

# Import your exported notebook module
import Updated_Assignment_flow9 as app

# ---- Loaders as simple functions (call your existing classes) ----
def load_training_data(path: str | Path) -> pd.DataFrame:
    return app.TrainingLoader(Path(path)).load()

def load_ideals(path: str | Path) -> pd.DataFrame:
    return app.IdealLoader(Path(path)).load()

def load_test_data(path: str | Path) -> pd.DataFrame:
    return app.TestLoader(Path(path)).load()

# ---- Model selection → you already have select_best_ideals ----
select_best_ideals = app.select_best_ideals

# ---- Tolerances/mapping: re-export your existing functions ----
compute_tolerances = app.compute_tolerances

# Provide a small, test-friendly wrapper that returns a DataFrame
def map_points_to_tolerance(test_df: pd.DataFrame,
                            ideals_df: pd.DataFrame,
                            chosen_ideals: list[str],
                            tolerances: dict[str, float],
                            x_col: str = "X") -> pd.DataFrame:
    """
    Uses your internal helpers (_prepare_ideal_lookup, assign_test_row) to
    return a tidy dataframe: [X, Y, DeltaY, IdealFuncNo].
    """
    import numpy as np
    ideal_lookup = app._prepare_ideal_lookup(ideals_df, chosen_ideals, x_col=x_col)
    rows = []
    for _, r in test_df.iterrows():
        x = float(r[x_col]); y = float(r["Y"])
        try:
            k, _ = app.assign_test_row(
                x=x, y=y,
                ideal_lookup=ideal_lookup,
                chosen_ideals=chosen_ideals,
                tolerances=tolerances,
                x_col=x_col,
            )
            # signed residual
            idx = (ideal_lookup[x_col] - x).abs().idxmin()
            ideal_y = float(ideal_lookup.loc[idx, k])
            delta = y - ideal_y
            rows.append({x_col: x, "Y": y, "DeltaY": float(delta), "IdealFuncNo": k})
        except app.AssignmentRuleError:
            rows.append({x_col: x, "Y": y, "DeltaY": np.nan, "IdealFuncNo": np.nan})
    return pd.DataFrame(rows)
