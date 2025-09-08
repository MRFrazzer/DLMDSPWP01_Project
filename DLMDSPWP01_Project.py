#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DLMDSP WP01 — End-to-end pipeline aligned to the written assignment.

Flow (simple, “learners-first”):
1) Custom exceptions
2) CSV loaders (Training / Ideal / Test)
3) SQLite helpers (engine + write table)
4) Model selection (pick four ideal functions) + tolerances
5) Test row assignment + persistence (test_mapping)
6) Optional plots (matplotlib quick plots; Bokeh interactive tabs)

Tables created:
- training          (X, Y1, Y2, Y3, Y4)
- ideal             (X, Y1..Y50)
- test_mapping      (X, Y, DeltaY, IdealFuncNo)
"""

from __future__ import annotations  # allow modern type hinting in older Python versions

from dataclasses import dataclass  # for simple data containers
from pathlib import Path  # path handling that works on all OSes
from typing import Dict, List, Tuple, Optional  # type hints

import os  # used only in __main__ for printing current dir info
import sys  # used only in __main__ for printing argv[0] info

import pandas as pd  # main data table library
from sqlalchemy import create_engine  # to create a SQLite connection
from sqlalchemy.engine import Engine  # for type hints of SQLAlchemy engine


# =========================
# 1) Custom Exceptions
# =========================

class DLMDSPError(Exception):
    """Base error for this assignment."""


class DataShapeMismatchError(DLMDSPError):
    """Raised when required columns or counts do not match the spec."""


class AssignmentRuleError(DLMDSPError):
    """Raised when a test row cannot be assigned under the criterion."""


# =========================
# 2) CSV Loaders
# =========================

@dataclass
class BaseCSVLoader:
    """
    Base CSV loader that requires an 'X' column.

    Attributes:
        path: Path to the CSV file.
        x_col: Name of the X column (default: 'X').
    """
    path: Path  # where to read CSV from
    x_col: str = "X"  # the name of the X column we expect

    def load(self) -> pd.DataFrame:
        """
        Load a CSV and validate the presence of the X column.

        Returns:
            A pandas DataFrame containing the file data.

        Raises:
            DataShapeMismatchError: If the X column is missing.
        """
        df = pd.read_csv(self.path)  # read CSV into DataFrame
        if self.x_col not in df.columns:  # verify required X column exists
            raise DataShapeMismatchError(
                f"Missing '{self.x_col}' in {self.path}. "
                f"Found columns: {list(df.columns)}"
            )
        return df  # return the loaded DataFrame


class TrainingLoader(BaseCSVLoader):
    """
    Loader for the training dataset.

    Expected columns: X, Y1, Y2, Y3, Y4 (exactly five columns).
    """
    def load(self) -> pd.DataFrame:
        df = super().load()  # reuse base loading + X check
        y_cols = [c for c in df.columns if c != self.x_col]  # all Ys except X
        if len(y_cols) != 4:  # training must have exactly 4 Y columns
            raise DataShapeMismatchError(
                f"Training must have exactly 4 Y columns; got {len(y_cols)} -> {y_cols}"
            )
        return df


class IdealLoader(BaseCSVLoader):
    """
    Loader for the ideal dataset.

    Expected columns: X, Y1..Y50 (exactly 51 columns).
    """
    def load(self) -> pd.DataFrame:
        df = super().load()  # reuse base loading + X check
        y_cols = [c for c in df.columns if c != self.x_col]  # ideal Ys
        if len(y_cols) != 50:  # should be exactly 50 ideal columns
            preview = y_cols[:10]  # show first few for debugging
            raise DataShapeMismatchError(
                "Ideal must have exactly 50 Y columns; "
                f"got {len(y_cols)}. First 10: {preview}"
            )
        return df


class TestLoader(BaseCSVLoader):
    """
    Loader for the test dataset.

    Expected columns: X, Y (exactly two columns).
    """
    def load(self) -> pd.DataFrame:
        df = super().load()  # reuse base loading + X check
        if "Y" not in df.columns:  # test must include Y
            raise DataShapeMismatchError("Test data must contain a 'Y' column.")
        return df


# Convenience wrappers (handy for unit tests)
def load_training_data(path: str | Path) -> pd.DataFrame:
    """Load training CSV from a given path."""
    return TrainingLoader(Path(path)).load()  # cast to Path for reliability


def load_ideals(path: str | Path) -> pd.DataFrame:
    """Load ideal CSV from a given path."""
    return IdealLoader(Path(path)).load()


def load_test_data(path: str | Path) -> pd.DataFrame:
    """Load test CSV from a given path."""
    return TestLoader(Path(path)).load()


# =========================
# 3) SQLite Helpers
# =========================

def make_engine(sqlite_path: Path) -> Engine:
    """
    Create a SQLAlchemy engine for a SQLite file.

    Args:
        sqlite_path: Path to the SQLite database file.

    Returns:
        A SQLAlchemy Engine connected to the given SQLite file.
    """
    return create_engine(f"sqlite:///{sqlite_path.as_posix()}", echo=False)  # echo=False → no SQL logs


def write_table(df: pd.DataFrame, table: str, engine: Engine) -> None:
    """
    Write (or replace) a DataFrame into a SQLite table.

    Args:
        df: Data to write.
        table: SQLite table name.
        engine: Open SQLAlchemy Engine.
    """
    df.to_sql(table, engine, if_exists="replace", index=False)  # overwrite table for reproducibility


# =========================
# 4) Model Selection + Tolerances
# =========================

def _rmse(a: pd.Series, b: pd.Series) -> float:
    """
    Compute the root-mean-square error between two aligned series.

    Args:
        a: First numeric series.
        b: Second numeric series.

    Returns:
        The RMSE value as a float.
    """
    diff = a.values - b.values  # vector of differences
    return float((diff ** 2).mean() ** 0.5)  # sqrt(mean(square(diff)))


def select_best_ideals(
    training: pd.DataFrame,
    ideal: pd.DataFrame,
    x_col: str = "X",
) -> Dict[str, str]:
    """
    For each training target (Y1..Y4), choose the ideal column with minimum RMSE.

    This aligns on X (inner join) to compare values on the common grid.

    Args:
        training: DataFrame with columns ['X', 'Y1', 'Y2', 'Y3', 'Y4'].
        ideal: DataFrame with columns ['X', 'Y1'..'Y50'].
        x_col: Name of the X column (default: 'X').

    Returns:
        A mapping like {'Y1': 'Y17', 'Y2': 'Y8', 'Y3': 'Y22', 'Y4': 'Y41'}.
    """
    merged = pd.merge(training, ideal, on=x_col, how="inner", suffixes=("", "_ideal"))  # align rows by X

    train_targets = [c for c in training.columns if c != x_col]  # ['Y1','Y2','Y3','Y4']
    ideal_targets = [c for c in ideal.columns if c != x_col]  # ['Y1'..'Y50']

    mapping: Dict[str, str] = {}  # will store best ideal per training column
    for tcol in train_targets:  # loop over Y1..Y4
        best_col: Optional[str] = None  # track which ideal is best so far
        best_score = float("inf")  # RMSE starts at +∞ so any real score is lower
        for icol in ideal_targets:  # check each ideal candidate
            # If an ideal column name also exists in training (Y1..Y4),
            # the merged DataFrame stores it as '<name>_ideal'.
            icol_in_merged = f"{icol}_ideal" if icol in train_targets else icol  # avoid column collision
            score = _rmse(merged[tcol], merged[icol_in_merged])  # compute RMSE on common X
            if score < best_score:  # keep the lowest RMSE
                best_score = score
                best_col = icol
        if best_col is None:  # safety check (should not happen)
            raise DLMDSPError(f"Could not select an ideal for {tcol}.")
        mapping[tcol] = best_col  # remember the best ideal for this Yk
    return mapping


def compute_tolerances(
    training: pd.DataFrame,
    ideal: pd.DataFrame,
    mapping: Dict[str, str],
    x_col: str = "X",
    scale: float = 2 ** 0.5,  # sqrt(2) per assignment rule
) -> Dict[str, float]:
    """
    Compute one tolerance value per chosen ideal function.

    Definition:
        tolerance_k = scale * max_abs(Y_k_training - Y_k_ideal)

    Where `scale = sqrt(2)` by default (assignment rule).

    Args:
        training: Training DataFrame.
        ideal: Ideal DataFrame.
        mapping: Mapping from training Yk -> ideal Yj (e.g., {'Y1': 'Y17', ...}).
        x_col: Name of the X column.
        scale: Multiplier applied to the max absolute residual.

    Returns:
        Dict where keys are '1','2','3','4' (IdealFuncNo) and values are tolerances.
    """
    merged = pd.merge(training, ideal, on=x_col, how="inner", suffixes=("", "_ideal"))  # align by X
    train_targets = [c for c in training.columns if c != x_col]  # list of training Ys

    tolerances: Dict[str, float] = {}  # result per IdealFuncNo
    for idx, (tcol, icol) in enumerate(mapping.items(), start=1):  # keep 1..4 numbering
        icol_in_merged = f"{icol}_ideal" if icol in train_targets else icol  # resolve column name
        max_abs = (merged[tcol] - merged[icol_in_merged]).abs().max()  # max absolute residual on training set
        tolerances[str(idx)] = float(scale * max_abs)  # tolerance = sqrt(2)*max_abs
    return tolerances


# =========================
# 5) Test Assignment + Persistence
# =========================

def _prepare_ideal_lookup(
    ideal: pd.DataFrame,
    chosen_ideals: List[str],
    x_col: str = "X",
) -> pd.DataFrame:
    """
    Build a small lookup DataFrame with X and the four chosen ideal columns.

    Args:
        ideal: The full ideal DataFrame (X + Y1..Y50).
        chosen_ideals: The four chosen ideal column names, in order.
        x_col: Name of the X column.

    Returns:
        A DataFrame with columns [X, chosen_ideals...].
    """
    cols = [x_col] + chosen_ideals  # only keep X and selected ideals
    return ideal[cols].copy()  # copy to avoid modifying original


def assign_test_row(
    x: float,
    y: float,
    ideal_lookup: pd.DataFrame,
    chosen_ideals: List[str],
    tolerances: Dict[str, float],
    x_col: str = "X",
) -> Tuple[str, float]:
    """
    Assign a single test point (x, y) to one of the four chosen ideals.

    Strategy (simple and deterministic):
      1) Try exact X match; otherwise use the nearest X in the lookup.
      2) Compute |y - y_ideal_k| for each chosen ideal k = 1..4.
      3) Pick the smallest deviation that is <= tolerance_k.
      4) If none fits, raise AssignmentRuleError.

    Args:
        x: X value of the test point.
        y: Measured Y value of the test point.
        ideal_lookup: DataFrame with [X, ideal1, ideal2, ideal3, ideal4].
        chosen_ideals: The four ideal column names in order.
        tolerances: Dict mapping '1'..'4' to tolerance floats.
        x_col: Name of the X column (default 'X').

    Returns:
        A tuple (IdealFuncNo, DeltaY) where:
            - IdealFuncNo is '1'..'4' (as a string),
            - DeltaY is the absolute deviation used for the decision.

    Raises:
        AssignmentRuleError: If no ideal satisfies its tolerance.
    """
    # 1) Match by X (exact or nearest)
    row = ideal_lookup.loc[ideal_lookup[x_col] == x]  # try exact match on X
    if row.empty:  # if no exact match, pick the nearest X
        nearest_idx = (ideal_lookup[x_col] - x).abs().idxmin()  # index of closest X
        row = ideal_lookup.loc[[nearest_idx]]  # keep as single-row DataFrame
    row = row.squeeze()  # convert single-row DataFrame → Series for easy access

    # 2) Compute deviations per ideal
    deviations: List[Tuple[str, float]] = []  # list of (IdealFuncNo, deviation)
    for idx, col in enumerate(chosen_ideals, start=1):  # idx=1..4
        dy = abs(y - float(row[col]))  # absolute difference vs that ideal at this X
        deviations.append((str(idx), dy))  # remember which ideal # and its deviation

    # 3) Choose the smallest deviation that passes its tolerance
    deviations.sort(key=lambda t: t[1])  # smallest deviation first
    for k, dy in deviations:
        if dy <= tolerances[k]:  # if within that ideal's tolerance → accept
            return k, dy  # return ideal number as string and the deviation

    # 4) No match
    raise AssignmentRuleError(
        f"No valid assignment for x={x}, y={y}; "
        f"deviations={deviations}, tolerances={tolerances}"
    )


def stream_and_store_test_results(
    test_df: pd.DataFrame,
    ideal_lookup: pd.DataFrame,
    chosen_ideals: List[str],
    tolerances: Dict[str, float],
    engine: Engine,
    x_col: str = "X",
) -> None:
    """
    Iterate test rows in order, assign each to an ideal, and append to SQLite.

    Writes to table: test_mapping(X, Y, DeltaY, IdealFuncNo)
    """
    out_rows: List[Dict[str, float | int]] = []  # will hold rows to write
    for _, r in test_df.iterrows():  # go row-by-row through test data
        k, dy = assign_test_row(
            x=float(r[x_col]),  # ensure numeric
            y=float(r["Y"]),
            ideal_lookup=ideal_lookup,
            chosen_ideals=chosen_ideals,
            tolerances=tolerances,
            x_col=x_col,
        )
        out_rows.append(
            {
                "X": float(r[x_col]),
                "Y": float(r["Y"]),
                "DeltaY": float(dy),     # deviation used for the decision
                "IdealFuncNo": int(k),   # store as integer 1..4
            }
        )
    pd.DataFrame(out_rows).to_sql(
        "test_mapping", engine, if_exists="append", index=False  # append so we can re-run in parts if needed
    )


# =========================
# 5B) Quick Matplotlib Plots (Optional)
# =========================

def quick_plot_all_training_vs_ideals(
    training: pd.DataFrame,
    ideal: pd.DataFrame,
    mapping: Dict[str, str],
    x_col: str = "X",
) -> None:
    """
    Create 4 simple line plots: each training Yk vs its chosen ideal.

    Note: This function shows figures immediately. Use in notebooks or scripts.
    """
    import matplotlib.pyplot as plt  # local import to keep top clean and optional

    train_targets = [c for c in training.columns if c != x_col]  # ['Y1'..'Y4']
    for tcol in train_targets:
        icol = mapping[tcol]  # chosen ideal for this training column
        merged = pd.merge(
            training[[x_col, tcol]],
            ideal[[x_col, icol]],
            on=x_col,
            how="inner",
            suffixes=("", "_ideal"),
        )
        plt.figure()  # new figure for each pair
        plt.plot(merged[x_col], merged[tcol], label=tcol)  # plot training
        plt.plot(merged[x_col], merged[icol], label=f"{icol} (ideal)")  # plot ideal
        plt.title(f"{tcol} vs {icol}")  # simple title
        plt.xlabel(x_col)
        plt.ylabel("Value")
        plt.legend()
        plt.tight_layout()  # prevent label clipping
        plt.show()  # display plot


# =========================
# 5C) Interactive Bokeh Tabs (Optional)
# =========================

def _bokeh_single_panel(
    training: pd.DataFrame,
    ideal: pd.DataFrame,
    tm_all: Optional[pd.DataFrame],
    tcol: str,
    icol: str,
    tol: float,
    idx_for_this_panel: int,
    x_col: str = "X",
):
    """
    Create a single Bokeh TabPanel with:
      - training vs chosen ideal line plots
      - ± tolerance band
      - accepted test points (for this ideal)
      - rejected points (relative to this ideal)
      - residual plot (ΔY vs X) and simple coverage text
    """
    from bokeh.models import ColumnDataSource, HoverTool, Band, TabPanel, Div  # Bokeh building blocks
    from bokeh.plotting import figure  # to create figures
    from bokeh.layouts import column  # to stack plots vertically

    merged = pd.merge(
        training[[x_col, tcol]],
        ideal[[x_col, icol]],
        on=x_col,
        how="inner",
        suffixes=("", "_ideal"),
    ).rename(columns={icol: "ideal_y", tcol: "train_y", x_col: "x"})  # standardize column names for plotting

    merged["upper"] = merged["ideal_y"] + tol  # upper band = ideal + tol
    merged["lower"] = merged["ideal_y"] - tol  # lower band = ideal - tol
    src = ColumnDataSource(merged)  # Bokeh data source

    # Main figure
    p = figure(
        width=840, height=420,
        title=f"{tcol} vs {icol} (tolerance ±{tol:.4g})",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",  # enable mouse wheel zoom by default
    )
    band = Band(base="x", lower="lower", upper="upper", source=src,
                level="underlay", fill_alpha=0.15, line_alpha=0.0)  # shaded tolerance area
    p.add_layout(band)
    train_line = p.line("x", "train_y", source=src, line_width=2, legend_label=tcol)  # training line
    ideal_line = p.line("x", "ideal_y", source=src, line_width=2,
                        line_dash="dashed", legend_label=f"{icol} (ideal)")  # ideal dashed line

    tm_accept_src = None  # placeholders for conditional layers
    tm_reject_src = None
    accepted_count = 0
    total_count = 0

    if tm_all is not None and not tm_all.empty:  # only if we have test_mapping saved
        total_count = len(tm_all)
        tm_accept = tm_all.loc[
            tm_all["IdealFuncNo"] == idx_for_this_panel,
            ["X", "Y", "DeltaY", "IdealFuncNo"],
        ].copy()  # only points assigned to this ideal
        accepted_count = len(tm_accept)
        if accepted_count > 0:
            tm_accept.rename(columns={"X": "x"}, inplace=True)  # match plot's x name
            tm_accept_src = ColumnDataSource(tm_accept)
            pts = p.scatter("x", "Y", size=6, alpha=0.9, source=tm_accept_src,
                            legend_label="test points")  # accepted points
            p.add_tools(HoverTool(
                renderers=[pts],
                tooltips=[("X", "@x{0.#####}"), ("Y (test)", "@Y{0.#####}"),
                          ("ΔY", "@DeltaY{0.#####}"), ("Ideal#", "@IdealFuncNo")]
            ))

        # “Rejected for this ideal” = |Y - ideal(x)| > tol (even if they were accepted by another ideal)
        ideal_for_merge = ideal[[x_col, icol]].rename(columns={x_col: "x", icol: "ideal_y"})  # ideal curve
        tm_all_x = tm_all[["X", "Y", "DeltaY", "IdealFuncNo"]].rename(columns={"X": "x"}).copy()  # all test points
        rej = pd.merge(tm_all_x, ideal_for_merge, on="x", how="left")  # attach ideal value at each x
        rej["delta_here"] = (rej["Y"] - rej["ideal_y"]).abs()  # deviation vs this ideal
        tm_reject = rej.loc[rej["delta_here"] > tol, ["x", "Y", "delta_here", "IdealFuncNo"]].copy()  # filter out-of-band

        if not tm_reject.empty:
            tm_reject_src = ColumnDataSource(tm_reject)
            rej_pts = p.scatter("x", "Y", size=8, marker="x", line_width=2,
                                line_alpha=0.9, fill_alpha=0.0, line_color="red",
                                source=tm_reject_src, legend_label="rejected (this ideal)")  # mark as X
            p.add_tools(HoverTool(
                renderers=[rej_pts],
                tooltips=[("X", "@x{0.#####}"), ("Y (test)", "@Y{0.#####}"),
                          ("ΔY (this ideal)", "@delta_here{0.#####}"),
                          ("Assigned Ideal#", "@IdealFuncNo"),
                          ("Status", "rejected")]
            ))

    p.add_tools(HoverTool(
        renderers=[train_line, ideal_line],
        tooltips=[("X", "@x{0.#####}"),
                  ("Training", "@train_y{0.#####}"),
                  ("Ideal", "@ideal_y{0.#####}")]
    ))
    p.legend.location = "top_left"  # keep legend visible
    p.legend.click_policy = "hide"  # allow toggling series by clicking legend

    # Residual figure
    r = figure(
        width=840, height=260,
        title=f"Residuals (ΔY) — {tcol}/{icol}",
        x_axis_label="X", y_axis_label="ΔY",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
    )
    # Keep hover X synced (draw invisible line so hover shares x-axis)
    r.line("x", "train_y", source=src, alpha=0.0)  # invisible helper line
    residual_series = merged["train_y"] - merged["ideal_y"]  # training residuals
    res_src = ColumnDataSource({"x": merged["x"], "res": residual_series})
    r.line("x", "res", source=res_src, line_width=2,
           legend_label="training residual (Yk - ideal)")  # residual curve

    if tm_accept_src is not None:  # show accepted test ΔY if present
        r.scatter("x", "DeltaY", source=tm_accept_src, size=6, alpha=0.9,
                  legend_label="test ΔY (accepted)")
        r.add_tools(HoverTool(tooltips=[("X", "@x{0.#####}"), ("ΔY", "@DeltaY{0.#####}")]))
    r.legend.location = "top_left"
    r.legend.click_policy = "hide"

    # Coverage note (simple % of points assigned to this ideal out of all)
    coverage = 100.0 * accepted_count / total_count if total_count else 0.0
    stats = Div(text=f"<b>Coverage for {icol}: accepted {accepted_count} / total {total_count} "
                     f"({coverage:.1f}%)</b>")

    return TabPanel(child=column(p, r, stats), title=tcol)  # return as a tab


def bokeh_plot_all_training_vs_ideals(
    engine: Engine,
    mapping: Dict[str, str],
    tolerances: Dict[str, float],
    x_col: str = "X",
    save_path: str = "bokeh_training_vs_ideals.html",
    show_in_browser: bool = True,
) -> None:
    """
    Save an interactive Bokeh Tabs HTML with tolerance bands and test points.

    Args:
        engine: SQLAlchemy engine (reads tables training/ideal/test_mapping).
        mapping: Training Yk -> ideal Yj mapping.
        tolerances: {'1': tol1, '2': tol2, '3': tol3, '4': tol4}
        x_col: Name of the X column.
        save_path: Output HTML file.
        show_in_browser: Whether to open the HTML after saving.
    """
    from bokeh.io import output_file, save, show  # output helpers
    from bokeh.models import Tabs  # container for multiple TabPanel

    with engine.connect() as conn:  # open one connection for all reads
        training = pd.read_sql_query("SELECT * FROM training", conn)  # fetch training
        ideal = pd.read_sql_query("SELECT * FROM ideal", conn)  # fetch ideal
        try:
            tm_all = pd.read_sql_query("SELECT * FROM test_mapping", conn)  # fetch assigned test points (if exist)
        except Exception:
            tm_all = None  # ok if table isn't there yet

    train_targets = [c for c in training.columns if c != x_col]  # ['Y1'..'Y4']

    panels = []  # collect per-Y tab panels
    for idx, tcol in enumerate(train_targets, start=1):  # keep ideal numbering aligned
        icol = mapping[tcol]  # the chosen ideal for this training column
        tol = float(tolerances[str(idx)])  # tolerance for this ideal
        panels.append(
            _bokeh_single_panel(
                training=training,
                ideal=ideal,
                tm_all=tm_all,
                tcol=tcol,
                icol=icol,
                tol=tol,
                idx_for_this_panel=idx,  # pass ideal number (1..4)
                x_col=x_col,
            )
        )

    output_file(save_path, title="Training vs Ideal (Interactive)")  # set HTML output file
    tabs = Tabs(tabs=panels)  # wrap panels in tabs
    save(tabs)  # write HTML to disk
    if show_in_browser:
        show(tabs)  # open in default browser
    print(f"[Bokeh] Saved interactive tabs to: {save_path}")  # simple console note


# =========================
# 6) Main Orchestration
# =========================

def main() -> None:
    """
    Orchestrate the full flow:

    1) Load CSVs
    2) Create SQLite DB; write 'training' and 'ideal'
    3) Select four ideal functions; compute tolerances
    4) Stream test rows → assign → append 'test_mapping'
    5) (Optional) quick plots / Bokeh
    """
    # --- Edit these paths for your environment ---
    data_dir = Path(
        r"C:/Users/micha/OneDrive - itsgroupgy.com/Personal Development/"
        r"Ai text/ai AND SOCIETY/assignment"
    )  # folder where CSVs live
    training_path = data_dir / "training.csv"  # training CSV path
    ideal_path = data_dir / "ideal.csv"  # ideal CSV path
    test_path = data_dir / "test.csv"  # test CSV path

    sqlite_path = Path("assignment.db")  # output SQLite file in current folder

    # --- Load data ---
    training_df = TrainingLoader(training_path).load()  # validate + load training
    ideal_df = IdealLoader(ideal_path).load()  # validate + load ideal
    test_df = TestLoader(test_path).load()  # validate + load test

    # Normalize column names (strip spaces)
    for df in (training_df, ideal_df, test_df):
        df.columns = [str(c).strip() for c in df.columns]  # remove accidental spaces

    # --- SQLite: write base tables ---
    engine = make_engine(sqlite_path)  # create DB engine
    write_table(training_df, "training", engine)  # store training table
    write_table(ideal_df, "ideal", engine)  # store ideal table

    # --- Choose four ideal functions ---
    train_targets = [c for c in training_df.columns if c != "X"]  # ['Y1'..'Y4']
    if len(train_targets) != 4:  # safety check for assignment spec
        raise DataShapeMismatchError(
            f"Expected 4 training Y columns, found {len(train_targets)}: {train_targets}"
        )

    mapping = select_best_ideals(training_df, ideal_df, x_col="X")  # choose best ideal per training Y
    chosen_ideals = [mapping[t] for t in train_targets]  # keep order Y1..Y4

    # --- Tolerances (assignment rule) ---
    tolerances = compute_tolerances(training_df, ideal_df, mapping, x_col="X")  # per-ideal tolerances

    # --- Optional: quick plots (comment out if not desired) ---
    # quick_plot_all_training_vs_ideals(training_df, ideal_df, mapping, x_col="X")

    # --- Prepare lookup + assign test rows ---
    ideal_lookup = _prepare_ideal_lookup(ideal_df, chosen_ideals, x_col="X")  # small table: X + chosen ideals
    stream_and_store_test_results(
        test_df=test_df,
        ideal_lookup=ideal_lookup,
        chosen_ideals=chosen_ideals,
        tolerances=tolerances,
        engine=engine,
        x_col="X",
    )  # fills/extends the test_mapping table

    # --- Optional: Bokeh interactive tabs (comment out if not needed) ---
    # bokeh_plot_all_training_vs_ideals(
    #     engine=engine,
    #     mapping=mapping,
    #     tolerances=tolerances,
    #     x_col="X",
    #     save_path="bokeh_training_vs_ideals.html",
    #     show_in_browser=True,
    # )

    # --- Friendly summary (stdout only; no side-effects in library code) ---
    print("=== SUMMARY ===")
    print(f"SQLite file          : {sqlite_path.resolve()}")  # show full path
    print(f"Training table shape : {training_df.shape}")  # (rows, cols)
    print(f"Ideal table shape    : {ideal_df.shape}")
    print(f"Test rows processed  : {len(test_df)}")
    print("Chosen ideals (Y1..Y4 -> IdealFuncNo 1..4):")
    for idx, (t, icol) in enumerate(zip(train_targets, chosen_ideals), 1):  # show mapping in order
        print(f"  {t} -> {icol} (IdealFuncNo={idx})")
    print("Tolerances used (per IdealFuncNo):", tolerances)
    print("Created/overwritten tables: training, ideal, test_mapping")


# =========================
# 7) Script Entry Point
# =========================

if __name__ == "__main__":
    print("CWD:", os.getcwd())  # current working directory (helps debug paths)
    print("argv[0] dir:", os.path.dirname(sys.argv[0]))  # folder of the running script
    try:
        main()  # run the pipeline
    except DataShapeMismatchError as exc:
        print(f"[ERROR] Data validation failed: {exc}")  # clearer error for column/shape issues
    except AssignmentRuleError as exc:
        print(f"[ERROR] Compiling criterion not met: {exc}")  # no ideal within tolerance
    except FileNotFoundError as exc:
        print(f"[ERROR] Could not find file: {exc}")  # missing CSVs
    except Exception as exc:  # last resort catch (keep it visible for students)
        print(f"[ERROR] Unexpected issue: {exc}")
