# Correlation Heatmap Plotter

This [Python](https://www.python.org/) program uses the [pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) function from [SciPy](https://scipy.org/) to calculate the Pearson correlation coefficients and corresponding p values to describe the correlation between two sets of features. These values are then used to generate a Correlation Heatmap with [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/). 

# User Instructions

### Downloading the Program

* On Mac click [this](https://github.com/Jack-Coutts/Correlation_Heatmap_plotter/releases/download/v1.0.0/corr_plot_mac_exe) link to download the executable file. 

* On Windows click [this](https://github.com/Jack-Coutts/Correlation_Heatmap_plotter/releases/download/v1.0.0/corr_plot_windows.exe) link to download the executable file.

NOTE: Both of these files can also be found in the GitHub release or in the `dist/` directory in this repository.

**IMPORTANT: It is recommended that you save this file in a folder that also contains your input data files (which are described below).**

### Input Data

This program works with two single-sheet excel files (.xlsx format) which both have an identical first column. This first column should be an identifier for each sample/individual with the remaining columns being different features/measurements/metadata associated with the sample/individual. 

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

**IMPORTANT: It is essential that the first column is always identical across both of the spreadsheets.**

### Running the Program

1. To run the program, simply double click on the `corr_plot_mac_exe` or `corr_plot_windows.exe` file that you've downloaded.

2. A black window should appear, and you should need to wait approximately 30 seconds for the program to load. Then, the following text will appear: `Please enter the file path of the x axis data e.g.metadata.xlsx: `. Here you should enter the file path for the data you want on the x axis of your correlation heatmap. If you placed the executable file in the same folder as your data, then your response might be `spreadsheet1.xlsx`. If you have your executable file in the `Desktop/` folder and your data had the `/Desktop/data/spreadsheet1.xlsx` file path, then you would need to enter `data/spreadsheet1.xlsx`. This is because all file paths used by this program are **relative**, absolute file paths will not work! Once you have entered the file path, press enter and the program will check the file exists at the specified file path.

3. Next, you'll be asked for the x axis label to be displayed on the heatmap.

4. Then, you'll be asked for the data you want on the y axis. This works in the same way as for the x axis. 

5. Similarly, you will then be asked for the y axis label.

6. The correlation heatmap will then be created and the text on screen will confirm this has been successful.


### Outputs

This program creates three outputs. 

1. A correlation heatmap in a `.png` file.
2. A `.csv` file containing all of the Pearson Correlation Coefficients calculated by the `pearsonr` function used for the heatmap.
3. A `.csv` file containing all of the p values calculated by the `pearsonr` function used for the heatmap. 

These files will be added to a folder called `corr_plot_outputs` which will be created in the same folder as the one in which you've saved the executable file. 

On the heatmap, the colour of a block indicates the strength of a correlation (Pearson Correlation Coefficient) and the number/absence of asterisks is indicative of the p value.

* No `*` means the p value is above 0.05.

* `*` means the p value is above 0.01 and below or equal to 0.05.

* `**` means the p value is above 0.001 and below or equal to 0.01.

* `***` means the p value is equal to or below 0.001.


# Developer Instructions

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
* `dist/corr_plot_windows.exe` the executable Windows.

### Development Instructions

* After the project has been git cloned, run `poetry install` to install the relevant dependencies from the `pyproject.toml`.
* To add a dependency, run `poetry add <dependency>`.
* To run the script via the poetry virtual environment, run `poetry run plot` as specified in the `pyproject.toml`.
* To create a new executable, run `poetry run pyinstaller --onefile corr_plot/main.py`. This pyinstaller command will also produce other artifacts: the `build/` directory and `main.spec` file. I do not need these so I delete them.
* NOTE: All file paths are relative.



