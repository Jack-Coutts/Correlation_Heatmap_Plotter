from typing import Tuple
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from pathlib import Path
import os
import sys


def get_base_dir():

    # Determine the directory of the executable or script
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as a normal script
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return base_dir


def file_checker(file_type: str, base_dir: Path) -> Path:

    # Get the name of the file and check it exists
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


def get_data(base_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:

    metadata = file_checker("metadata.xlxs", base_dir)
    measured_data = file_checker("measured_data.xlxs", base_dir)

    metadata_df = pd.read_excel(metadata)
    measured_data_df = pd.read_excel(measured_data)

    return metadata_df, measured_data_df


def check_sample_match(
    metadata_df: pd.DataFrame, measured_data_df: pd.DataFrame
):

    meta_sample_col = metadata_df.iloc[:, 0]  # Select the first column
    measured_sample_col = measured_data_df.iloc[:, 0]  # Select the first column

    are_columns_equal = meta_sample_col.equals(measured_sample_col)

    if are_columns_equal:
        print("Sample columns match.")
    else:
        print("Sample columns do not match!")
        # Exit the program
        sys.exit("Exiting the program")


def calculate_correlation_and_pvalue(
    measured_data_df: pd.DataFrame, metadata_df: pd.DataFrame
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
                corr, p_value = pearsonr(merged[data_col_1], merged[meta_col_1])
                correlation_df.loc[data_col_1, meta_col_1] = corr
                p_value_df.loc[data_col_1, meta_col_1] = p_value
            else:
                correlation_df.loc[data_col_1, meta_col_1] = None
                p_value_df.loc[data_col_1, meta_col_1] = None

    # Replace None with NaN for correlation_df
    # Replace None with NaN and convert to float
    correlation_df = correlation_df.apply(pd.to_numeric, errors="coerce")

    return correlation_df, p_value_df


def p_val_sig_figs(p_value_df: pd.DataFrame) -> pd.DataFrame:

    p_value_annotations = p_value_df.apply(
        lambda x: x.map(
            lambda y: f"{y:.3g}" if isinstance(y, (int, float)) else y
        )
    )

    return p_value_annotations


def plot_pearson_correlation_heatmap(
    correlation_df: pd.DataFrame, p_value_annotations: pd.DataFrame
):

    plt.figure(figsize=(10, 8))
    heatmap = sns.heatmap(
        correlation_df,
        annot=p_value_annotations,
        cmap="coolwarm",
        fmt="",
        linewidths=0.5,
        annot_kws={"size": 10},
    )

    # Label the axes
    plt.xlabel("Metadata Classes", labelpad=10)
    plt.ylabel("Lipid Classes")

    # Label the color scale
    cbar = heatmap.collections[0].colorbar
    cbar.set_label("Pearson Correlation Coefficient")

    # Add a note at the bottom
    plt.figtext(
        0.5,
        0.01,
        "*p-values of the pearson correlation coefficients are displayed in the heatmap (p < 0.05 indicates statistical significance).",
        ha="center",
        fontsize=7,
    )

    # Adjust the layout to ensure the note is visible
    plt.subplots_adjust(bottom=0.1, left=0.2)

    plt.title("Pearson Correlation Heatmap")
    plt.savefig(f"pearson_corr_heatmap.png")
    print("Heatmap Plotted Successfully.")


def main():

    # Your program logic here
    print("Program is running...")

    base_dir = get_base_dir()

    metadata_df, measured_data_df = get_data(base_dir)

    check_sample_match(metadata_df, measured_data_df)

    correlation_df, p_value_df = calculate_correlation_and_pvalue(
        measured_data_df, metadata_df
    )

    p_value_annotations = p_val_sig_figs(p_value_df)

    plot_pearson_correlation_heatmap(correlation_df, p_value_annotations)

    # Exit the program
    sys.exit("Exiting the program")


if __name__ == "__main__":
    main()
