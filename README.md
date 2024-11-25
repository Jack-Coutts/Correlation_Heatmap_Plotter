# Correlation Heatmap Plotter

This program uses [scipy's pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) function to calculate the Pearson correlation coefficient and the corresponding p vales to quantify the correlation between the features in two excel spreadsheets. These correlation coefficients and p values are then used to generate a correlation heatmap with [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/). 

## User Instructions

### Downloading the Program

### Input Data

This program works with two single-sheet excel files which both have an identical first column. This first columns should be observations/samples/individuals where each row represents measurements from a single individual/observation/sample. The remaining columns can be the measured features of that individual/observation/sample. 

Take the two spreasheets containing fake data below as examples:

Spreadsheet1.xlsx

| People | Age | Height | Weight | Arm Length |
| John | 45 | 174 | 75 | 70 |
| Jane | 13 | 130 | 50 | 50 |
| Fred | 25 | 184 | 88 | 78 |
| Joe | 37 | 200 | 100 | 99 |
| Sarah | 65 | 155 | 68 | 40 |
| Holly | 6 | 98 | 42 | 41 |

Spreadsheet2.xlsx

| People | Vitamin C | Vitamin D | Vitamin E | Vitamin K |
| John | 145 | 154 | 295 | 332 |
| Jane | 131 | 1430 | 540 | 350 |
| Fred | 253 | 1834 | 488 | 748 |
| Joe | 67 | 240 | 1500 | 499 |
| Sarah | 655 | 155 | 645 | 440 |
| Holly | 345 | 198 | 200 | 471 |

There are three different heatmaps that can be produced using these two spreadsheets:

1. How vitamins are correlated with each other by entering spreadsheet2 as both of the input spreadsheets.
2. How the metadata (age, height, etc) are correlated with each other by entering spreadsheet1 as both of the input spreadsheets.
3. How the vitamin levels correlate with the metadata but entering spreadsheet1 as the first dataset and spreadhseet2 as the second (or the other way around). 

It is essential that the first column is always identical accross both of the spreadsheets.



### Running the Program


### Outputs



## Developer Instructions

### Dependencies

* [Poetry](https://python-poetry.org/) (Dependency management)
* [Python (3.12-3.14)](https://www.python.org/downloads/)
* [pandas](https://pandas.pydata.org/)
* [matplotlib](https://matplotlib.org/)
* [SciPy](https://scipy.org/)
* [seaborn](https://seaborn.pydata.org/)
* [openpyxl](https://openpyxl.readthedocs.io/en/stable/)
* [PyInstaller](https://pyinstaller.org/en/stable/) 


### Directory Structure

* `corr_plot/main.py` is the file containing all of the code for the program.
* `pyproject.toml` is the configuration file used by poetry.
* `poetry.lock` controls dependency versions.
* `dist/corr_plot_mac_exe` the executable file for Mac.
* `dist/corr_plot_windows_exe` the executable Windows.

### Development Instructions

* After the project has been git cloned, run `poetry install` to install the relevant dependencies from the `pyproject.toml`.
* To add a dependency, run `poetry add <dependency>`.
* To run the script via the poetry virtual environment, run `poetry run plot` as specified in the `pyproject.toml`.
* To create a new executable, run `poetry run pyinstaller --onefile csv_writer/main.py`. This pyinstaller command will also produce other artifacts: the `build/` directory and `main.spec` file. I do not need these so I delete them.
* NOTE: All file paths are relative.



