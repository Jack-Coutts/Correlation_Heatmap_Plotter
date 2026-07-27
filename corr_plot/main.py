from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import cast

import pandas as pd

from corr_plot.analysis import (
    AnalysisSettings,
    CensorStrategy,
    CorrelationMethod,
    find_censored_values,
    find_common_group_columns,
    read_input_file,
    run_analysis,
    validate_and_align_samples,
    validate_group_values,
)


def get_base_dir() -> Path:
    """Return the executable directory or this module's directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter y or n.")


def ask_choice(prompt: str, choices: tuple[str, ...], default: str) -> str:
    options = "/".join(choices)
    while True:
        answer = input(f"{prompt} ({options}) [{default}]: ").strip().lower()
        if not answer:
            return default
        if answer in choices:
            return answer
        print(f"Please choose one of: {', '.join(choices)}.")


def file_checker(file_type: str, base_dir: Path) -> Path:
    while True:
        entered = Path(input(f"Please enter the path of the {file_type}: ").strip())
        candidate = entered if entered.is_absolute() else base_dir / entered
        candidate = candidate.resolve()
        if candidate.is_file():
            print(f"File found: {candidate}")
            return candidate
        print("File not found.")


def get_data(
    base_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, str, str, Path, Path]:
    x_path = file_checker("x-axis data (.csv or .xlsx)", base_dir)
    x_axis_label = input("Please enter the x-axis label: ").strip() or "X features"
    y_path = file_checker("y-axis data (.csv or .xlsx)", base_dir)
    y_axis_label = input("Please enter the y-axis label: ").strip() or "Y features"
    return (
        read_input_file(x_path),
        read_input_file(y_path),
        x_axis_label,
        y_axis_label,
        x_path,
        y_path,
    )


def choose_censor_strategy(
    x_data: pd.DataFrame, y_data: pd.DataFrame
) -> CensorStrategy:
    censored = {
        "x-axis": find_censored_values(x_data),
        "y-axis": find_censored_values(y_data),
    }
    total = sum(sum(columns.values()) for columns in censored.values())
    if not total:
        return "error"

    print(f"Detected {total} left-censored value(s), such as '<2.25': {censored}")
    print(
        "Choose explicitly: error; omit; use detection limit; use half the limit; "
        "or use limit/sqrt(2). The correct choice depends on the assay plan."
    )
    answer = ask_choice(
        "Censor handling",
        ("error", "omit", "limit", "half_limit", "lod_sqrt2"),
        "error",
    )
    return cast(CensorStrategy, answer)


def _safe_directory_name(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return slug or "unnamed_group"


def build_cohorts(
    x_data: pd.DataFrame, y_data: pd.DataFrame
) -> list[tuple[str, pd.DataFrame, pd.DataFrame]]:
    group_columns = find_common_group_columns(x_data, y_data)
    if group_columns is None:
        return [("all_samples", x_data, y_data)]

    validate_group_values(x_data, y_data, group_columns)
    x_group, _ = group_columns
    groups = x_data[x_group].dropna().unique().tolist()
    if len(groups) < 2:
        return [("all_samples", x_data, y_data)]

    print(f"Detected common grouping variable with levels: {groups}")
    mode = ask_choice(
        "Analysis cohorts",
        ("pooled", "stratified", "both"),
        "stratified",
    )

    cohorts: list[tuple[str, pd.DataFrame, pd.DataFrame]] = []
    if mode in {"pooled", "both"}:
        print(
            "Warning: pooled correlations are unadjusted and may be confounded by group."
        )
        cohorts.append(("all_groups_unadjusted", x_data, y_data))
    if mode in {"stratified", "both"}:
        for group in groups:
            mask = x_data[x_group].eq(group)
            cohorts.append(
                (
                    _safe_directory_name(group),
                    x_data.loc[mask].reset_index(drop=True),
                    y_data.loc[mask].reset_index(drop=True),
                )
            )
    return cohorts


def main() -> None:
    print("Correlation Heatmap Plotter")
    base_dir = get_base_dir()
    x_data, y_data, x_label, y_label, x_path, y_path = get_data(base_dir)
    x_data, y_data = validate_and_align_samples(x_data, y_data)

    method = cast(
        CorrelationMethod,
        ask_choice(
            "Correlation method",
            ("pearson", "spearman"),
            "pearson",
        ),
    )
    apply_fdr = ask_yes_no(
        "Apply global Benjamini-Hochberg false-discovery correction? (y/n): "
    )
    censor_strategy = choose_censor_strategy(x_data, y_data)
    minimum_samples = int(
        ask_choice(
            "Minimum pairwise sample size",
            ("3", "5", "10"),
            "3",
        )
    )

    settings = AnalysisSettings(
        correlation_method=method,
        minimum_samples=minimum_samples,
        apply_fdr=apply_fdr,
        fdr_scope="global",
        censor_strategy=censor_strategy,
    )
    cohorts = build_cohorts(x_data, y_data)
    output_root = (
        base_dir / "outputs"
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[1] / "outputs"
    )

    for cohort_name, cohort_x, cohort_y in cohorts:
        output_directory = (
            output_root
            if len(cohorts) == 1
            else output_root / cohort_name
        )
        result = run_analysis(
            cohort_x,
            cohort_y,
            output_directory=output_directory,
            x_axis_label=x_label,
            y_axis_label=y_label,
            settings=settings,
            cohort_name=cohort_name,
        )
        valid_tests = int(result.p_values.notna().sum().sum())
        print(
            f"Created {cohort_name}: {valid_tests} valid tests in "
            f"{output_directory}"
        )

    print(
        "Analysis complete. Review analysis_metadata.json for preprocessing and "
        "interpretation details."
    )
    print(f"Inputs: {x_path} and {y_path}")


if __name__ == "__main__":
    main()
