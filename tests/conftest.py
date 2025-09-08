# (tiny synthetic data)
# tests/conftest.py

import math
import numpy as np
import pandas as pd
import pytest

# --- ensure project root (parent of tests/) is importable ---
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ------------------------------------------------------------


@pytest.fixture
def tiny_training_df():
    x = np.linspace(0, 3, 7)
    return pd.DataFrame({"X": x, "Y1": 2*x+1, "Y2": x**2, "Y3": np.sin(x), "Y4": 0.5*x+2})

@pytest.fixture
def tiny_ideals_df():
    x = np.linspace(0, 3, 7)
    return pd.DataFrame({
        "X": x,
        "Y1": 2*x+1,            # exact for Y1
        "Y2": x**2 + 0.05,      # slight offset
        "Y3": np.sin(x) + 0.1,  # slight offset
        "Y4": 0.5*x + 2.1,      # slight offset
    })

@pytest.fixture
def tiny_test_df():
    rng = np.random.default_rng(123)
    xs = np.array([0.25, 1.25, 2.75, 2.0, 0.7])
    y1 = 2*xs + 1 + rng.normal(0, 0.03, size=len(xs))
    y2 = xs**2 + 0.05 + rng.normal(0, 0.03, size=len(xs))
    ys = np.array([y1[0], y2[1], 99.0, y1[3], -42.0])  # a couple outliers
    return pd.DataFrame({"X": xs, "Y": ys})

@pytest.fixture
def sqrt2():
    return math.sqrt(2.0)
