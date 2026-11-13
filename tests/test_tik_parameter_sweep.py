from decimal import Decimal
import unittest

from research.redshift.independent_benchmarks import (
    CHOU_2010_HOLDOUT, PTB_2025_CALIBRATION, ZHENG_2023_TRAINING,
    zheng_training_summary,
)
from research.redshift.tik_parameter_sweep import (
    TIKHeightProfile, build_reference_state, calculate_profile_contrast,
    calibrate_profile_to_independent_data, run_default_parameter_sweep,
    state_at_height, sweep_two_point_parameters,
)

D = Decimal


class TIKParameterSweepTests(unittest.TestCase):
    def test_training_dataset_contains_fourteen_published_runs(self):
        summary = zheng_training_summary()
        self.assertEqual(summary["run_count"], 14)
        self.assertGreater(summary["weighted_gradient_1e19_per_cm"], 12.0)
        self.assertGreater(summary["total_sigma_1e19_per_cm"], summary["statistical_sigma_1e19_per_cm"])

    def test_independent_holdout_and_calibration_are_distinct_experiments(self):
        self.assertEqual(ZHENG_2023_TRAINING.role, "TRAINING")
        self.assertEqual(PTB_2025_CALIBRATION.role, "EXTERNAL_CALIBRATION")
        self.assertEqual(CHOU_2010_HOLDOUT.role, "INDEPENDENT_HOLDOUT")
        self.assertNotEqual(PTB_2025_CALIBRATION.source_doi, CHOU_2010_HOLDOUT.source_doi)

    def test_profile_calibrates_ptb_and_predicts_chou_holdout(self):
        result = calibrate_profile_to_independent_data(
            baseline_transmission_probability=0.25,
            return_model="linear",
            return_coefficient=0.25,
        )
        self.assertAlmostEqual(
            result.external_calibration_prediction,
            result.external_calibration_observed,
            delta=1e-27,
        )
        self.assertAlmostEqual(result.holdout_prediction / result.holdout_observed, 0.995, delta=0.01)
        self.assertLess(abs(result.holdout_residual_sigma), 0.1)
        self.assertLessEqual(result.transmission_probability_at_holdout_height, 1.0)
        self.assertGreaterEqual(result.transmission_probability_at_holdout_height, 0.0)
        self.assertEqual(result.status["transmission_gradient"], "FITTED_ON_PTB_2025")

    def test_multiple_return_families_fit_calibration_but_are_not_discriminated(self):
        rows = run_default_parameter_sweep()
        self.assertEqual(len(rows), 28)
        self.assertTrue(all(abs(row.holdout_residual_sigma) < 0.1 for row in rows))
        self.assertEqual({row.return_model for row in rows}, {"linear", "power", "saturating"})

    def test_two_point_parameter_sweep_changes_return_contrast(self):
        rows = sweep_two_point_parameters()
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row.normalized_contrast != "0" for row in rows))
        by_name = {row.parameter: row for row in rows}
        self.assertIn("transmission_probability", by_name)
        self.assertIn("return_channel_coverage_fraction", by_name)

    def test_height_profile_rejects_probability_outside_unit_interval(self):
        base = build_reference_state()
        profile = TIKHeightProfile(base, D("-1"))
        with self.assertRaises(ValueError):
            state_at_height(profile, D("1"))

    def test_common_energy_scale_cancels_in_normalized_profile_contrast(self):
        base_a = build_reference_state(event_energy_j=D("1e-147"))
        base_b = build_reference_state(event_energy_j=D("1e-140"))
        profile_a = TIKHeightProfile(base_a, D("-0.0001"))
        profile_b = TIKHeightProfile(base_b, D("-0.0001"))
        contrast_a = calculate_profile_contrast(
            profile_a, D("0"), D("0.01")
        ).normalized_contrast
        contrast_b = calculate_profile_contrast(
            profile_b, D("0"), D("0.01")
        ).normalized_contrast
        self.assertAlmostEqual(float(contrast_a), float(contrast_b), places=12)

    def test_common_return_channel_scale_cancels_when_same_at_both_points(self):
        base_a = build_reference_state(return_channel_coverage_fraction=D("0.25"))
        base_b = build_reference_state(return_channel_coverage_fraction=D("1"))
        profile_a = TIKHeightProfile(base_a, D("-0.0001"))
        profile_b = TIKHeightProfile(base_b, D("-0.0001"))
        x_a = calculate_profile_contrast(profile_a, D("0"), D("0.01")).normalized_contrast
        x_b = calculate_profile_contrast(profile_b, D("0"), D("0.01")).normalized_contrast
        self.assertAlmostEqual(float(x_a), float(x_b), places=12)


if __name__ == "__main__":
    unittest.main()
