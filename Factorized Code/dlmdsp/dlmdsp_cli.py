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

# ──────────────────────────────────────────────────────────────────────────────
# Excel export helper creates 3 sheets from the tables in the database as well as a sheet to record the rejected rows from the test dataset.
# ──────────────────────────────────────────────────────────────────────────────
def export_db_to_excel(db_path, out_path=None, rejections_csv="test_rejections.csv"):
    """
    Export the SQLite tables ('training', 'ideal', 'test_mapping') to an Excel
    workbook, and (optionally) add a 4th sheet 'test_rejections' from a CSV file.

    Parameters
    ----------
    db_path : str | pathlib.Path
        Path to the SQLite database file, e.g. 'assignment.db'.
    out_path : str | pathlib.Path | None
        Optional output .xlsx path. If None, a timestamped file is created
        next to the DB (e.g., 'assignment_export_YYYYMMDD_HHMMSS.xlsx').
    rejections_csv : str | pathlib.Path
        Path to the CSV with rejected rows (e.g., 'test_rejections.csv').
        If the file does not exist, the export still succeeds without that sheet.

    Returns
    -------
    str
        Filesystem path to the written Excel file.

    Notes
    -----
    • This function does NOT write rejections to the DB. It only reads them
      from a CSV and adds them as a 4th Excel sheet.
    • Requires 'pandas' and 'openpyxl'.
    """
    from pathlib import Path               # path handling
    from datetime import datetime          # timestamp for default filename
    import sqlite3                         # DB connector
    import pandas as pd                    # table IO
    import os                              # file existence check

    db_path = Path(db_path)                # normalize to Path
    if not db_path.exists():               # safety: DB must exist
        raise FileNotFoundError(f"DB not found: {db_path}")

    # Build default Excel filename if none provided
    if out_path is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = db_path.with_name(f"{db_path.stem}_export_{stamp}.xlsx")

        # Keep only one timestamped export: delete older ones in the same folder
        for old in db_path.parent.glob(f"{db_path.stem}_export_*.xlsx"):
            if old != out_path:  # don't touch the file we are about to write
                try:
                    old.unlink()
                except Exception as e:
                    print(f"[WARN] Could not delete old export {old}: {e}")

    out_path = str(Path(out_path))         # ExcelWriter prefers plain str
    rejections_csv = Path(rejections_csv)  # normalize to Path for checks

    # Open DB connection and Excel writer
    with sqlite3.connect(str(db_path)) as con, pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        # 1) Write the three DB tables as individual sheets (skip if missing)
        for table in ("training", "ideal", "test_mapping"):
            exists = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                con, params=[table]
            )
            if exists.empty:
                print(f"[WARN] table '{table}' not found; skipping")
                continue
            df = pd.read_sql(f"SELECT * FROM {table};", con)    # read full table
            df.to_excel(xw, sheet_name=table, index=False)      # write sheet

        # 2) Append a 4th sheet from the CSV of rejections (only if file exists)cl
        if rejections_csv.exists():
            try:
                rej_df = pd.read_csv(rejections_csv)            # read CSV of rejects
                rej_df.to_excel(xw, sheet_name="test_rejections", index=False)
                print(f"[INFO] Added rejection sheet from: {rejections_csv}")
            except Exception as e:
                print(f"[WARN] Could not add 'test_rejections' sheet: {e}")
        else:
            print(f"[INFO] No rejections CSV found at {rejections_csv} — skipping 4th sheet")

    print(f"[INFO] Excel export written to: {out_path}")
    return out_path
# ──────────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────────
# Reset mapping tables so results don't accumulate across runs
# ──────────────────────────────────────────────────────────────────────────────
def reset_mapping_tables(engine, reset_rejections: bool = True) -> None:
    """
    Drop and recreate the mapping tables so each run starts clean.

    Parameters
    ----------
    engine : sqlalchemy.Engine
        Your SQLAlchemy engine connected to assignment.db.
    reset_rejections : bool
        If True, also reset the optional 'test_rejections' table.
    """
    import pandas as pd
    from sqlalchemy import text

    # 1) Drop existing tables if they exist (safe no-ops if they don't)
    with engine.begin() as conn:                      # single transaction
        conn.execute(text("DROP TABLE IF EXISTS test_mapping;"))
        if reset_rejections:
            conn.execute(text("DROP TABLE IF EXISTS test_rejections;"))

    # 2) Recreate empty tables with the expected schemas
    #    (so downstream .to_sql(..., if_exists='append') will append cleanly)
    pd.DataFrame(columns=["X", "Y", "DeltaY", "IdealFuncNo"]).to_sql(
        "test_mapping", engine, if_exists="replace", index=False
    )
    if reset_rejections:
        pd.DataFrame(columns=["X", "Y", "reason"]).to_sql(
            "test_rejections", engine, if_exists="replace", index=False
        )

def main() -> None:  # entry function to run pipeline
    """
    Run the end-to-end DLMDSP workflow.

    Steps performed:
      1) Resolve input/output paths
      2) Load CSVs (training, ideal, test) and normalize headers
      3) Create SQLite engine (and optionally reset mapping tables to avoid accumulation)
      4) Write training/ideal tables to the DB
      5) Choose the four best ideals (least squares) and compute tolerances (√2 × max train residual)
      6) Build compact ideal lookup and assign the test rows (append accepted rows to test_mapping)
      7) Save an optional interactive Bokeh view
      8) Print a concise run summary
      9) Export an Excel workbook with 3 DB sheets (+ optional 4th sheet from CSV rejections)
     10) Dispose the engine cleanly (even on error)
    """
    engine = None  # ensure the name exists even if engine creation fails

    try:
        # --- Paths / inputs ----------------------------------------------------
        data_dir = Path(  # base folder containing your three CSVs (edit to your own path if needed)
            r"C:/Users/micha/OneDrive - itsgroupgy.com/Personal Development/"
            r"Ai text/ai AND SOCIETY/assignment"
        )
        training_path = data_dir / "training.csv"   # training CSV path
        ideal_path = data_dir / "ideal.csv"         # ideal CSV path
        test_path = data_dir / "test.csv"           # test CSV path
        sqlite_path = Path("assignment.db")         # SQLite DB filename in CWD

        # --- Load CSVs ---------------------------------------------------------
        training_df = TrainingCsvLoader(training_path).load()  # read + validate training
        ideal_df = IdealCsvLoader(ideal_path).load()           # read + validate ideal
        test_df = TestCsvLoader(test_path).load()              # read + validate test

        # Normalize headers: remove stray spaces so column names are exactly "X", "Y1".. etc.
        for df in (training_df, ideal_df, test_df):
            df.columns = [str(c).strip() for c in df.columns]  # strip accidental spaces

        # --- Create engine BEFORE any function that needs it -------------------
        engine = create_sqlite_engine(sqlite_path)  # open a SQLite engine for assignment.db

        # Start each run fresh (no accumulation in test_mapping / optional test_rejections)
        reset_mapping_tables(engine, reset_rejections=True)

        # --- Persist training / ideal -----------------------------------------
        write_dataframe(training_df, "training", engine)  # create/replace training table
        write_dataframe(ideal_df, "ideal", engine)        # create/replace ideal table

        # --- Model selection & tolerances -------------------------------------
        training_targets = [c for c in training_df.columns if c != "X"]  # expect exactly ['Y1','Y2','Y3','Y4']
        if len(training_targets) != 4:  # guard for spec compliance
            # Raise a clear error if the training CSV doesn't have 4 Y columns
            raise DataShapeMismatchError(
                f"Expected 4 training Y columns, found {len(training_targets)}: {training_targets}"
            )

        best_map = choose_best_ideal_columns(training_df, ideal_df, x_col="X")  # pick 4 best ideals for Y1..Y4
        chosen_ideals_in_order = [best_map[t] for t in training_targets]        # preserve Y1..Y4 order

        tolerances = compute_tolerances(  # compute √2 × max training |residual| per chosen ideal
            training_df, ideal_df, best_map, x_col="X"
        )

        # Optional quick plot (static matplotlib preview of training vs chosen ideals)
        quick_plot_training_vs_ideals(training_df, ideal_df, best_map, x_col="X")

        # --- Map test rows -----------------------------------------------------
        ideal_lookup_df = build_ideal_lookup(  # small DF: X + four chosen ideal columns
            ideal_df, chosen_ideals_in_order, x_col="X"
        )

        # Stream over test rows, assign by tolerance rule, append accepted rows to DB table 'test_mapping'
        stream_and_store_test_results(
            test_df=test_df,                   # all test points
            ideal_lookup_df=ideal_lookup_df,   # X + chosen ideals lookup
            chosen_ideals=chosen_ideals_in_order,  # ['Yxx','Yyy','Yzz','Yww'] in Y1..Y4 order
            tolerances=tolerances,             # dict: {'1': tol1, '2': tol2, '3': tol3, '4': tol4}
            engine=engine,                     # DB engine for writing 'test_mapping'
            x_col="X",                         # name of the X column
        )

        # Optional interactive Bokeh tabs (saved to HTML)
        save_bokeh_training_vs_ideals(
            engine,                            # the engine used to read training/ideal inside viz
            best_map,                          # mapping Y1..Y4 -> ideal names
            tolerances,                        # tolerances dict for annotation
            x_col="X",                         # X column
            save_path="bokeh_training_vs_ideals.html",  # output HTML filename
            open_in_browser=True               # auto-open in default browser
        )

        # --- Summary -----------------------------------------------------------
        print("=== SUMMARY ===")  # header line
        print(f"SQLite file          : {sqlite_path.resolve()}")  # DB absolute path
        print(f"Training table shape : {training_df.shape}")      # shape of training DF
        print(f"Ideal table shape    : {ideal_df.shape}")         # shape of ideal DF
        print(f"Test rows processed  : {len(test_df)}")           # number of test rows examined
        print("Chosen ideals (Y1..Y4 -> IdealFuncNo 1..4):")      # header for mapping
        for ideal_number, (training_name, ideal_name) in enumerate(
            zip(training_targets, chosen_ideals_in_order), 1
        ):
            print(f"  {training_name} -> {ideal_name} (IdealFuncNo={ideal_number})")  # mapping line
        print("Tolerances used (per IdealFuncNo):", tolerances)  # show the 4 tolerance values
        print("Created/overwritten tables: training, ideal, test_mapping")  # DB effects

        # --- Excel export (DB sheets + optional 4th from CSV) ------------------
        try:
            # Writes: training, ideal, test_mapping from DB; plus test_rejections.csv if it exists
            export_db_to_excel(sqlite_path, rejections_csv="test_rejections.csv")
        except Exception as e:
            print(f"[WARN] Excel export skipped: {e}")  # don't fail the run if Excel export fails

    finally:
        # Always dispose the engine if it was created; protects against locked DB handles on Windows
        if engine is not None:
            try:
                engine.dispose()  # release pooled connections/handles
            except Exception:
                pass  # ignore dispose errors to keep shutdown clean


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
