# tests/test_loaders_error_path.py
"""
Loader error-path test: the ideal CSV must have exactly 50 Y columns.
This test writes a deliberately invalid ideal CSV (only two Y columns)
and asserts that the package raises `DataShapeMismatchError`.
"""

import pandas as pd                # build a tiny CSV on disk
import pytest                      # assertion helpers and tmp_path fixture
from app_api import load_ideals    # shim that forwards into the dlmdsp package
from dlmdsp import DataShapeMismatchError  # package validation error to expect


def test_ideal_loader_rejects_wrong_column_count(tmp_path):
    """Writing an ideal.csv with the wrong number of Y columns should fail."""
    bad = tmp_path / "bad_ideal.csv"                                # temp file path
    # Only 2 Y columns -> violates the spec (expected X + Y1..Y50)
    pd.DataFrame({"X": [0, 1], "Y1": [1, 2], "Y2": [2, 3]}).to_csv(
        bad, index=False
    )

    # The loader should raise the package's DataShapeMismatchError.
    with pytest.raises(DataShapeMismatchError):
        load_ideals(bad)
