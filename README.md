# Correlation Heatmap Plotter

This program uses [scipy's pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) function to calculate the Pearson correlation coefficient and the corresponding p vales to quantify the correlation between the features in two excel spreadsheets. These correlation coefficients and p values are then used to generate a correlation heatmap with [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/). 

## User Instructions

### Downloading the Program

* On Mac click [this](https://github.com/Jack-Coutts/Correlation_Heatmap_plotter/releases/download/v1.0.0/corr_plot_mac_exe) link to download the executable file. 

* On Windows click [this](https://github.com/Jack-Coutts/Correlation_Heatmap_plotter/releases/download/v1.0.0/corr_plot_windows.exe) link to download the executable file.

NOTE: Both of these files can also be found in the GitHub release or in the `dist/` directory in this repository.

**IMPORTANT: It is recommended that you save this file in a folder that also contains your input data files (which are described below).**

### Input Data

This program works with two single-sheet excel files (.xlsx format) which both have an identical first column. This first columns should be observations/samples/individuals where each row represents measurements from a single individual/observation/sample. The remaining columns can be the measured features of that individual/observation/sample. 

Take the two spreasheets containing fake data below as examples:

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

There are three different heatmaps that can be produced using these two spreadsheets:

1. How vitamins are correlated with each other by entering spreadsheet2 as both of the input spreadsheets.
2. How the metadata (age, height, etc) are correlated with each other by entering spreadsheet1 as both of the input spreadsheets.
3. How the vitamin levels correlate with the metadata but entering spreadsheet1 as the first dataset and spreadhseet2 as the second (or the other way around). 

It is essential that the first column is always identical accross both of the spreadsheets.

### Running the Program

1. To run the program simply double click on the `corr_plot_mac_exe` or `corr_plot_windows.exe` file.
2. A black window should appear and you should need to wait approximately 30 seconds for the program to load and for the following text to appear: `Please enter the file path of the x axis data e.g.metadata.xlsx: `. Here you should enter the file path to the data you want on the x axis of your correlation heatmap. If you placed the executable file in the same folder as you data, then the user response might be `spreadsheet1.xlsx`. If you have your executable file in the `/Desktop/` folder and the data was in the `/Desktop/data/spreadsheet1.xlsx` file then the user would need to enter `data/spreadsheet1.xlsx`. This is because all file paths used by this program are relative, absolute file paths will not work! Once you have entered the file path, press enter and the program will check that it can find the file. 
3. You will next be asked for the x axis label you want displayed on your heatmap. 
4. You will then be asked for the data you want on the y axis. This works in the exact same way as for the x axis. 
5. Similarly, you will then be asked for the y axis label.
6. The correlation heatmap will then be created and the text on the screen will tell you if it has been successful.


### Outputs

This program creates three outputs. 

1. A correlation heatmap in a .png file.
2. A csv file containing all of the Pearson Correlation Coefficients calculated by the `pearsonr` function and used for the heatmap.
3. A csv file containing all of the p values calculated by the `pearsonr` function and used for the heatmap. 

These files will be added to a folder called `corr_plot_outputs` which will be created in the same folder as the one in which you have placed the executable file. 


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
* `dist/corr_plot_windows.exe` the executable Windows.

### Development Instructions

* After the project has been git cloned, run `poetry install` to install the relevant dependencies from the `pyproject.toml`.
* To add a dependency, run `poetry add <dependency>`.
* To run the script via the poetry virtual environment, run `poetry run plot` as specified in the `pyproject.toml`.
* To create a new executable, run `poetry run pyinstaller --onefile corr_plot/main.py`. This pyinstaller command will also produce other artifacts: the `build/` directory and `main.spec` file. I do not need these so I delete them.
* NOTE: All file paths are relative.



