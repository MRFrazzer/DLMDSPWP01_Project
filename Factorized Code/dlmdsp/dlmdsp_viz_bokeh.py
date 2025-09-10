# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_viz_bokeh.py                                                             # module: interactive Bokeh
# ──────────────────────────────────────────────────────────────────────────────
"""Interactive Bokeh tabs with tolerance bands, accepted points, and residuals.

For each training/ideal pair, I show:
- training and ideal curves
- a ±tolerance band
- accepted test points with hover details
- a residual chart
"""

from __future__ import annotations                                                # modern typing
from typing import Dict, Optional, List                                            # explicit types
import pandas as pd                                                                # data handling
from sqlalchemy.engine import Engine                                               # engine type


def _make_single_bokeh_panel(                                                     # build one tab panel
    training_df: pd.DataFrame,                                                     # training table
    ideal_df: pd.DataFrame,                                                        # ideal table
    test_mapping_df: Optional[pd.DataFrame],                                       # test mapping (may be None)
    training_col: str,                                                             # name of training Y column
    ideal_col: str,                                                                # name of chosen ideal column
    tolerance: float,                                                              # tolerance value for panel
    ideal_number_for_panel: int,                                                   # ideal number (1..4)
    x_col: str = "X",                                                             # X column name
):                                                                                 # returns TabPanel
    """Build a single tab showing the curves, tolerance band, and residuals."""
    from bokeh.models import ColumnDataSource, HoverTool, Band, TabPanel, Div      # Bokeh components
    from bokeh.plotting import figure                                              # figure factory
    from bokeh.layouts import column                                               # vertical layout

    merged = pd.merge(                                                             # align training and ideal
        training_df[[x_col, training_col]],                                        # slice training columns
        ideal_df[[x_col, ideal_col]],                                              # slice ideal columns
        on=x_col,                                                                  # join on X
        how="inner",                                                              # inner join
        suffixes=("", "_ideal"),                                                  # avoid collision
    ).rename(columns={ideal_col: "ideal_y", training_col: "train_y", x_col: "x"})  # unify names for plotting

    merged["upper"] = merged["ideal_y"] + tolerance                               # top of tolerance band
    merged["lower"] = merged["ideal_y"] - tolerance                               # bottom of tolerance band
    source = ColumnDataSource(merged)                                              # wrap for Bokeh

    p = figure(width=840, height=420, title=f"{training_col} vs {ideal_col} (tolerance ±{tolerance:.4g})", tools="pan,wheel_zoom,box_zoom,reset,save", active_scroll="wheel_zoom")  # main chart
    band = Band(base="x", lower="lower", upper="upper", source=source, level="underlay", fill_alpha=0.15, line_alpha=0.0)  # shaded band
    p.add_layout(band)                                                             # add band behind lines
    train_line = p.line("x", "train_y", source=source, line_width=2, legend_label=training_col)  # training line
    ideal_line = p.line("x", "ideal_y", source=source, line_width=2, line_dash="dashed", legend_label=f"{ideal_col} (ideal)")  # ideal line

    accepted_src = None                                                            # holder for accepted points
    rejected_src = None                                                            # holder for rejected markers
    accepted_count = 0                                                             # counter for accepted points
    total_count = 0                                                                # counter for total test points

    if test_mapping_df is not None and not test_mapping_df.empty:                  # only if mapping exists
        total_count = len(test_mapping_df)                                         # set total count
        accepted = test_mapping_df.loc[test_mapping_df["IdealFuncNo"] == ideal_number_for_panel, ["X", "Y", "DeltaY", "IdealFuncNo"]].copy()  # filter accepted
        accepted_count = len(accepted)                                             # count accepted
        if accepted_count > 0:                                                     # if any accepted
            accepted.rename(columns={"X": "x"}, inplace=True)                    # rename X→x for plotting
            from bokeh.models import ColumnDataSource as CDS                        # alias to avoid shadowing
            accepted_src = CDS(accepted)                                           # wrap accepted
            points = p.scatter("x", "Y", size=6, alpha=0.9, source=accepted_src, legend_label="test points")  # draw points
            p.add_tools(HoverTool(renderers=[points], tooltips=[("X", "@x{0.#####}"), ("Y (test)", "@Y{0.#####}"), ("ΔY", "@DeltaY{0.#####}"), ("Ideal#", "@IdealFuncNo")]))  # hover tool

        ideal_curve = ideal_df[[x_col, ideal_col]].rename(columns={x_col: "x", ideal_col: "ideal_y"})  # ideal series
        all_points = test_mapping_df[["X", "Y", "DeltaY", "IdealFuncNo"]].rename(columns={"X": "x"}).copy()  # all test points
        joined = pd.merge(all_points, ideal_curve, on="x", how="left")           # attach ideal y at each x
        joined["delta_here"] = (joined["Y"] - joined["ideal_y"]).abs()          # deviation vs this ideal
        rejected = joined.loc[joined["delta_here"] > tolerance, ["x", "Y", "delta_here", "IdealFuncNo"]].copy()  # out-of-band

        if not rejected.empty:                                                     # draw rejected markers
            from bokeh.models import ColumnDataSource as CDS                        # alias for source
            rejected_src = CDS(rejected)                                           # wrap rejected points
            rej_points = p.scatter("x", "Y", size=8, marker="x", line_width=2, line_alpha=0.9, fill_alpha=0.0, line_color="red", source=rejected_src, legend_label="rejected (this ideal)")  # X markers
            p.add_tools(HoverTool(renderers=[rej_points], tooltips=[("X", "@x{0.#####}"), ("Y (test)", "@Y{0.#####}"), ("ΔY (this ideal)", "@delta_here{0.#####}"), ("Assigned Ideal#", "@IdealFuncNo"), ("Status", "rejected")]))  # hover

    from bokeh.models import HoverTool                                             # import hover tool
    p.add_tools(HoverTool(renderers=[train_line, ideal_line], tooltips=[("X", "@x{0.#####}"), ("Training", "@train_y{0.#####}"), ("Ideal", "@ideal_y{0.#####}")]))  # line hovers
    p.legend.location = "top_left"                                                # place legend
    p.legend.click_policy = "hide"                                                # allow toggling

    r = figure(width=840, height=260, title=f"Residuals (ΔY) — {training_col}/{ideal_col}", x_axis_label="X", y_axis_label="ΔY", tools="pan,wheel_zoom,box_zoom,reset,save", active_scroll="wheel_zoom")  # residual chart
    r.line("x", "train_y", source=source, alpha=0.0)                              # invisible line to sync hover
    residual_series = merged["train_y"] - merged["ideal_y"]                        # compute residuals
    from bokeh.models import ColumnDataSource as CDS                                # alias CDS
    residual_source = CDS({"x": merged["x"], "res": residual_series})            # wrap residuals
    r.line("x", "res", source=residual_source, line_width=2, legend_label="training residual (Yk - ideal)")  # draw residual line

    if accepted_src is not None:                                                   # if accepted points exist
        r.scatter("x", "DeltaY", source=accepted_src, size=6, alpha=0.9, legend_label="test ΔY (accepted)")  # plot ΔY
        r.add_tools(HoverTool(tooltips=[("X", "@x{0.#####}"), ("ΔY", "@DeltaY{0.#####}")]))  # hover tool
    r.legend.location = "top_left"                                                # legend position
    r.legend.click_policy = "hide"                                                # toggle visibility

    from bokeh.models import Div                                                   # HTML widget
    from bokeh.layouts import column                                               # layout helper
    coverage = 100.0 * accepted_count / total_count if total_count else 0.0        # compute simple coverage
    stats = Div(text=f"<b>Coverage for {ideal_col}: accepted {accepted_count} / total {total_count} ({coverage:.1f}%)</b>")  # coverage text
    return TabPanel(child=column(p, r, stats), title=training_col)                 # return assembled panel


def save_bokeh_training_vs_ideals(                                                # save interactive HTML
    engine: Engine,                                                                # DB engine
    best_map: Dict[str, str],                                                      # mapping training→ideal
    tolerances: Dict[str, float],                                                  # per-ideal tolerances
    x_col: str = "X",                                                             # X column name
    save_path: str = "bokeh_training_vs_ideals.html",                             # output HTML path
    open_in_browser: bool = True,                                                  # whether to open after saving
) -> None:                                                                         # no return; writes file
    """Save an interactive HTML dashboard with one tab per training/ideal pair."""
    from bokeh.io import output_file, save, show                                   # file IO helpers
    from bokeh.models import Tabs                                                  # tabs container

    with engine.connect() as conn:                                                 # single DB connection
        training_df = pd.read_sql_query("SELECT * FROM training", conn)           # read training table
        ideal_df = pd.read_sql_query("SELECT * FROM ideal", conn)                 # read ideal table
        try:                                                                        # test mapping may not exist
            mapping_df = pd.read_sql_query("SELECT * FROM test_mapping", conn)    # read mapping table
        except Exception:                                                           # if missing or error
            mapping_df = None                                                       # fine to proceed without it

    training_targets = [c for c in training_df.columns if c != x_col]              # list training Ys
    panels: List = []                                                               # container for TabPanels
    for ideal_number, training_col in enumerate(training_targets, start=1):        # iterate Y1..Y4 with numbers
        ideal_col = best_map[training_col]                                         # chosen ideal for this training
        tolerance = float(tolerances[str(ideal_number)])                           # tolerance value for this ideal
        panels.append(                                                             # build and collect panel
            _make_single_bokeh_panel(                                              # call panel builder
                training_df=training_df,                                           # pass training DF
                ideal_df=ideal_df,                                                 # pass ideal DF
                test_mapping_df=mapping_df,                                        # pass mapping DF (or None)
                training_col=training_col,                                         # training column name
                ideal_col=ideal_col,                                               # ideal column name
                tolerance=tolerance,                                               # tolerance for band
                ideal_number_for_panel=ideal_number,                                # 1..4 identifier
                x_col=x_col,                                                       # X column name
            )                                                                      # end call
        )                                                                          # end append

    output_file(save_path, title="Training vs Ideal (Interactive)")               # configure output file
    tabs = Tabs(tabs=panels)                                                       # pack panels into Tabs
    save(tabs)                                                                     # write HTML to disk
    if open_in_browser:                                                            # optionally open in browser
        show(tabs)                                                                 # open the file
    print(f"[Bokeh] Saved interactive tabs to: {save_path}")                       # console confirmation
