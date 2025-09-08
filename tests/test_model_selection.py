#tests/test_model_selection.py (1 small test)

from app_api import select_best_ideals

def test_select_best_ideals_includes_exact_match(tiny_training_df, tiny_ideals_df):
    mapping = select_best_ideals(tiny_training_df, tiny_ideals_df, x_col="X")
    assert isinstance(mapping, dict) and len(mapping) == 4
    assert mapping["Y1"] == "Y1"  # exact match should be chosen
    for icol in mapping.values():
        assert icol in tiny_ideals_df.columns
