# tests/conftest.py
"""
Shared pytest fixtures for tiny synthetic datasets.

I keep these very small and deterministic so tests run fast and stay readable.
Nothing here touches the package code; it only provides DataFrames for tests.
"""

import math                   # basic math utilities (for sqrt2)
import numpy as np            # numeric helpers to generate arrays
import pandas as pd           # DataFrame construction for fixtures
import pytest                 # pytest fixture decorator

# --- Make sure the project root (parent of tests/) is importable ----------------
# This lets test files `import app_api` and `import dlmdsp` without extra setup.
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # project root
if ROOT not in sys.path:                                               # avoid duplicates
    sys.path.insert(0, ROOT)                                           # prepend root to sys.path
# -----------------------------------------------------------------------------

@pytest.fixture
def tiny_training_df():
    """Return a tiny training set with X and Y1..Y4 on a short grid."""
    x = np.linspace(0, 3, 7)  # 7 evenly spaced points in [0, 3]
    return pd.DataFrame({
        "X": x,
        "Y1": 2*x + 1,        # linear
        "Y2": x**2,           # quadratic
        "Y3": np.sin(x),      # sinusoid
        "Y4": 0.5*x + 2,      # another linear
    })

@pytest.fixture
def tiny_ideals_df():
    """Return a tiny ideal set: X and four Y columns, close to training."""
    x = np.linspace(0, 3, 7)  # same X grid as training
    return pd.DataFrame({
        "X": x,
        "Y1": 2*x + 1,            # exact match for training Y1
        "Y2": x**2 + 0.05,        # small offset vs training Y2
        "Y3": np.sin(x) + 0.1,    # small offset vs training Y3
        "Y4": 0.5*x + 2.1,        # small offset vs training Y4
    })

@pytest.fixture
def tiny_test_df():
    """Return a tiny test set with a few in-tolerance points and some outliers."""
    rng = np.random.default_rng(123)                         # deterministic noise
    xs = np.array([0.25, 1.25, 2.75, 2.0, 0.7])             # test X values
    y1 = 2*xs + 1 + rng.normal(0, 0.03, size=len(xs))       # near Y1 (linear) with noise
    y2 = xs**2 + 0.05 + rng.normal(0, 0.03, size=len(xs))   # near Y2 (quadratic) with noise
    ys = np.array([y1[0], y2[1], 99.0, y1[3], -42.0])       # include two clear outliers
    return pd.DataFrame({"X": xs, "Y": ys})                 # test frame: X and Y only

@pytest.fixture
def sqrt2():
    """Return sqrt(2) as a convenience fixture for tests."""
    return math.sqrt(2.0)
