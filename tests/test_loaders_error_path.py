# tests/test_loaders_error_path.py
import pandas as pd
import pytest
from app_api import load_ideals
from Updated_Assignment_flow9 import DataShapeMismatchError  # your exception

def test_ideal_loader_rejects_wrong_column_count(tmp_path):
    bad = tmp_path / "bad_ideal.csv"
    # Only 2 Y cols -> should raise
    pd.DataFrame({"X":[0,1], "Y1":[1,2], "Y2":[2,3]}).to_csv(bad, index=False)
    with pytest.raises(DataShapeMismatchError):
        load_ideals(bad)
