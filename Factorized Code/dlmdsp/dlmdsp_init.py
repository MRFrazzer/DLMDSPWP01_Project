# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp__init__.py                                                             # module: package initializer
# ──────────────────────────────────────────────────────────────────────────────
"""Central place for the package’s public API.

I re-export the most commonly used functions and classes so user code can write:
    from dlmdsp import load_training_csv, choose_best_ideal_columns
without importing from individual files. This file is about ergonomics: it keeps
imports short and makes the package feel cohesive.
"""

from .dlmdsp_exceptions import DLMDSPError, DataShapeMismatchError, AssignmentRuleError  # re-export custom exceptions for easy import
from .dlmdsp_loaders import (                                                           # re-export loaders and helpers
    BaseCsvLoader,                                                                     # base CSV loader class
    TrainingCsvLoader,                                                                 # training CSV loader
    IdealCsvLoader,                                                                    # ideal CSV loader
    TestCsvLoader,                                                                     # test CSV loader
    load_training_csv,                                                                 # function wrapper: load training CSV
    load_ideal_csv,                                                                    # function wrapper: load ideal CSV
    load_test_csv,                                                                     # function wrapper: load test CSV
)                                                                                      # end tuple
from .dlmdsp_database import create_sqlite_engine, write_dataframe                       # DB helpers: engine creator and DataFrame writer
from .dlmdsp_model_selection import choose_best_ideal_columns, compute_tolerances        # modeling helpers: ideal selection + tolerances
from .dlmdsp_mapping import (                                                            # mapping helpers: assignment and persistence
    build_ideal_lookup,                                                                 # build compact ideal lookup table
    assign_single_test_point,                                                           # assign one test point
    stream_and_store_test_results,                                                      # stream all test points and store to DB
)                                                                                      # end tuple
from .dlmdsp_plots import quick_plot_training_vs_ideals                                  # optional matplotlib quick plot
from .dlmdsp_viz_bokeh import save_bokeh_training_vs_ideals                              # optional bokeh interactive saver

__all__ = [                                                                             # public API of the package
    "DLMDSPError", "DataShapeMismatchError", "AssignmentRuleError",                  # exceptions to expose
    "BaseCsvLoader", "TrainingCsvLoader", "IdealCsvLoader", "TestCsvLoader",         # loader classes to expose
    "load_training_csv", "load_ideal_csv", "load_test_csv",                           # loader functions to expose
    "create_sqlite_engine", "write_dataframe",                                        # DB helpers to expose
    "choose_best_ideal_columns", "compute_tolerances",                                # modeling helpers to expose
    "build_ideal_lookup", "assign_single_test_point", "stream_and_store_test_results",# mapping helpers to expose
    "quick_plot_training_vs_ideals", "save_bokeh_training_vs_ideals",                 # visualization helpers to expose
]                                                                                      # end __all__
