from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
from typing import Literal
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import (
    ConstantInputWarning,
    false_discovery_control,
    pearsonr,
    spearmanr,
)


CorrelationMethod = Literal["pearson", "spearman"]
CensorStrategy = Literal["error", "omit", "limit", "half_limit", "lod_sqrt2"]
FdrScope = Literal["global", "column"]

_CENSORED_VALUE = re.compile(
    r"^\s*<\s*(?P<limit>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)


@dataclass(frozen=True)
class PreparationReport:
    excluded_categorical_columns: tuple[str, ...]
    censored_values_by_column: dict[str, int]
    censor_strategy: CensorStrategy


@dataclass(frozen=True)
class CorrelationResult:
    correlations: pd.DataFrame
    p_values: pd.DataFrame
    sample_sizes: pd.DataFrame
    adjusted_p_values: pd.DataFrame | None = None
    max_leave_one_out_delta: pd.DataFrame | None = None


@dataclass(frozen=True)
class AnalysisSettings:
    correlation_method: CorrelationMethod = "pearson"
    minimum_samples: int = 3
    apply_fdr: bool = True
    fdr_scope: FdrScope = "global"
    fdr_method: str = "bh"
    alternative: str = "two-sided"
    censor_strategy: CensorStrategy = "error"
    calculate_influence: bool = False
    detailed_outputs: bool = False


def read_input_file(path: Path) -> pd.DataFrame:
    """Read a supported input file without guessing its format."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path)
    raise ValueError(
        f"Unsupported input format {suffix!r}. Use .csv, .xlsx, or .xlsm."
    )


def find_censored_values(dataframe: pd.DataFrame) -> dict[str, int]:
    """Count left-censored values such as '<2.25' in each column."""
    result: dict[str, int] = {}
    for column in dataframe.columns[1:]:
        count = int(
            dataframe[column]
            .dropna()
            .astype(str)
            .str.match(_CENSORED_VALUE)
            .sum()
        )
        if count:
            result[str(column)] = count
    return result


def _replace_censored_value(value: object, strategy: CensorStrategy) -> object:
    if pd.isna(value):
        return value

    match = _CENSORED_VALUE.match(str(value))
    if match is None:
        return value

    limit = float(match.group("limit"))
    if strategy == "error":
        raise ValueError(
            f"Left-censored value {value!r} requires an explicit censor strategy."
        )
    if strategy == "omit":
        return np.nan
    if strategy == "limit":
        return limit
    if strategy == "half_limit":
        return limit / 2
    if strategy == "lod_sqrt2":
        return limit / math.sqrt(2)
    raise ValueError(f"Unknown censor strategy: {strategy}")


def prepare_numeric_features(
    dataframe: pd.DataFrame,
    *,
    censor_strategy: CensorStrategy = "error",
) -> tuple[pd.DataFrame, PreparationReport]:
    """
    Retain the identifier and numeric feature columns.

    Entirely categorical columns are reported and excluded. Mixed columns with
    unrecognised nonnumeric values fail rather than being silently corrupted.
    """
    if dataframe.shape[1] < 2:
        raise ValueError("Input data must contain an ID column and at least one feature.")
    if not dataframe.columns.is_unique:
        duplicates = dataframe.columns[dataframe.columns.duplicated()].unique().tolist()
        raise ValueError(f"Input data contains duplicate column names: {duplicates}")

    identifier = dataframe.iloc[:, 0].copy()
    features: dict[str, pd.Series] = {}
    excluded: list[str] = []
    censored_counts = find_censored_values(dataframe)

    for column in dataframe.columns[1:]:
        series = dataframe[column]
        converted_source = series.map(
            lambda value: _replace_censored_value(value, censor_strategy)
        )
        converted = pd.to_numeric(converted_source, errors="coerce")
        invalid_mask = (
            series.notna()
            & converted.isna()
            & ~series.astype(str).str.match(_CENSORED_VALUE)
        )

        numeric_count = int(converted.notna().sum())
        if numeric_count == 0 and invalid_mask.any():
            excluded.append(str(column))
            continue
        if invalid_mask.any():
            examples = series.loc[invalid_mask].astype(str).unique()[:5].tolist()
            raise ValueError(
                f"Column {column!r} mixes numeric and unsupported values: {examples}"
            )
        if numeric_count == 0:
            raise ValueError(f"Feature column {column!r} contains no usable values.")

        features[str(column)] = converted.astype(float)

    if not features:
        raise ValueError("No numeric feature columns were found.")

    prepared = pd.DataFrame({str(dataframe.columns[0]): identifier, **features})
    report = PreparationReport(
        excluded_categorical_columns=tuple(excluded),
        censored_values_by_column=censored_counts,
        censor_strategy=censor_strategy,
    )
    return prepared, report


def validate_and_align_samples(
    x_data: pd.DataFrame, y_data: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate unique IDs and reorder y_data to match x_data by identifier."""
    x_id = x_data.columns[0]
    y_id = y_data.columns[0]

    for name, dataframe, id_column in (
        ("x-axis", x_data, x_id),
        ("y-axis", y_data, y_id),
    ):
        if dataframe[id_column].isna().any():
            raise ValueError(f"{name} data contains missing sample identifiers.")
        duplicates = dataframe.loc[
            dataframe[id_column].duplicated(keep=False), id_column
        ].unique()
        if len(duplicates):
            raise ValueError(
                f"{name} data contains duplicate sample identifiers: "
                f"{duplicates[:5].tolist()}"
            )

    x_ids = pd.Index(x_data[x_id])
    y_ids = pd.Index(y_data[y_id])
    missing_from_y = x_ids.difference(y_ids)
    missing_from_x = y_ids.difference(x_ids)
    if len(missing_from_y) or len(missing_from_x):
        raise ValueError(
            "Sample identifier sets differ. "
            f"Missing from y-axis: {missing_from_y[:5].tolist()}; "
            f"missing from x-axis: {missing_from_x[:5].tolist()}."
        )

    aligned_x = x_data.reset_index(drop=True).copy()
    aligned_y = (
        y_data.set_index(y_id, drop=False)
        .loc[x_ids]
        .reset_index(drop=True)
        .copy()
    )
    return aligned_x, aligned_y


def find_common_group_columns(
    x_data: pd.DataFrame, y_data: pd.DataFrame
) -> tuple[str, str] | None:
    """Find matching columns named 'group', ignoring case."""
    x_groups = [column for column in x_data.columns[1:] if str(column).lower() == "group"]
    y_groups = [column for column in y_data.columns[1:] if str(column).lower() == "group"]
    if len(x_groups) == 1 and len(y_groups) == 1:
        return str(x_groups[0]), str(y_groups[0])
    return None


def validate_group_values(
    x_data: pd.DataFrame,
    y_data: pd.DataFrame,
    group_columns: tuple[str, str],
) -> None:
    x_group, y_group = group_columns
    x_values = x_data[x_group].astype("string").reset_index(drop=True)
    y_values = y_data[y_group].astype("string").reset_index(drop=True)
    if not x_values.equals(y_values):
        raise ValueError("Group assignments do not match between the two files.")


def calculate_correlations(
    y_data: pd.DataFrame,
    x_data: pd.DataFrame,
    *,
    method: CorrelationMethod = "pearson",
    minimum_samples: int = 3,
) -> CorrelationResult:
    """Calculate pairwise-complete correlations with explicit per-cell n."""
    if method not in {"pearson", "spearman"}:
        raise ValueError("method must be 'pearson' or 'spearman'")
    if minimum_samples < 3:
        raise ValueError("minimum_samples must be at least 3")

    y_columns = list(y_data.columns[1:])
    x_columns = list(x_data.columns[1:])
    shape = (len(y_columns), len(x_columns))
    correlations = pd.DataFrame(
        np.nan, index=y_columns, columns=x_columns, dtype=float
    )
    p_values = pd.DataFrame(np.nan, index=y_columns, columns=x_columns, dtype=float)
    sample_sizes = pd.DataFrame(0, index=y_columns, columns=x_columns, dtype=int)

    for y_column in y_columns:
        for x_column in x_columns:
            pair = pd.DataFrame(
                {
                    "y": pd.to_numeric(y_data[y_column], errors="coerce"),
                    "x": pd.to_numeric(x_data[x_column], errors="coerce"),
                }
            ).dropna()
            sample_sizes.loc[y_column, x_column] = len(pair)

            if len(pair) < minimum_samples:
                continue
            if pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
                continue

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConstantInputWarning)
                if method == "pearson":
                    result = pearsonr(
                        pair["y"].to_numpy(),
                        pair["x"].to_numpy(),
                        alternative="two-sided",
                    )
                else:
                    result = spearmanr(
                        pair["y"].to_numpy(),
                        pair["x"].to_numpy(),
                        alternative="two-sided",
                    )

            statistic = float(result.statistic)
            p_value = float(result.pvalue)
            if np.isfinite(statistic) and np.isfinite(p_value):
                correlations.loc[y_column, x_column] = statistic
                p_values.loc[y_column, x_column] = p_value

    return CorrelationResult(
        correlations=correlations,
        p_values=p_values,
        sample_sizes=sample_sizes,
    )


def calculate_leave_one_out_influence(
    y_data: pd.DataFrame,
    x_data: pd.DataFrame,
    result: CorrelationResult,
    *,
    method: CorrelationMethod = "pearson",
    minimum_samples: int = 3,
) -> pd.DataFrame:
    """
    Return the largest absolute change in each coefficient after removing one sample.

    Values remain NaN when a pair cannot be recalculated after removing a sample.
    This is a sensitivity diagnostic, not an instruction to delete observations.
    """
    influence = pd.DataFrame(
        np.nan,
        index=result.correlations.index,
        columns=result.correlations.columns,
        dtype=float,
    )
    for y_column in result.correlations.index:
        for x_column in result.correlations.columns:
            full_coefficient = result.correlations.loc[y_column, x_column]
            if not np.isfinite(full_coefficient):
                continue

            pair = pd.DataFrame(
                {
                    "y": pd.to_numeric(y_data[y_column], errors="coerce"),
                    "x": pd.to_numeric(x_data[x_column], errors="coerce"),
                }
            ).dropna()
            if len(pair) <= minimum_samples:
                continue

            changes: list[float] = []
            for position in range(len(pair)):
                reduced = pair.drop(pair.index[position])
                if (
                    len(reduced) < minimum_samples
                    or reduced["x"].nunique() < 2
                    or reduced["y"].nunique() < 2
                ):
                    continue
                if method == "pearson":
                    coefficient = pearsonr(
                        reduced["y"].to_numpy(), reduced["x"].to_numpy()
                    ).statistic
                else:
                    coefficient = spearmanr(
                        reduced["y"].to_numpy(), reduced["x"].to_numpy()
                    ).statistic
                if np.isfinite(coefficient):
                    changes.append(abs(float(coefficient) - full_coefficient))

            if changes:
                influence.loc[y_column, x_column] = max(changes)
    return influence


def feature_diagnostics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Summarise distributions without using significance tests as data-quality gates."""
    rows: dict[str, dict[str, float | int]] = {}
    for column in dataframe.columns[1:]:
        values = pd.to_numeric(dataframe[column], errors="coerce")
        rows[str(column)] = {
            "n": int(values.notna().sum()),
            "missing": int(values.isna().sum()),
            "unique": int(values.nunique()),
            "mean": float(values.mean()),
            "standard_deviation": float(values.std()),
            "median": float(values.median()),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
            "skewness": float(values.skew()),
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def adjust_p_values(
    p_values: pd.DataFrame,
    *,
    scope: FdrScope = "global",
    method: str = "bh",
) -> pd.DataFrame:
    """Adjust only finite p-values, accepting valid boundary values 0 and 1."""
    numeric = p_values.apply(pd.to_numeric, errors="coerce").astype(float)
    finite_values = numeric.to_numpy()[np.isfinite(numeric.to_numpy())]
    if ((finite_values < 0) | (finite_values > 1)).any():
        raise ValueError("P-values must be between 0 and 1 inclusive.")

    adjusted = pd.DataFrame(
        np.nan, index=numeric.index, columns=numeric.columns, dtype=float
    )
    if scope == "global":
        finite_mask = np.isfinite(numeric.to_numpy())
        if finite_mask.any():
            adjusted_values = false_discovery_control(
                numeric.to_numpy()[finite_mask], method=method
            )
            adjusted_array = adjusted.to_numpy()
            adjusted_array[finite_mask] = adjusted_values
            adjusted.iloc[:, :] = adjusted_array
        return adjusted

    if scope == "column":
        for column in numeric.columns:
            finite_mask = np.isfinite(numeric[column].to_numpy())
            if finite_mask.any():
                values = numeric[column].to_numpy()[finite_mask]
                adjusted.loc[finite_mask, column] = false_discovery_control(
                    values, method=method
                )
        return adjusted

    raise ValueError("scope must be 'global' or 'column'")


def add_fdr_adjustment(
    result: CorrelationResult,
    *,
    scope: FdrScope = "global",
    method: str = "bh",
) -> CorrelationResult:
    return CorrelationResult(
        correlations=result.correlations,
        p_values=result.p_values,
        sample_sizes=result.sample_sizes,
        adjusted_p_values=adjust_p_values(
            result.p_values, scope=scope, method=method
        ),
        max_leave_one_out_delta=result.max_leave_one_out_delta,
    )


def significance_annotations(values: pd.DataFrame) -> pd.DataFrame:
    numeric = values.apply(pd.to_numeric, errors="coerce")
    return numeric.map(
        lambda value: (
            ""
            if pd.isna(value)
            else "***"
            if value <= 0.001
            else "**"
            if value <= 0.01
            else "*"
            if value <= 0.05
            else ""
        )
    )


def plot_correlation_heatmap(
    result: CorrelationResult,
    significance_values: pd.DataFrame,
    *,
    x_axis_label: str,
    y_axis_label: str,
    output_path: Path,
    method: CorrelationMethod,
    significance_label: str,
) -> None:
    rows, columns = result.correlations.shape
    figsize = (max(10, columns * 0.8), max(8, rows * 0.8))
    figure, axis = plt.subplots(figsize=figsize)
    heatmap = sns.heatmap(
        result.correlations,
        annot=significance_annotations(significance_values),
        cmap="coolwarm",
        center=0,
        fmt="",
        linewidths=0.5,
        annot_kws={"size": 12},
        vmin=-1,
        vmax=1,
        ax=axis,
    )
    axis.set_xlabel(x_axis_label, labelpad=10)
    axis.set_ylabel(y_axis_label)
    axis.set_title(
        f"{method.title()} correlation heatmap ({significance_label})"
    )
    colorbar = heatmap.collections[0].colorbar
    colorbar.set_label(f"{method.title()} correlation coefficient")
    figure.subplots_adjust(bottom=0.1, left=0.2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, bbox_inches="tight")
    plt.close(figure)


def write_analysis_outputs(
    result: CorrelationResult,
    *,
    output_directory: Path,
    settings: AnalysisSettings,
    x_axis_label: str,
    y_axis_label: str,
    x_report: PreparationReport,
    y_report: PreparationReport,
    x_diagnostics: pd.DataFrame,
    y_diagnostics: pd.DataFrame,
    cohort_name: str,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    result.correlations.to_csv(output_directory / "correlation_data.csv")

    if result.adjusted_p_values is not None:
        result.adjusted_p_values.to_csv(output_directory / "adjusted_p_value_data.csv")
        plot_correlation_heatmap(
            result,
            result.adjusted_p_values,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            output_path=output_directory / "correlation_heatmap.png",
            method=settings.correlation_method,
            significance_label=f"global {settings.fdr_method.upper()} FDR",
        )
    else:
        result.p_values.to_csv(output_directory / "p_value_data.csv")
        plot_correlation_heatmap(
            result,
            result.p_values,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            output_path=output_directory / "correlation_heatmap.png",
            method=settings.correlation_method,
            significance_label="raw p-values",
        )

    if not settings.detailed_outputs:
        return

    result.p_values.to_csv(output_directory / "p_value_data.csv")
    result.sample_sizes.to_csv(output_directory / "sample_size_data.csv")
    x_diagnostics.to_csv(output_directory / "x_feature_diagnostics.csv")
    y_diagnostics.to_csv(output_directory / "y_feature_diagnostics.csv")
    if result.max_leave_one_out_delta is not None:
        result.max_leave_one_out_delta.to_csv(
            output_directory / "max_leave_one_out_delta_data.csv"
        )

    finite_n = result.sample_sizes.to_numpy()
    influence = result.max_leave_one_out_delta
    x_skewed = int((x_diagnostics["skewness"].abs() > 1).sum())
    y_skewed = int((y_diagnostics["skewness"].abs() > 1).sum())
    influential_pairs = (
        int((influence.to_numpy() > 0.2).sum())
        if influence is not None
        else None
    )
    analysis_warnings: list[str] = []
    if x_skewed or y_skewed:
        analysis_warnings.append(
            "Features with absolute skewness over 1 were detected. Inspect "
            "distributions and pre-specify any defensible transformation."
        )
    if influential_pairs:
        analysis_warnings.append(
            "Some coefficients change by more than 0.20 when one sample is "
            "removed. Inspect these pairs; do not automatically delete samples."
        )
    if cohort_name == "all_groups_unadjusted":
        analysis_warnings.append(
            "This pooled analysis is not adjusted for group and may be confounded."
        )
    if settings.correlation_method == "spearman" and finite_n.max() < 500:
        analysis_warnings.append(
            "SciPy Spearman p-values are asymptotic at these sample sizes. "
            "Use a pre-specified permutation procedure for confirmatory inference."
        )
    metadata = {
        "cohort": cohort_name,
        "settings": asdict(settings),
        "x_axis_label": x_axis_label,
        "y_axis_label": y_axis_label,
        "x_preparation": asdict(x_report),
        "y_preparation": asdict(y_report),
        "number_of_tests": int(np.isfinite(result.p_values.to_numpy()).sum()),
        "minimum_cell_sample_size": int(finite_n.min()),
        "maximum_cell_sample_size": int(finite_n.max()),
        "x_features_with_absolute_skewness_over_1": x_skewed,
        "y_features_with_absolute_skewness_over_1": y_skewed,
        "pairs_with_leave_one_out_delta_over_0_2": influential_pairs,
        "analysis_warnings": analysis_warnings,
        "significance_stars": {
            "*": "p or adjusted p <= 0.05",
            "**": "p or adjusted p <= 0.01",
            "***": "p or adjusted p <= 0.001",
        },
        "interpretation_note": (
            "Correlation is an association, not evidence of causation. "
            "Pooled cohorts may be confounded by group or other covariates."
        ),
    }
    (output_directory / "analysis_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )


def run_analysis(
    x_data: pd.DataFrame,
    y_data: pd.DataFrame,
    *,
    output_directory: Path,
    x_axis_label: str,
    y_axis_label: str,
    settings: AnalysisSettings,
    cohort_name: str = "all_samples",
) -> CorrelationResult:
    aligned_x, aligned_y = validate_and_align_samples(x_data, y_data)
    prepared_x, x_report = prepare_numeric_features(
        aligned_x, censor_strategy=settings.censor_strategy
    )
    prepared_y, y_report = prepare_numeric_features(
        aligned_y, censor_strategy=settings.censor_strategy
    )
    x_diagnostics = feature_diagnostics(prepared_x)
    y_diagnostics = feature_diagnostics(prepared_y)
    result = calculate_correlations(
        prepared_y,
        prepared_x,
        method=settings.correlation_method,
        minimum_samples=settings.minimum_samples,
    )
    if settings.calculate_influence:
        result = CorrelationResult(
            correlations=result.correlations,
            p_values=result.p_values,
            sample_sizes=result.sample_sizes,
            max_leave_one_out_delta=calculate_leave_one_out_influence(
                prepared_y,
                prepared_x,
                result,
                method=settings.correlation_method,
                minimum_samples=settings.minimum_samples,
            ),
        )
    if settings.apply_fdr:
        result = add_fdr_adjustment(
            result, scope=settings.fdr_scope, method=settings.fdr_method
        )
    write_analysis_outputs(
        result,
        output_directory=output_directory,
        settings=settings,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
        x_report=x_report,
        y_report=y_report,
        x_diagnostics=x_diagnostics,
        y_diagnostics=y_diagnostics,
        cohort_name=cohort_name,
    )
    return result
