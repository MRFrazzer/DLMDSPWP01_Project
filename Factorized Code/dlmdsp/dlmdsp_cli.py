# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_cli.py                                                                   # module: orchestration entry
# ──────────────────────────────────────────────────────────────────────────────
"""Command-line runner for the DLMDSP pipeline.

When I run, I:
1) Load the CSVs
2) Write training and ideal to SQLite
3) Pick the closest ideals for Y1..Y4
4) Compute tolerances
5) Assign test rows and write `test_mapping`
6) Print a short summary
"""

from __future__ import annotations                                                # modern typing
from pathlib import Path                                                          # file paths
import os                                                                         # debug: current working dir
import sys                                                                        # debug: script location
import pandas as pd                                                                # handy when debugging prints
from .dlmdsp_exceptions import DataShapeMismatchError, AssignmentRuleError           # clear error types
from .dlmdsp_loaders import TrainingCsvLoader, IdealCsvLoader, TestCsvLoader         # CSV readers
from .dlmdsp_database import create_sqlite_engine, write_dataframe                   # DB helpers
from .dlmdsp_model_selection import choose_best_ideal_columns, compute_tolerances    # modeling helpers
from .dlmdsp_mapping import build_ideal_lookup, stream_and_store_test_results        # assignment helpers
from .dlmdsp_plots import quick_plot_training_vs_ideals                            # optional: matplotlib
from .dlmdsp_viz_bokeh import save_bokeh_training_vs_ideals                        # optional: bokeh


def main() -> None:                                                               # entry function to run pipeline
    """Run the end-to-end DLMDSP workflow with the configured file paths."""
    data_dir = Path(                                                               # directory containing CSVs
        r"C:/Users/micha/OneDrive - itsgroupgy.com/Personal Development/"
        r"Ai text/ai AND SOCIETY/assignment"
    )                                                                              # end Path
    training_path = data_dir / "training.csv"                                     # training CSV path
    ideal_path = data_dir / "ideal.csv"                                           # ideal CSV path
    test_path = data_dir / "test.csv"                                             # test CSV path
    sqlite_path = Path("assignment.db")                                           # SQLite DB output path

    training_df = TrainingCsvLoader(training_path).load()                          # read+validate training
    ideal_df = IdealCsvLoader(ideal_path).load()                                   # read+validate ideal
    test_df = TestCsvLoader(test_path).load()                                      # read+validate test

    for df in (training_df, ideal_df, test_df):                                    # normalize headers
        df.columns = [str(c).strip() for c in df.columns]                          # strip accidental spaces

    engine = create_sqlite_engine(sqlite_path)                                     # create database engine
    write_dataframe(training_df, "training", engine)                              # write training table
    write_dataframe(ideal_df, "ideal", engine)                                    # write ideal table

    training_targets = [c for c in training_df.columns if c != "X"]              # expected ['Y1'..'Y4']
    if len(training_targets) != 4:                                                 # guard for spec compliance
        raise DataShapeMismatchError(                                              # raise helpful error
            f"Expected 4 training Y columns, found {len(training_targets)}: {training_targets}"  # message
        )                                                                          # end raise

    best_map = choose_best_ideal_columns(training_df, ideal_df, x_col="X")        # select best ideals
    chosen_ideals_in_order = [best_map[t] for t in training_targets]               # preserve Y1..Y4 order

    tolerances = compute_tolerances(training_df, ideal_df, best_map, x_col="X")   # compute per-ideal tolerance

    quick_plot_training_vs_ideals(training_df, ideal_df, best_map, x_col="X")   # optional preview

    ideal_lookup_df = build_ideal_lookup(ideal_df, chosen_ideals_in_order, x_col="X")  # compact lookup
    stream_and_store_test_results(                                                 # process and append results
        test_df=test_df,                                                           # pass test DF
        ideal_lookup_df=ideal_lookup_df,                                           # pass lookup DF
        chosen_ideals=chosen_ideals_in_order,                                      # pass chosen ideal names
        tolerances=tolerances,                                                     # pass tolerance dict
        engine=engine,                                                             # pass DB engine
        x_col="X",                                                                # X column name
    )                                                                              # end call

    save_bokeh_training_vs_ideals(engine, best_map, tolerances, x_col="X", save_path="bokeh_training_vs_ideals.html", open_in_browser=True)  # optional interactive

    print("=== SUMMARY ===")                                                       # header line
    print(f"SQLite file          : {sqlite_path.resolve()}")                      # report DB path
    print(f"Training table shape : {training_df.shape}")                          # report training shape
    print(f"Ideal table shape    : {ideal_df.shape}")                              # report ideal shape
    print(f"Test rows processed  : {len(test_df)}")                               # report test row count
    print("Chosen ideals (Y1..Y4 -> IdealFuncNo 1..4):")                          # header for mapping
    for ideal_number, (training_name, ideal_name) in enumerate(zip(training_targets, chosen_ideals_in_order), 1):  # iterate mapping
        print(f"  {training_name} -> {ideal_name} (IdealFuncNo={ideal_number})")   # print mapping line
    print("Tolerances used (per IdealFuncNo):", tolerances)                        # print tolerances dict
    print("Created/overwritten tables: training, ideal, test_mapping")            # list affected tables


if __name__ == "__main__":                                                        # allow `python -m dlmdsp.cli`
    """Run the pipeline when executed as a script.

    I print a couple of paths for context, call main(), and show clear messages
    for common error cases.
    """  # block docstring
    print("CWD:", os.getcwd())                                                     # show current working dir
    print("argv[0] dir:", os.path.dirname(sys.argv[0]))                            # show script folder
    try:                                                                           # run with error handling
        main()                                                                      # execute pipeline
    except DataShapeMismatchError as exc:                                          # schema validation issues
        print(f"[ERROR] Data validation failed: {exc}")                            # human-friendly error
    except AssignmentRuleError as exc:                                             # assignment tolerance failures
        print(f"[ERROR] Compiling criterion not met: {exc}")                       # human-friendly error
    except FileNotFoundError as exc:                                               # missing file paths
        print(f"[ERROR] Could not find file: {exc}")                               # human-friendly error
    except Exception as exc:                                                       # unexpected exceptions
        print(f"[ERROR] Unexpected issue: {exc}")                                  # catch-all message
