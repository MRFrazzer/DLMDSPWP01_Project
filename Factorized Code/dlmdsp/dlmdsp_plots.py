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
    x_col: str = "X",                                                             # X column name
) -> None:                                                                         # side-effect: shows plots
    """Plot each training series with its selected ideal on a simple chart."""
    import matplotlib.pyplot as plt                                                # import locally to keep optional
    training_targets = [c for c in training_df.columns if c != x_col]              # list of training Ys
    for training_col in training_targets:                                          # plot each training Y
        ideal_col = best_map[training_col]                                         # find its chosen ideal
        merged = pd.merge(                                                         # align on X for plotting
            training_df[[x_col, training_col]],                                    # keep needed columns
            ideal_df[[x_col, ideal_col]],                                          # keep needed columns
            on=x_col,                                                              # join key
            how="inner",                                                          # keep common X only
            suffixes=("", "_ideal"),                                              # avoid name collision
        )                                                                          # end merge
        plt.figure()                                                                # new figure per pair
        plt.plot(merged[x_col], merged[training_col], label=training_col)          # plot training curve
        plt.plot(merged[x_col], merged[ideal_col], label=f"{ideal_col} (ideal)")  # plot ideal curve
        plt.title(f"{training_col} vs {ideal_col}")                               # set title
        plt.xlabel(x_col)                                                          # label x-axis
        plt.ylabel("Value")                                                        # label y-axis
        plt.legend()                                                               # show legend
        plt.tight_layout()                                                         # tidy layout
        plt.show()                                                                 # display plot
