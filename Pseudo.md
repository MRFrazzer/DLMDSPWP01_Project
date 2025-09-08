DLMDSP WP01 — Pseudocode 

Purpose:
Load training/ideal/test CSVs → select best ideal functions for each training column → compute tolerances (√2 × max residual) → assign each test row to one of four chosen ideals if within tolerance → store results in SQLite tables → plot.

Tables:
training(X, Y1, Y2, Y3, Y4)
ideal(X, Y1..Y50)
test_mapping(X, Y, DeltaY, IdealFuncNo)

1) Custom Exceptions

    - DLMDSPError: base error for module.

    - DataShapeMismatchError: raised if CSV columns don’t match spec.

    - AssignmentRuleError: raised if a test row cannot be assigned within tolerance.

2) CSV Loaders
    > CLASS BaseCSVLoader(path, x_col='X')

    + METHOD load() → DataFrame

        - Read CSV from path.

        - If x_col not in columns → raise DataShapeMismatchError.

        - Return DataFrame.

    > CLASS TrainingLoader(BaseCSVLoader)

    + METHOD load() → DataFrame

        - df ← super().load()

        - y_cols ← all columns except X

        - If len(y_cols) != 4 → raise DataShapeMismatchError.

        - Return df.

    > CLASS IdealLoader(BaseCSVLoader)

    + METHOD load() → DataFrame

        - df ← super().load()

        - y_cols ← all columns except X

        - If len(y_cols) != 50 → raise DataShapeMismatchError.

        - Return df.

    > CLASS TestLoader(BaseCSVLoader)

    + METHOD load() → DataFrame

        - df ← super().load()

        - If "Y" not in columns → raise DataShapeMismatchError.

        - Return df.

    > Convenience wrappers

    - load_training_data(path) → TrainingLoader(path).load()

    - load_ideals(path) → IdealLoader(path).load()

    - load_test_data(path) → TestLoader(path).load()

3) SQLite Helpers
    + make_engine(sqlite_path) → Engine

        - Create and return SQLAlchemy engine for sqlite_path.

    + write_table(df, table, engine) → None

        - Write df to table in SQLite using if_exists='replace'.

4) Model Selection + Tolerances
    + Helper rmse(a, b) → float

        - Compute root-mean-square error between aligned numeric series.

            select_best_ideals(training, ideal, x_col='X') → dict{training_Yk: ideal_Yj}

    + Goal: For each training column Y1..Y4, pick the ideal Yj with minimum RMSE.
      Steps:

        1. merged ← inner-join(training, ideal) on X (handles same X grid).

        2. train_targets ← [Y1, Y2, Y3, Y4]

        3. ideal_targets ← [Y1..Y50]

    4. For each tcol in train_targets:

        - best_col ← None, best_score ← +∞

        + For each icol in ideal_targets:

            - Resolve column name in merged (icol vs icol+'_ideal' if collision).

            - score ← rmse(merged[tcol], merged[icol_in_merged])

            - If score < best_score: update best_score and best_col

        - If best_col is None → raise DLMDSPError

        - Record mapping tcol → best_col

    5. Return mapping (e.g., {'Y1':'Y17', 'Y2':'Y8', 'Y3':'Y22', 'Y4':'Y41'})

        > compute_tolerances(training, ideal, mapping, x_col='X', scale=√2) → dict{'1':float,...,'4':float}

        + Goal: For each chosen ideal, compute tolerance = scale * max_abs(trainingYk - idealYj) on training set.
            Steps:

                1. merged ← inner-join(training, ideal) on X

                2. train_targets ← [Y1, Y2, Y3, Y4]

                3. For idx, (tcol, icol) in mapping (preserve order 1..4):

                    - Resolve icol_in_merged (handle name collision).

                    - max_abs ← max | merged[tcol] - merged[icol_in_merged] |

                    - tolerances[str(idx)] ← float(scale * max_abs)

                4. Return tolerances dict keyed '1'..'4'.

5) Test Assignment + Persistence
    + _prepare_ideal_lookup(ideal, chosen_ideals, x_col='X') → DataFrame

        - Return a small DataFrame with columns [X] + chosen_ideals (the 4 selected ideal curves).

    + assign_test_row(x, y, ideal_lookup, chosen_ideals, tolerances, x_col='X') → (IdealFuncNo:str, DeltaY:float)

        + Goal: Assign one test point (x, y) to the closest of the four chosen ideals if within that ideal’s tolerance.
        Steps:

            1. Try exact X match: row ← ideal_lookup where X == x.

            2. If empty: pick nearest X by minimal |X - x|.

            3. Convert row to Series for easy access.

            4. For each ideal index k=1..4 and its column name in chosen_ideals:

                - dy_k ← | y - row[ideal_k_at_x] |

                - Append (k_as_str, dy_k) to list deviations.

            5. Sort deviations by dy ascending.

            6. For each (k, dy) in sorted deviations:

                - If dy ≤ tolerances[k] → return (k, dy) (first that passes).

            7. If none passed → raise AssignmentRuleError.

    + stream_and_store_test_results(test_df, ideal_lookup, chosen_ideals, tolerances, engine, x_col='X') → None

    + Goal: Process all test rows, assign each to an ideal if possible, write results to test_mapping.
    Steps:

        1. Initialize out_rows ← [].

        2. Loop over each row r in test_df:

            - (k, dy) ← assign_test_row(x=r[X], y=r[Y], ...)

            - Append dict {X, Y, DeltaY=dy, IdealFuncNo=int(k)} to out_rows.

        3. Convert out_rows to DataFrame.

        4. Append to SQLite table test_mapping (if_exists='append').

6) Graph Plotting
    > quick_plot_all_training_vs_ideals(training, ideal, mapping, x_col='X') → None

        + For each Yk:

            - Join training Yk with chosen ideal curve on X.

            - Plot lines (training vs ideal).

            - Show figure.

    > bokeh_plot_all_training_vs_ideals(engine, mapping, tolerances, x_col='X', save_path, show_in_browser=True) → None

        - Read training, ideal, and test_mapping (if present) from SQLite.

        + For each Yk/ideal pair:

            + Build a tab with:

                - Ideal band ± tolerance.

                - Training vs ideal lines.

                - Test points accepted for this ideal.

                - Points rejected for this ideal (|Y − ideal| > tol).

                - Residual line plot and simple coverage summary.

        - Save as HTML and (optionally) open in browser.

7) Main Orchestration
    > main() → None

    + Inputs (paths):

        - data_dir (folder containing training.csv, ideal.csv, test.csv)

        - sqlite_path = "assignment.db"

    Steps:

        1. Resolve file paths: training_path, ideal_path, test_path.

        2. Load data:

            - training_df ← TrainingLoader(training_path).load()

            - ideal_df ← IdealLoader(ideal_path).load()

            - test_df ← TestLoader(test_path).load()

        3. Normalize headers: strip spaces from all column names.

        4. Create engine: engine ← make_engine(sqlite_path).

        5. Persist base tables:

            - write_table(training_df, 'training', engine)

            - write_table(ideal_df, 'ideal', engine)

        6. Validate training shape: expect exactly 4 Y columns.

        7. mapping ← select_best_ideals(training_df, ideal_df)

        8. chosen_ideals ← [mapping['Y1'], mapping['Y2'], mapping['Y3'], mapping['Y4']]

        9. tolerances ← compute_tolerances(training_df, ideal_df, mapping)

        10. Build ideal lookup: ideal_lookup ← _prepare_ideal_lookup(ideal_df, chosen_ideals)

        11. Assign and store tests:

            - stream_and_store_test_results(test_df, ideal_lookup, chosen_ideals, tolerances, engine)

        12. plots:

            - quick_plot_all_training_vs_ideals(...) or

            - bokeh_plot_all_training_vs_ideals(...)

        13. Print a short text summary (paths, shapes, chosen ideals, tolerances).

            > Script entry (if __name__ == "__main__":)

                - Print debugging info (CWD and script folder).

                + Run main() inside try/except:

                    + Catch and print friendly messages for:

                        - DataShapeMismatchError

                        - AssignmentRuleError

                        - FileNotFoundError

                        - Any unexpected Exception


Data Expectations & Rules 

    - Training CSV: columns exactly X, Y1, Y2, Y3, Y4.

    - Ideal CSV: columns exactly X, Y1..Y50.

    - Test CSV: columns exactly X, Y.

    - Selection rule: for each Yk, pick Yj (from ideals) with lowest RMSE on common X.

    - Tolerance per ideal k: tol_k = √2 × max |Yk_train − Yj_ideal| (measured on training).

    + Assignment rule for a test point (x, y):

        1. Evaluate y against the four chosen ideals at x (exact or nearest X).

        2. Compute absolute deviations; sort ascending.

        3. Accept the first ideal whose deviation ≤ its tol_k.

        4. If none qualifies → unassignable (error raised in strict mode).

    - Persistence: All base and result tables are written to SQLite for traceability.