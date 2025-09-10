# Unit Test - README

# How to run the unit tests


1. Terminal (Windows/macOS/Linux)

Open Anaconda Prompt, cmd/PowerShell, macOS Terminal, or VS Code Terminal.

cd into the project folder (app_api.py, dlmdsp/, and tests/).

	python -m pip install -U pytest pandas numpy sqlalchemy pytest-cov
    python -m pytest -q tests
	python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=term-missing tests
	python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=html tests
	# then open htmlcov/index.html



2. Jupyter Notebook 

Open a notebook from the project folder (or os.chdir(...) to it).

Run these in a cell:

	!python -m pip install -U pytest pandas numpy sqlalchemy pytest-cov
    !python -m pytest -q tests
	!python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=term-missing tests
	!python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=html tests


	View the HTML report at htmlcov/index.html (via the Jupyter file browser).

## Expected output:
PS C:\Users\micha\DLMDSP WP01\Factorized Code> python -m pip install -U pytest pandas numpy sqlalchemy pytest-cov
>>     python -m pytest -q tests
>>     python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=term-missing tests
>>     python -m pytest --cov=app_api --cov=Updated_Assignment_flow9 --cov-report=html tests
Requirement already satisfied: pytest in c:\users\micha\anaconda3\lib\site-packages (8.4.2)
Requirement already satisfied: pandas in c:\users\micha\anaconda3\lib\site-packages (2.3.2)
Requirement already satisfied: numpy in c:\users\micha\anaconda3\lib\site-packages (2.3.3)
Requirement already satisfied: sqlalchemy in c:\users\micha\anaconda3\lib\site-packages (2.0.43)
Requirement already satisfied: pytest-cov in c:\users\micha\anaconda3\lib\site-packages (7.0.0)
Requirement already satisfied: colorama>=0.4 in c:\users\micha\anaconda3\lib\site-packages (from pytest) (0.4.6)
Requirement already satisfied: iniconfig>=1 in c:\users\micha\anaconda3\lib\site-packages (from pytest) (1.1.1)
Requirement already satisfied: packaging>=20 in c:\users\micha\anaconda3\lib\site-packages (from pytest) (24.2)
Requirement already satisfied: pluggy<2,>=1.5 in c:\users\micha\anaconda3\lib\site-packages (from pytest) (1.5.0)
Requirement already satisfied: pygments>=2.7.2 in c:\users\micha\anaconda3\lib\site-packages (from pytest) (2.19.1)
Requirement already satisfied: python-dateutil>=2.8.2 in c:\users\micha\anaconda3\lib\site-packages (from pandas) (2.9.0.post0)
Requirement already satisfied: pytz>=2020.1 in c:\users\micha\anaconda3\lib\site-packages (from pandas) (2024.1)
Requirement already satisfied: tzdata>=2022.7 in c:\users\micha\anaconda3\lib\site-packages (from pandas) (2025.2)
Requirement already satisfied: greenlet>=1 in c:\users\micha\anaconda3\lib\site-packages (from sqlalchemy) (3.1.1)
Requirement already satisfied: typing-extensions>=4.6.0 in c:\users\micha\anaconda3\lib\site-packages (from sqlalchemy) (4.12.2)
Requirement already satisfied: coverage>=7.10.6 in c:\users\micha\anaconda3\lib\site-packages (from coverage[toml]>=7.10.6->pytest-cov) (7.10.6)
Requirement already satisfied: six>=1.5 in c:\users\micha\anaconda3\lib\site-packages (from python-dateutil>=2.8.2->pandas) (1.17.0)
.....                                                                                                               [100%]
5 passed in 0.37s
================================================== test session starts ===================================================
platform win32 -- Python 3.13.5, pytest-8.4.2, pluggy-1.5.0
rootdir: C:\Users\micha\DLMDSP WP01\Factorized Code
plugins: anyio-4.7.0, cov-7.0.0
collected 5 items                                                                                                         

tests\test_db_schema.py .                                                                                           [ 20%]
tests\test_loaders_error_path.py .                                                                                  [ 40%] 
tests\test_mapping_and_loaders.py ..                                                                                [ 80%]
tests\test_model_selection.py .C:\Users\micha\anaconda3\Lib\site-packages\coverage\inorout.py:521: CoverageWarning: Module Updated_Assignment_flow9 was never imported. (module-not-imported)
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
                                                                                     [100%]

===================================================== tests coverage ===================================================== 
____________________________________ coverage: platform win32, python 3.13.5-final-0 _____________________________________ 

Name         Stmts   Miss  Cover   Missing
------------------------------------------
app_api.py      29      4    86%   128-135
------------------------------------------
TOTAL           29      4    86%
=================================================== 5 passed in 0.61s ==================================================== 
================================================== test session starts ===================================================
platform win32 -- Python 3.13.5, pytest-8.4.2, pluggy-1.5.0
rootdir: C:\Users\micha\DLMDSP WP01\Factorized Code
plugins: anyio-4.7.0, cov-7.0.0
collected 5 items                                                                                                         

tests\test_db_schema.py .                                                                                           [ 20%]
tests\test_loaders_error_path.py .                                                                                  [ 40%] 
tests\test_mapping_and_loaders.py ..                                                                                [ 80%]
tests\test_model_selection.py .C:\Users\micha\anaconda3\Lib\site-packages\coverage\inorout.py:521: CoverageWarning: Module Updated_Assignment_flow9 was never imported. (module-not-imported)
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
                                                                                     [100%]

===================================================== tests coverage ===================================================== 
____________________________________ coverage: platform win32, python 3.13.5-final-0 _____________________________________ 

Coverage HTML written to dir htmlcov
=================================================== 5 passed in 0.62s ====================================================



### Project tree:


project-root/
├─ app_api.py
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
└─ tests/
   ├─ conftest.py
   ├─ test_db_schema.py
   ├─ test_loaders_error_path.py
   ├─ test_mapping_and_loaders.py
   └─ test_model_selection.py




### Requirements

	Python 3.10+ 

	pytest, pandas, numpy, pytest-cov

	Run from the project root so tests/ can import app_api. If running from elsewhere, ensure your tests/conftest.py adds the project root to sys.path (Code for this already included in conftest.py).