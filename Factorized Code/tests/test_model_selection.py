# tests/test_model_selection.py
"""
Simple sanity check for the model-selection step.

We build a tiny synthetic training/ideal pair (from fixtures) and ensure that
`select_best_ideals` chooses the exact match for Y1 when it exists.
"""

from app_api import select_best_ideals  # thin shim → dlmdsp.choose_best_ideal_columns


def test_select_best_ideals_includes_exact_match(tiny_training_df, tiny_ideals_df):
    """If an ideal column matches a training column exactly, it should be selected."""
    mapping = select_best_ideals(tiny_training_df, tiny_ideals_df, x_col="X")  # {"Y1":"Y1", ...}
    assert isinstance(mapping, dict) and len(mapping) == 4                      # expect 4 training targets
    assert mapping["Y1"] == "Y1"                                                # exact match should be chosen
    for icol in mapping.values():                                               # every chosen ideal must exist
        assert icol in tiny_ideals_df.columns
