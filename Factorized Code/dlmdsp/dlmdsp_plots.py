# ──────────────────────────────────────────────────────────────────────────────
# dlmdsp_plots.py                                                                 # module: quick Matplotlib plots
# ──────────────────────────────────────────────────────────────────────────────
"""Quick Matplotlib preview of training curves vs their chosen ideals.

This is a fast visual check before using the richer Bokeh view.
"""

from __future__ import annotations                                                # modern typing
from typing import Dict                                                            # explicit type for mapping
import pandas as pd                                                                # data handling

def quick_plot_training_vs_ideals(                                                # simple preview plots
    training_df: pd.DataFrame,                                                     # training data
    ideal_df: pd.DataFrame,                                                        # ideal data
    best_map: Dict[str, str],                                                      # mapping training→ideal
    x_col: str = "X",                                                              # X column name
) -> None:                                                                         # side-effect: shows plots
    """Plot the four training series vs their chosen ideals in a single 2×2 figure."""
    import matplotlib.pyplot as plt                                                # import locally to keep optional

    training_targets = [c for c in training_df.columns if c != x_col]              # list of training Ys (Y1..Y4)
    rows, cols = 2, 2                                                              # 2×2 layout
    fig, axes = plt.subplots(rows, cols, figsize=(12, 8), squeeze=False)           # create grid of subplots

    for idx, training_col in enumerate(training_targets):                           # fill each panel
        ideal_col = best_map[training_col]                                         # chosen ideal for this Y
        merged = pd.merge(                                                         # align on X for plotting
            training_df[[x_col, training_col]],
            ideal_df[[x_col, ideal_col]],
            on=x_col, how="inner", suffixes=("", "_ideal"),
        )
        ax = axes[idx // cols][idx % cols]                                         # pick subplot cell
        ax.plot(merged[x_col], merged[training_col], label=training_col)           # training curve
        ax.plot(merged[x_col], merged[ideal_col], label=f"{ideal_col} (ideal)")    # ideal curve
        ax.set_title(f"{training_col} vs {ideal_col}")                             # panel title
        ax.set_xlabel(x_col)                                                       # x-axis label
        ax.set_ylabel("Value")                                                     # y-axis label
        ax.legend()                                                                # legend

    fig.tight_layout()                                                             # tidy layout for all panels
    plt.show()                                                                     # show one window with 4 charts
