# Unit Test - README

# How to run the unit tests


1. Terminal (Windows/macOS/Linux)

Open Anaconda Prompt, cmd/PowerShell, macOS Terminal, or VS Code Terminal.

cd into the project folder (the one with app_api.py, Updated_Assignment_flow9.py, and tests/).

	python -m pip install -U pytest pandas numpy pytest-cov
	python -m pytest -q tests
	python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=term-missing tests
	python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=html tests
	# then open htmlcov/index.html



2. Jupyter Notebook 

Open a notebook from the project folder (or os.chdir(...) to it).

Run these in a cell:

	!python -m pip install -U pytest pandas numpy pytest-cov
	!python -m pytest -q tests
	!python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=term-missing tests
	!python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=html tests


	View the HTML report at htmlcov/index.html (via the Jupyter file browser).

## Expected output:
Requirement already satisfied: pytest-cov in c:\users\micha\anaconda3\lib\site-packages (6.3.0)
Requirement already satisfied: pytest>=6.2.5 in c:\users\micha\anaconda3\lib\site-packages (from pytest-cov) (8.3.4)
Requirement already satisfied: coverage>=7.5 in c:\users\micha\anaconda3\lib\site-packages (from coverage[toml]>=7.5->pytest-cov) (7.10.6)
Requirement already satisfied: pluggy>=1.2 in c:\users\micha\anaconda3\lib\site-packages (from pytest-cov) (1.5.0)
Requirement already satisfied: colorama in c:\users\micha\anaconda3\lib\site-packages (from pytest>=6.2.5->pytest-cov) (0.4.6)
Requirement already satisfied: iniconfig in c:\users\micha\anaconda3\lib\site-packages (from pytest>=6.2.5->pytest-cov) (1.1.1)
Requirement already satisfied: packaging in c:\users\micha\anaconda3\lib\site-packages (from pytest>=6.2.5->pytest-cov) (24.2)
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\micha
plugins: anyio-4.7.0, cov-6.3.0
collected 5 items

tests\test_db_schema.py .                                                [ 20%]
tests\test_loaders_error_path.py .                                       [ 40%]
tests\test_mapping_and_loaders.py ..                                     [ 80%]
tests\test_model_selection.py .                                          [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
Updated_Assignment_flow9.py     251    151    40%   88, 103, 132, 143-145, 148-150, 153-155, 171, 178, 329, 349-367, 384-404, 424-572, 589-625, 647-742
app_api.py                       26      4    85%   48-51
-----------------------------------------------------------
TOTAL                           277    155    44%
============================== 5 passed in 0.74s ==============================
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\micha
plugins: anyio-4.7.0, cov-6.3.0
collected 5 items

tests\test_db_schema.py .                                                [ 20%]
tests\test_loaders_error_path.py .                                       [ 40%]
tests\test_mapping_and_loaders.py ..                                     [ 80%]
tests\test_model_selection.py .                                          [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Coverage HTML written to dir htmlcov
============================== 5 passed in 0.74s ==============================
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\micha
plugins: anyio-4.7.0, cov-6.3.0
collected 5 items

tests\test_db_schema.py .                                                [ 20%]
tests\test_loaders_error_path.py .                                       [ 40%]
tests\test_mapping_and_loaders.py ..                                     [ 80%]
tests\test_model_selection.py .                                          [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
Updated_Assignment_flow9.py     251    151    40%   88, 103, 132, 143-145, 148-150, 153-155, 171, 178, 329, 349-367, 384-404, 424-572, 589-625, 647-742
app_api.py                       26      4    85%   48-51
-----------------------------------------------------------
TOTAL                           277    155    44%
============================== 5 passed in 0.68s ==============================
Selection deleted




### Project tree:

├─ Updated_Assignment_flow9.py
├─ app_api.py
└─ tests/
   ├─ conftest.py
   ├─ test_model_selection.py
   └─ test_mapping_and_loaders.py


### Requirements

	Python 3.10+ 

	pytest, pandas, numpy, pytest-cov

	Run from the project root so tests/ can import app_api. If running from elsewhere, ensure your tests/conftest.py adds the project root to sys.path (Code for this already included in conftest.py).