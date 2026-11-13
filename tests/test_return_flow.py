from decimal import Decimal
import unittest
from research.return_flow import FitObservation, ReturnFlowInputs, calculate_return_flow, fit_models
from research.return_flow.model import dynamic_relaxation, return_fraction

D = Decimal

class ReturnFlowModelTests(unittest.TestCase):
    def test_linear_return_flow_and_energy_accounting(self):
        result = calculate_return_flow(ReturnFlowInputs(D("10"), D("0.5"), D("0.8"), D("0.5"), D("10")), model_name="linear", coefficient=D("0.5"))
        self.assertEqual(result.normalized_load, D("1"))
        self.assertEqual(result.return_fraction, D("0.1"))
        self.assertEqual(result.returned_power_density_w_m3, D("1.0"))
        self.assertEqual(result.retained_power_density_w_m3, D("9.0"))

    def test_saturating_curve_is_bounded_and_monotonic(self):
        values = [return_fraction(D(str(x)), "saturating", D("2")) for x in (0, 0.5, 1, 2, 5)]
        self.assertEqual(values[0], D(0))
        self.assertTrue(all(a <= b for a, b in zip(values, values[1:])))
        self.assertTrue(all(D(0) <= value <= D(1) for value in values))

    def test_dynamic_relaxation_moves_toward_target(self):
        value = dynamic_relaxation(0.0, 0.8, 2.0, 1.0)
        self.assertGreater(value, 0.0)
        self.assertLess(value, 0.8)

    def test_fit_recovers_synthetic_linear_coefficient(self):
        data = [FitObservation(x, min(1.0, 0.5 * x)) for x in (0.2, 0.4, 0.8, 1.2)]
        linear = next(item for item in fit_models(data, coefficient_grid=(0.25, 0.5, 1.0)) if item.model_name == "linear")
        self.assertEqual(linear.parameters["coefficient"], 0.5)
        self.assertAlmostEqual(linear.rmse, 0.0)

    def test_fit_ranks_exact_power_curve(self):
        data = [FitObservation(x, min(1.0, 0.25 * (x ** 2.0))) for x in (0.2, 0.4, 0.8, 1.2)]
        fits = fit_models(data, coefficient_grid=(0.25, 0.5, 1.0), exponent_grid=(1.0, 2.0))
        self.assertEqual(fits[0].model_name, "power")
        self.assertEqual(fits[0].parameters, {"coefficient": 0.25, "exponent": 2.0})
        self.assertAlmostEqual(fits[0].rmse, 0.0)

    def test_dynamic_candidate_requires_time_data(self):
        fits = fit_models([FitObservation(0.1, 0.05), FitObservation(0.2, 0.1)])
        self.assertNotIn("dynamic_saturating", {item.model_name for item in fits})

    def test_fit_is_deterministic_and_penalty_is_optional(self):
        data = [FitObservation(x, 0.2 * x) for x in (0.1, 0.2, 0.3)]
        first, second = fit_models(data), fit_models(data)
        self.assertEqual(first, second)
        penalized = fit_models(data, complexity_penalty=0.01)
        self.assertTrue(all(item.penalized_score >= item.rmse for item in penalized))

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_return_flow(ReturnFlowInputs(D("-1"), D("0.5"), D("0.5")))
        with self.assertRaises(ValueError):
            return_fraction(D("1"), "power", D("1"), exponent=D("0"))

if __name__ == "__main__":
    unittest.main()
