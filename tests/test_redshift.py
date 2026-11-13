import unittest
from research.redshift import (
    PUBLISHED_BENCHMARKS, RedshiftObservation, fit_redshift_models,
    predict_from_reference_shift, predict_from_return_flow_contrast,
)

class RedshiftModelTests(unittest.TestCase):
    def test_published_benchmarks_keep_sources_and_uncertainties(self):
        self.assertEqual(len(PUBLISHED_BENCHMARKS), 2)
        self.assertTrue(all(item.source_url and item.source_doi for item in PUBLISHED_BENCHMARKS))
        self.assertTrue(all(item.sigma > 0 for item in PUBLISHED_BENCHMARKS))
        self.assertEqual({item.input_kind for item in PUBLISHED_BENCHMARKS}, {"reference_potential_shift"})

    def test_linear_reference_control(self):
        result = predict_from_reference_shift(2e-15, coefficient=1.1)
        self.assertAlmostEqual(result.fractional_shift, 2.2e-15)
        self.assertEqual(result.input_kind, "reference_potential_shift")

    def test_tik_return_flow_bridge_is_dimensionless(self):
        result = predict_from_return_flow_contrast(2.0, 4.0, coefficient=3.0, exponent=2.0)
        self.assertAlmostEqual(result.fractional_shift, 0.75)
        self.assertEqual(result.input_kind, "return_flow_contrast")

    def test_tik_bridge_preserves_sign(self):
        result = predict_from_return_flow_contrast(-2.0, 4.0)
        self.assertAlmostEqual(result.fractional_shift, -0.5)

    def test_zero_return_flow_contrast_means_zero_shift(self):
        self.assertEqual(predict_from_return_flow_contrast(0.0, 10.0).fractional_shift, 0.0)

    def test_linear_fit_recovers_synthetic_coefficient(self):
        data = [RedshiftObservation(str(i), x, 1.25*x, 0.01, "synthetic") for i, x in enumerate((1.0, 2.0, 3.0))]
        fits = fit_redshift_models(data, input_scale=1.0, output_scale=1.0,
            coefficient_grid=(1.0, 1.25, 1.5), exponent_grid=(0.8, 1.0, 1.2), complexity_penalty=0.0)
        best_linear = next(item for item in fits if item.model_name == "linear")
        self.assertEqual(best_linear.parameters["coefficient"], 1.25)
        self.assertAlmostEqual(best_linear.chi_squared, 0.0)
        self.assertEqual(best_linear.sufficiency, "EXPLORATORY")

    def test_real_benchmark_fit_is_explicitly_underdetermined(self):
        fits = fit_redshift_models(PUBLISHED_BENCHMARKS)
        self.assertTrue(fits)
        self.assertTrue(all(item.sufficiency == "UNDERDETERMINED" for item in fits))
        self.assertTrue(all(item.input_kind == "reference_potential_shift" for item in fits))

    def test_invalid_uncertainty_and_mixed_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            fit_redshift_models([RedshiftObservation("a", 1.0, 1.0, 0.0, "x"), RedshiftObservation("b", 2.0, 2.0, 1.0, "x")])
        with self.assertRaises(ValueError):
            fit_redshift_models([RedshiftObservation("a", 1.0, 1.0, 1.0, "potential"), RedshiftObservation("b", 2.0, 2.0, 1.0, "return_flow")])

    def test_nonpositive_reference_density_is_rejected(self):
        with self.assertRaises(ValueError):
            predict_from_return_flow_contrast(1.0, 0.0)

if __name__ == "__main__":
    unittest.main()
