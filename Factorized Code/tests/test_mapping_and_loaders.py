# tests/test_mapping_and_loaders.py
"""
Two small integration checks:

1) Tolerances + mapping:
   - Build a best-ideal mapping from tiny fixtures.
   - Compute per-ideal tolerances.
   - Map test points and confirm accepted rows are within tolerance.

2) Loader minimum shapes:
   - Create minimal CSVs on disk.
   - Ensure loaders return DataFrames with the expected columns/shapes.
"""

import pandas as pd
import pytest
from app_api import (
    compute_tolerances,          # wrapper → dlmdsp.compute_tolerances
    map_points_to_tolerance,     # small helper that returns a tidy DF
    select_best_ideals,          # wrapper → dlmdsp.choose_best_ideal_columns
    load_training_data,          # wrapper → TrainingCsvLoader(...).load()
    load_ideals,                 # wrapper → IdealCsvLoader(...).load()
    load_test_data,              # wrapper → TestCsvLoader(...).load()
)


def test_compute_tolerances_and_mapping(tiny_training_df, tiny_ideals_df, tiny_test_df):
    """End-to-end small check: best ideals → tolerances → point mapping within tolerance."""
    mapping = select_best_ideals(tiny_training_df, tiny_ideals_df, x_col="X")  # {"Y1": "Yk", ...}
    chosen = [mapping[c] for c in ["Y1", "Y2", "Y3", "Y4"]]                    # preserve Y1..Y4 order

    tolerances = compute_tolerances(                                           # per-ideal tolerance dict
        training=tiny_training_df,
        ideal=tiny_ideals_df,
        mapping=mapping,
        x_col="X",
        scale=2**0.5,                                                          # sqrt(2)
    )
    assert set(tolerances.keys()) == {"1", "2", "3", "4"}                      # 4 ideals tracked

    # Y1 is exact in fixtures → training residual 0 → tolerance 0
    assert tolerances["1"] == pytest.approx(0.0, abs=1e-12)

    # Map test points; output columns must include the assignment info
    out = map_points_to_tolerance(
        test_df=tiny_test_df,
        ideals_df=tiny_ideals_df,
        chosen_ideals=chosen,
        tolerances=tolerances,
        x_col="X",
    )
    assert {"X", "Y", "DeltaY", "IdealFuncNo"}.issubset(out.columns)

    # For accepted rows, |DeltaY| must be within the chosen ideal's tolerance
    accepted = out.dropna(subset=["IdealFuncNo"])
    for _, r in accepted.iterrows():
        k = str(r["IdealFuncNo"])                           # "1".."4"
        assert abs(r["DeltaY"]) <= tolerances[k] + 1e-9     # small epsilon for float math


def test_loaders_min_shape(tmp_path):
    """Minimal CSVs on disk should load with the expected columns/shapes."""
    # File paths in the temp directory
    train = tmp_path / "training.csv"
    ideal = tmp_path / "ideal.csv"
    testf = tmp_path / "test.csv"

    # Training: X + exactly 4 Y columns
    pd.DataFrame({
        "X": [0, 1],
        "Y1": [1, 2],
        "Y2": [3, 4],
        "Y3": [5, 6],
        "Y4": [7, 8],
    }).to_csv(train, index=False)

    # Ideal: X + exactly 50 Y columns (Y1..Y50)
    data = {"X": [0, 1]}
    for i in range(1, 51):                                   # generate 50 ideal columns
        data[f"Y{i}"] = [i, i + 1]
    pd.DataFrame(data).to_csv(ideal, index=False)

    # Test: X + Y
    pd.DataFrame({"X": [0.5, 1.5], "Y": [10, 20]}).to_csv(testf, index=False)

    # Loaders should accept these and produce expected shapes/columns
    assert load_training_data(train).shape[0] > 0
    assert load_ideals(ideal).shape[1] == 51                 # X + 50 Y columns
    assert set(load_test_data(testf).columns) == {"X", "Y"}
