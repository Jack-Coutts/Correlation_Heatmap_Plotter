# Correlation Heatmap Plotter

This [Python](https://www.python.org/) program uses the [pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) function from [SciPy](https://scipy.org/) to calculate the Pearson correlation coefficients and corresponding p values to describe the correlation between two sets of features. There is also the option to do [false discovery control](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html) with the Benjamini-Hochberg procedure to generate q values from the aforementioned p values. These values are then used to generate a Correlation Heatmap with [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/).

# User Instructions

### Downloading the Program

* On Mac click [this](https://github.com/Jack-Coutts/Correlation_Heatmap_plotter/releases/download/v1.1.0/corr_plot_mac_exe) link to download the executable file.

* On Windows click [this](https://github.com/Jack-Coutts/Correlation_Heatmap_plotter/releases/download/v1.1.0/corr_plot_windows.exe) link to download the executable file.

NOTE: Both of these files can also be found in the GitHub release or in the `dist/` directory in this repository.

**IMPORTANT: It is recommended that you save this file in a folder that also contains your input data files (which are described below).**

### Input Data

This program works with two CSV or single-sheet Excel files (`.csv`, `.xlsx`, or `.xlsm`). The first column in each file must contain unique, non-missing sample identifiers. Both files must contain the same identifiers, but they do not need to be in the same row order because the program aligns rows by identifier.

All measurement columns must be numeric. Entirely categorical columns (such as `group`) are reported and excluded. Mixed numeric/text columns are rejected instead of being silently corrupted. Left-censored values such as `<2.25` require an explicit handling choice based on the assay's pre-specified analysis plan.

Take the two dummy spreadsheets below as examples:

Spreadsheet1.xlsx

| People | Age | Height | Weight | Arm Length |
| ----- | ----- | ----- | ----- | ----- |
| John | 45 | 174 | 75 | 70 |
| Jane | 13 | 130 | 50 | 50 |
| Fred | 25 | 184 | 88 | 78 |
| Joe | 37 | 200 | 100 | 99 |
| Sarah | 65 | 155 | 68 | 40 |
| Holly | 6 | 98 | 42 | 41 |

Spreadsheet2.xlsx

| People | Vitamin C | Vitamin D | Vitamin E | Vitamin K |
| ----- | ----- | ----- | ----- | ----- |
| John | 145 | 154 | 295 | 332 |
| Jane | 131 | 1430 | 540 | 350 |
| Fred | 253 | 1834 | 488 | 748 |
| Joe | 67 | 240 | 1500 | 499 |
| Sarah | 655 | 155 | 645 | 440 |
| Holly | 345 | 198 | 200 | 471 |

There are three different heatmaps that could be produced using these two spreadsheets:

1. How vitamins are correlated with each other by entering spreadsheet2 as both of the input spreadsheets.
2. How the metadata (age, height, etc) are correlated with each other by entering spreadsheet1 as both of the input spreadsheets.
3. How the vitamin levels correlate with the metadata but entering spreadsheet1 as the first dataset and spreadhseet2 as the second (or the other way around).

**IMPORTANT: Sample identifiers must be unique and both files must contain the same identifier set. Correlation is an association, not evidence of causation.**

### Running the Program

1. Run the executable, or run `poetry run plot` from a source checkout.
2. Enter the x-axis file, x-axis label, y-axis file, and y-axis label. Relative and absolute paths are supported.
3. Choose Pearson or Spearman correlation.
4. Choose whether to apply Benjamini-Hochberg false-discovery correction. Correction is global across every finite p-value in a heatmap.
5. If censored values are detected, explicitly choose how to handle them.
6. Choose the minimum pairwise sample size.
7. If both files contain a `group` column, choose pooled, stratified, or both analyses. Stratification is the default. Pooled results are labelled unadjusted and may be confounded by group.


### Outputs

All generated files are written under one root `outputs/` directory. Analyses are organised first by the two input files, then by cohort, and finally by raw or FDR significance.

Each individual run contains exactly three files:

1. `correlation_data.csv`: correlation coefficients.
2. `p_value_data.csv` or `adjusted_p_value_data.csv`: the selected significance values.
3. `correlation_heatmap.png`: the corresponding heatmap on a fixed coefficient scale from -1 to 1.

Asterisks indicate the raw or globally adjusted p-value named in the heatmap title.

* No `*` means the p (or q) value is above 0.05.

* `*` means the p (or q) value is above 0.01 and below or equal to 0.05.

* `**` means the p (or q) value is above 0.001 and below or equal to 0.01.

* `***` means the p (or q) value is equal to or below 0.001.


# Developer Instructions

### Dependencies

* [Poetry](https://python-poetry.org/) (Dependency management)
* [Python (3.12-3.14)](https://www.python.org/downloads/)
* [pandas](https://pandas.pydata.org/)
* [matplotlib](https://matplotlib.org/)
* [SciPy](https://scipy.org/)
* [seaborn](https://seaborn.pydata.org/)
* [openpyxl](https://openpyxl.readthedocs.io/en/stable/)
* [NumPy](https://numpy.org/)
* [PyInstaller](https://pyinstaller.org/en/stable/)


### Directory Structure

* `corr_plot/main.py` contains the interactive command-line interface.
* `corr_plot/analysis.py` contains data preparation, statistics, diagnostics, plotting, and output generation.
* `tests/test_analysis.py` contains numerical and edge-case regression tests.
* `pyproject.toml` is the configuration file used by poetry.
* `poetry.lock` controls dependency versions.
* `dist/corr_plot_mac_exe` the executable file for Mac.
* `dist/corr_plot_windows.exe` the executable Windows.

### Development Instructions

* After the project has been git cloned, run `poetry install` to install the relevant dependencies from the `pyproject.toml`.
* To add a dependency, run `poetry add <dependency>`.
* To run the script via the poetry virtual environment, run `poetry run plot` as specified in the `pyproject.toml`.
* To run the test suite, run `MPLBACKEND=Agg poetry run python -m unittest discover -s tests -v`.
* To create a new executable, run `poetry run pyinstaller --onefile corr_plot/main.py`. This pyinstaller command will also produce other artifacts: the `build/` directory and `main.spec` file. I do not need these so I delete them.



