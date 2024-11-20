import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def main():

    file_path = "MD231120_mvdamatrix_all_v1.xlsx"

    df = pd.read_excel(file_path)

    print(df.head())


if __name__ == "__main__":
    main()
