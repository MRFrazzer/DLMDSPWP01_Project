#tests/test_mapping_and_loaders.py (two short checks)

import pandas as pd
import pytest
from app_api import (
    compute_tolerances,
    map_points_to_tolerance,
    select_best_ideals,
    load_training_data, load_ideals, load_test_data
)

def test_compute_tolerances_and_mapping(tiny_training_df, tiny_ideals_df, tiny_test_df):
    mapping = select_best_ideals(tiny_training_df, tiny_ideals_df, x_col="X")
    chosen = [mapping[c] for c in ["Y1","Y2","Y3","Y4"]]
    tolerances = compute_tolerances(
        training=tiny_training_df, ideal=tiny_ideals_df, mapping=mapping, x_col="X", scale=2**0.5
    )
    assert set(tolerances.keys()) == {"1","2","3","4"}
    # Y1 is exact → training deviation 0 → tolerance 0
    assert tolerances["1"] == pytest.approx(0.0, abs=1e-12)

    out = map_points_to_tolerance(
        test_df=tiny_test_df, ideals_df=tiny_ideals_df, chosen_ideals=chosen,
        tolerances=tolerances, x_col="X"
    )
    assert {"X","Y","DeltaY","IdealFuncNo"}.issubset(out.columns)
    accepted = out.dropna(subset=["IdealFuncNo"])
    for _, r in accepted.iterrows():
        k = str(r["IdealFuncNo"])
        assert abs(r["DeltaY"]) <= tolerances[k] + 1e-9

def test_loaders_min_shape(tmp_path):
    # Create minimal CSVs and assert your loaders return DataFrames
    train = tmp_path / "training.csv"
    ideal = tmp_path / "ideal.csv"
    testf = tmp_path / "test.csv"

    pd.DataFrame({"X":[0,1], "Y1":[1,2], "Y2":[3,4], "Y3":[5,6], "Y4":[7,8]}).to_csv(train, index=False)
    
    data = {"X":[0,1]}
    for i in range(1, 51):  # your loader requires exactly 50 Y columns
        data[f"Y{i}"] = [i, i+1]
    pd.DataFrame(data).to_csv(ideal, index=False)
    pd.DataFrame({"X":[0.5, 1.5], "Y":[10, 20]}).to_csv(testf, index=False)

    assert load_training_data(train).shape[0] > 0
    assert load_ideals(ideal).shape[1] == 51  # X + 50 Y columns
    assert set(load_test_data(testf).columns) == {"X","Y"}
