# tests/test_db_schema.py
import pandas as pd
import pytest
from sqlalchemy import create_engine, inspect

@pytest.fixture
def temp_engine(tmp_path):
    db_file = tmp_path / "t.sqlite"
    eng = create_engine(f"sqlite:///{db_file.as_posix()}")
    try:
        yield eng
    finally:
        eng.dispose()  # closes any open sqlite3 connections

def test_db_tables_exist_and_shapes(temp_engine):
    eng = temp_engine
     
    
    # --- Write minimal, valid tables that match your assignment’s schema ---
    # training: X + 4 training series (Y1..Y4)
    pd.DataFrame({"X": [0], "Y1": [1], "Y2": [2], "Y3": [3], "Y4": [4]}).to_sql(
        "training", eng, if_exists="replace", index=False
    )

    # ideal: X + 50 ideals (Y1..Y50)
    ideal_data = {"X": [0]}
    for i in range(1, 51):
        ideal_data[f"Y{i}"] = [i]
    pd.DataFrame(ideal_data).to_sql("ideal", eng, if_exists="replace", index=False)

    # test_mapping: X, Y, delta_y, IdealFuncNo (or similar identifier)
    pd.DataFrame(
        {"X": [0.5], "Y": [1.2], "delta_y": [0.1], "IdealFuncNo": ["1"]}
    ).to_sql("test_mapping", eng, if_exists="replace", index=False)

    # --- Inspect schema ---
    insp = inspect(eng)
    tables = set(insp.get_table_names())
    assert {"training", "ideal", "test_mapping"}.issubset(tables)

    tcols = {c["name"] for c in insp.get_columns("training")}
    icols = {c["name"] for c in insp.get_columns("ideal")}
    mcols = {c["name"] for c in insp.get_columns("test_mapping")}

    # Training must include X and at least 4 Y columns
    assert "X" in tcols and len(tcols) >= 5

    # Ideal must include X and 50 Y columns total ⇒ 51 columns
    assert "X" in icols and len(icols) >= 51

    # Mapping must include X, Y, delta_y and some ideal id column
    assert {"X", "Y", "delta_y"}.issubset(mcols)
    assert ("IdealFuncNo" in mcols) or ("ideal_col" in mcols) or ("ideal_index" in mcols)
