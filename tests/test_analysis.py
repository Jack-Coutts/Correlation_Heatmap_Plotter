from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control

from corr_plot.analysis import (
    AnalysisSettings,
    add_fdr_adjustment,
    adjust_p_values,
    calculate_correlations,
    calculate_leave_one_out_influence,
    prepare_numeric_features,
    read_input_file,
    run_analysis,
    validate_and_align_samples,
)


class InputPreparationTests(unittest.TestCase):
    def test_csv_loading_and_censored_value_handling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text(
                "sample,group,afp\nA,case,1.0\nB,control,<2.0\nC,case,\n",
                encoding="utf-8",
            )
            dataframe = read_input_file(path)

        prepared, report = prepare_numeric_features(
            dataframe, censor_strategy="half_limit"
        )

        self.assertEqual(prepared.columns.tolist(), ["sample", "afp"])
        self.assertAlmostEqual(prepared.loc[1, "afp"], 1.0)
        self.assertTrue(np.isnan(prepared.loc[2, "afp"]))
        self.assertEqual(report.excluded_categorical_columns, ("group",))
        self.assertEqual(report.censored_values_by_column, {"afp": 1})

    def test_mixed_unsupported_values_fail_loudly(self) -> None:
        dataframe = pd.DataFrame(
            {"sample": ["A", "B", "C"], "value": [1.0, "unknown", 3.0]}
        )
        with self.assertRaisesRegex(ValueError, "mixes numeric"):
            prepare_numeric_features(dataframe)

    def test_alignment_uses_identifiers_not_row_order(self) -> None:
        x_data = pd.DataFrame({"id": ["A", "B"], "x": [1.0, 2.0]})
        y_data = pd.DataFrame({"sample": ["B", "A"], "y": [20.0, 10.0]})
        aligned_x, aligned_y = validate_and_align_samples(x_data, y_data)

        self.assertEqual(aligned_x["id"].tolist(), ["A", "B"])
        self.assertEqual(aligned_y["sample"].tolist(), ["A", "B"])
        self.assertEqual(aligned_y["y"].tolist(), [10.0, 20.0])

    def test_duplicate_identifiers_are_rejected(self) -> None:
        x_data = pd.DataFrame({"id": ["A", "A"], "x": [1.0, 2.0]})
        y_data = pd.DataFrame({"id": ["A", "B"], "y": [1.0, 2.0]})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_and_align_samples(x_data, y_data)


class CorrelationTests(unittest.TestCase):
    def test_known_pearson_value_and_sample_size(self) -> None:
        x_data = pd.DataFrame({"id": list("ABCD"), "x": [1.0, 2.0, 3.0, 4.0]})
        y_data = pd.DataFrame({"id": list("ABCD"), "y": [2.0, 4.0, 6.0, 8.0]})
        result = calculate_correlations(y_data, x_data)

        self.assertAlmostEqual(result.correlations.loc["y", "x"], 1.0)
        self.assertAlmostEqual(result.p_values.loc["y", "x"], 0.0)
        self.assertEqual(result.sample_sizes.loc["y", "x"], 4)

    def test_same_file_correlations_have_valid_diagonal(self) -> None:
        data = pd.DataFrame(
            {
                "id": list("ABCD"),
                "a": [1.0, 2.0, 3.0, 4.0],
                "b": [4.0, 1.0, 3.0, 2.0],
            }
        )
        result = calculate_correlations(data, data)

        self.assertAlmostEqual(result.correlations.loc["a", "a"], 1.0)
        self.assertAlmostEqual(result.correlations.loc["b", "b"], 1.0)
        self.assertAlmostEqual(result.p_values.loc["a", "a"], 0.0)

    def test_missing_and_constant_inputs_are_reported_without_crashing(self) -> None:
        x_data = pd.DataFrame(
            {"id": list("ABCD"), "x": [1.0, np.nan, 3.0, 4.0], "constant": 2.0}
        )
        y_data = pd.DataFrame({"id": list("ABCD"), "y": [1.0, 2.0, 3.0, 4.0]})
        result = calculate_correlations(y_data, x_data, minimum_samples=3)

        self.assertEqual(result.sample_sizes.loc["y", "x"], 3)
        self.assertTrue(np.isfinite(result.correlations.loc["y", "x"]))
        self.assertTrue(np.isnan(result.correlations.loc["y", "constant"]))
        self.assertTrue(np.isnan(result.p_values.loc["y", "constant"]))

    def test_leave_one_out_influence_is_zero_for_exact_linear_data(self) -> None:
        x_data = pd.DataFrame({"id": list("ABCDE"), "x": range(5)})
        y_data = pd.DataFrame({"id": list("ABCDE"), "y": range(0, 10, 2)})
        result = calculate_correlations(y_data, x_data)
        influence = calculate_leave_one_out_influence(y_data, x_data, result)

        self.assertAlmostEqual(influence.loc["y", "x"], 0.0)


class MultipleTestingTests(unittest.TestCase):
    def test_global_fdr_handles_nan_zero_and_one(self) -> None:
        p_values = pd.DataFrame([[0.0, 0.04], [np.nan, 1.0]])
        adjusted = adjust_p_values(p_values, scope="global")
        expected = false_discovery_control(np.array([0.0, 0.04, 1.0]))

        self.assertAlmostEqual(adjusted.iloc[0, 0], expected[0])
        self.assertAlmostEqual(adjusted.iloc[0, 1], expected[1])
        self.assertTrue(np.isnan(adjusted.iloc[1, 0]))
        self.assertAlmostEqual(adjusted.iloc[1, 1], expected[2])

    def test_fdr_result_preserves_raw_values_and_sample_sizes(self) -> None:
        x_data = pd.DataFrame({"id": list("ABCD"), "x": [1.0, 2.0, 3.0, 4.0]})
        y_data = pd.DataFrame({"id": list("ABCD"), "y": [2.0, 4.0, 6.0, 8.0]})
        raw = calculate_correlations(y_data, x_data)
        adjusted = add_fdr_adjustment(raw)

        pd.testing.assert_frame_equal(raw.p_values, adjusted.p_values)
        pd.testing.assert_frame_equal(raw.sample_sizes, adjusted.sample_sizes)
        self.assertIsNotNone(adjusted.adjusted_p_values)


class OutputTests(unittest.TestCase):
    def test_default_run_writes_only_three_files(self) -> None:
        x_data = pd.DataFrame({"id": list("ABCDE"), "x": range(5)})
        y_data = pd.DataFrame({"id": list("ABCDE"), "y": range(0, 10, 2)})

        for apply_fdr, significance_file in (
            (False, "p_value_data.csv"),
            (True, "adjusted_p_value_data.csv"),
        ):
            with self.subTest(apply_fdr=apply_fdr), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                run_analysis(
                    x_data,
                    y_data,
                    output_directory=output,
                    x_axis_label="X",
                    y_axis_label="Y",
                    settings=AnalysisSettings(apply_fdr=apply_fdr),
                )
                self.assertEqual(
                    {path.name for path in output.iterdir()},
                    {
                        "correlation_data.csv",
                        significance_file,
                        "correlation_heatmap.png",
                    },
                )

    def test_run_analysis_writes_reproducibility_outputs(self) -> None:
        x_data = pd.DataFrame(
            {"id": list("ABCDE"), "group": ["a", "a", "b", "b", "b"], "x": range(5)}
        )
        y_data = pd.DataFrame(
            {"id": list("ABCDE"), "group": ["a", "a", "b", "b", "b"], "y": range(0, 10, 2)}
        )
        settings = AnalysisSettings(
            apply_fdr=True,
            calculate_influence=True,
            detailed_outputs=True,
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            run_analysis(
                x_data,
                y_data,
                output_directory=output,
                x_axis_label="X",
                y_axis_label="Y",
                settings=settings,
            )
            expected_files = {
                "correlation_data.csv",
                "p_value_data.csv",
                "adjusted_p_value_data.csv",
                "sample_size_data.csv",
                "correlation_heatmap.png",
                "analysis_metadata.json",
                "x_feature_diagnostics.csv",
                "y_feature_diagnostics.csv",
                "max_leave_one_out_delta_data.csv",
            }
            self.assertEqual(
                {path.name for path in output.iterdir()}, expected_files
            )


if __name__ == "__main__":
    unittest.main()
