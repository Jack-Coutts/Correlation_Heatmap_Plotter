import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

meta = "meta_data.xlsx"
data = "lipid_class.xlsx"


def calculate_correlation_and_pvalue(df1, df2):
    correlation_df = pd.DataFrame()
    p_value_df = pd.DataFrame()

    for col1 in df1.columns[1:]:  # Exclude the first column (ID)
        for col2 in df2.columns[1:]:  # Exclude the first column (ID)
            # Drop rows with missing values
            merged = pd.concat([df1[col1], df2[col2]], axis=1).dropna()
            if (
                len(merged) > 1
            ):  # Ensure there are enough data points to calculate correlation
                corr, p_value = pearsonr(merged[col1], merged[col2])
                correlation_df.loc[col1, col2] = corr
                p_value_df.loc[col1, col2] = p_value
            else:
                correlation_df.loc[col1, col2] = None
                p_value_df.loc[col1, col2] = None

    return correlation_df, p_value_df


def main():

    metadata = pd.read_excel(meta)
    df = pd.read_excel(data)

    print(metadata.head())
    print("-----")
    print(df.head())

    correlation_df, p_value_df = calculate_correlation_and_pvalue(df, metadata)

    p_value_annotations = p_value_df.applymap(
        lambda x: f"{x:.3g}" if isinstance(x, (int, float)) else x
    )

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
    plt.xlabel("Metadata Classes")
    plt.ylabel("Lipid Classes")

    # Label the color scale
    cbar = heatmap.collections[0].colorbar
    cbar.set_label("Pearson Correlation Coefficient")

    # Add a note at the bottom
    plt.figtext(
        0.5,
        0.05,
        "p-values of the pearson correlation coefficients are displayed in the annotations. p < 0.05 indicates statistical significance.",
        ha="center",
        fontsize=10,
    )

    # Adjust the layout to ensure the note is visible
    plt.subplots_adjust(bottom=0.2)

    plt.title("Correlation Heatmap")
    plt.show()


if __name__ == "__main__":
    main()
