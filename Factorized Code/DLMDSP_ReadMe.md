DLMDSP — How to Run

This project reads three CSVs (training.csv, ideal.csv, test.csv), writes them to SQLite, picks the best ideal functions for Y1..Y4, computes tolerances, assigns test points, and (optionally) shows:

    - a quick Matplotlib preview (one window with four panels), then

    - an interactive Bokeh dashboard in your browser.

Folder layout
<project-root>/
├─ dlmdsp/
│  ├─ __init__.py
│  ├─ dlmdsp_init.py
│  ├─ dlmdsp_exceptions.py
│  ├─ dlmdsp_loaders.py
│  ├─ dlmdsp_database.py
│  ├─ dlmdsp_model_selection.py
│  ├─ dlmdsp_mapping.py
│  ├─ dlmdsp_plots.py
│  └─ dlmdsp_viz_bokeh.py
└─ (other files, tests, etc.)

Requirements

    - Python 3.10+
    - Packages: pandas,   
      sqlalchemy, matplotlib, bokeh

If you like virtual envs:

    - py -m venv .venv
    - .\.venv\Scripts\Activate.ps1
    - # If PowerShell blocks activation:
    - # Set-ExecutionPolicy -Scope Process - -ExecutionPolicy Bypass
    - pip install --upgrade pip
    - pip install pandas sqlalchemy - matplotlib bokeh


Mac/Linux:

    - python3 -m venv .venv
    - source .venv/bin/activate
    - pip install --upgrade pip
    - pip install pandas sqlalchemy   - matplotlib bokeh

Point to your data

Open dlmdsp/dlmdsp_cli.py and set data_dir to the folder that contains training.csv, ideal.csv, and test.csv:

    data_dir = Path(r"C:/path/to/your/folder")

Running it (starting from the dlmdsp directory)

    1. Open a terminal in dlmdsp/.

    2. Go up one level to the project root (the command must run from the folder that contains dlmdsp):

    cd ..


    3. Run the pipeline:

        - py -m dlmdsp.dlmdsp_cli


    Mac/Linux:

        - python3 -m dlmdsp.dlmdsp_cli

What you’ll see

    - A Matplotlib window with 4 subplots opens first.

    - When you close that window, the script continues and opens the Bokeh dashboard in your default browser (also saved as bokeh_training_vs_ideals.html).

    - If you don’t want plots, just leave the plotting imports/calls commented out in dlmdsp_cli.py.

Output files

    - assignment.db (SQLite) with tables: - training, ideal, test_mapping

    - bokeh_training_vs_ideals.html (if Bokeh is enabled)

Troubleshooting

    + “No module named 'dlmdsp'”
        - You’re probably still inside dlmdsp/. Go up to the project root: cd .. and run the module again.

    + Missing packages
        - Install them with: pip install pandas sqlalchemy matplotlib bokeh.

    + Paths with spaces (Windows)
        - Quote them in the terminal, e.g. cd "C:\Users\you\My Project\dlmdsp".