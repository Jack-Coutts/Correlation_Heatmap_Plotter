from typing import Tuple
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from pathlib import Path
import os
import sys


# Set the base directory
def get_base_dir():
    # Determine the directory of the executable or script
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as a normal script
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return base_dir


# Get the file path of a user specified file and check it exists
def file_checker(file_type: str, base_dir: Path) -> Path:
    file_path = None
    while file_path is None:
        file_path = Path(
            os.path.join(
                base_dir,
                Path(input(f"Please enter the path of the {file_type}: ")),
            )
        )
        if file_path.is_file():  # file exists
            print("File found.")
            return file_path
        else:
            print("File not found.")
            file_path = None


# Get the two data files which will correspond to each axis of the heatmap
def get_data(base_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, str, str]:
    metadata = file_checker("x axis data e.g.metadata.xlxs", base_dir)
    x_axis_label = input("Please enter the x axis label: ")
    measured_data = file_checker(
        "y axis data e.g.measured_data.xlxs", base_dir
    )
    y_axis_label = input("Please enter the y axis label: ")

    metadata_df = pd.read_excel(metadata)
    measured_data_df = pd.read_excel(measured_data)

    return metadata_df, measured_data_df, x_axis_label, y_axis_label


# Check the first column of both dataframes is the same
def check_sample_match(
    metadata_df: pd.DataFrame, measured_data_df: pd.DataFrame
):
    meta_sample_col = metadata_df.iloc[:, 0]  # Select the first column
    measured_sample_col = measured_data_df.iloc[
        :, 0
    ]  # Select the first column

    are_columns_equal = meta_sample_col.equals(measured_sample_col)

    if are_columns_equal:
        print("Sample columns match.")
    else:
        print("Sample columns do not match!")
        # Exit the program
        sys.exit("Exiting the program")


# Calculate the pearson correlation and corresponding p values
def calculate_correlation_and_pvalue(
    measured_data_df: pd.DataFrame, metadata_df: pd.DataFrame, base_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Initialize DataFrames with appropriate indices and columns
    correlation_df = pd.DataFrame(
        index=measured_data_df.columns[1:], columns=metadata_df.columns[1:]
    )
    p_value_df = pd.DataFrame(
        index=measured_data_df.columns[1:], columns=metadata_df.columns[1:]
    )

    for data_col_1 in measured_data_df.columns[
        1:
    ]:  # Exclude the first column (ID)
        for meta_col_1 in metadata_df.columns[
            1:
        ]:  # Exclude the first column (ID)
            # Drop rows with missing values
            merged = pd.concat(
                [measured_data_df[data_col_1], metadata_df[meta_col_1]], axis=1
            ).dropna()
            if (
                len(merged) > 1
            ):  # Ensure there are enough data points to calculate correlation
                corr, p_value = pearsonr(
                    merged[data_col_1], merged[meta_col_1]
                )
                correlation_df.loc[data_col_1, meta_col_1] = corr
                p_value_df.loc[data_col_1, meta_col_1] = p_value
            else:
                correlation_df.loc[data_col_1, meta_col_1] = None
                p_value_df.loc[data_col_1, meta_col_1] = None

    # Replace None with NaN and convert to float
    correlation_df = correlation_df.apply(pd.to_numeric, errors="coerce")

    os.makedirs(f"{base_dir}/corr_plot_outputs/", exist_ok=True)

    correlation_df.to_csv(f"{base_dir}/corr_plot_outputs/correlation_data.csv")
    print("Created correlation_plot_csv.")

    p_value_df.to_csv(f"{base_dir}/corr_plot_outputs/p_value_data.csv")
    print("Created p_value_data_csv.")

    return correlation_df, p_value_df


# Create p value indicators using *'s
def p_val_indicator(p_value_df: pd.DataFrame) -> pd.DataFrame:
    # Convert all values to numeric types
    p_value_df = p_value_df.apply(pd.to_numeric, errors="coerce")

    # Apply the lambda function to handle the conditions
    p_value_annotations = p_value_df.apply(
        lambda x: x.map(
            lambda y: (
                "***"
                if y <= 0.001
                else "**"
                if y <= 0.01
                else "*"
                if y <= 0.05
                else ""
            )
        )
    )

    return p_value_annotations


# Plot the heatmap
def plot_pearson_correlation_heatmap(
    correlation_df: pd.DataFrame,
    p_value_annotations: pd.DataFrame,
    x_axis_label: str,
    y_axis_label: str,
    base_dir: Path,
):
    # Dynamically adjust the figure size based on the number of rows/columns
    num_rows, num_cols = correlation_df.shape
    col_size = num_cols * 0.8
    row_size = num_rows * 0.8

    figsize = (
        col_size if col_size > 10 else 10,
        row_size if row_size > 8 else 8,
    )  # Adjust the scaling factor as needed

    # Find largest absolute correlation to set a symmetrical colour scale
    max_corr_value = max(
        abs(correlation_df.min().min()), abs(correlation_df.max().max())
    )

    plt.figure(figsize=figsize)
    heatmap = sns.heatmap(
        correlation_df,
        annot=p_value_annotations,
        cmap="coolwarm",
        fmt="",
        linewidths=0.5,
        annot_kws={"size": 12},
        vmin=-max_corr_value,  # Center the colormap at 0
        vmax=max_corr_value,
    )

    # Label the axes
    plt.xlabel(x_axis_label, labelpad=10)
    plt.ylabel(y_axis_label)

    # Label the color scale
    cbar = heatmap.collections[0].colorbar
    cbar.set_label("Pearson Correlation Coefficient")

    # Adjust the layout to ensure the note is visible
    plt.subplots_adjust(bottom=0.1, left=0.2)

    plt.title("Pearson Correlation Heatmap")
    plt.savefig(
        f"{base_dir}/corr_plot_outputs/pearson_corr_heatmap.png",
        bbox_inches="tight",
    )
    print("Heatmap Plotted Successfully.")


# Run the script
def main():
    # Your program logic here
    print("Program is running...")

    base_dir = get_base_dir()

    metadata_df, measured_data_df, x_axis_label, y_axis_label = get_data(
        base_dir
    )

    check_sample_match(metadata_df, measured_data_df)

    correlation_df, p_value_df = calculate_correlation_and_pvalue(
        measured_data_df, metadata_df, base_dir
    )

    p_value_annotations = p_val_indicator(p_value_df)

    plot_pearson_correlation_heatmap(
        correlation_df,
        p_value_annotations,
        x_axis_label,
        y_axis_label,
        base_dir,
    )

    # Exit the program
    sys.exit("Exiting the program")


if __name__ == "__main__":
    main()
