import unittest
from decimal import Decimal as D

from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine.tik_adapter import TIKPairObservation, fit_tik_pairs


def state(transmission):
    return TIKLocalStateInputs(
        tik=ModelInputs(
            observation_volume_m3=D("10"),
            active_cell_count=2,
            cell_volume_m3=D("2"),
            transmission_probability=D(str(transmission)),
            event_energy_j=D("1e-120"),
        ),
        return_channel_coverage_fraction=D("0.75"),
        return_probability=D("0.8"),
        return_efficiency=D("0.9"),
        return_reference_power_density_w_m3=D("1e-10"),
    )


class TIKAdaptiveAdapterTests(unittest.TestCase):
    def setUp(self):
        self.observations = (
            TIKPairObservation("pair-1", state(0.9), state(0.8), 0.1),
            TIKPairObservation("pair-2", state(0.8), state(0.6), 0.2),
            TIKPairObservation("pair-3", state(0.7), state(0.4), 0.3),
        )

    def test_end_to_end_search_runs_real_tik_and_return_flow(self):
        result = fit_tik_pairs(
            self.observations,
            return_models=("linear", "power"),
            return_coefficients=(0.5, 1.0),
            return_exponents=(1.0, 1.5),
            response_formulas=("linear", "power"),
        )
        self.assertEqual(result.observation_count, 3)
        self.assertEqual(len(result.alternatives), 5)
        self.assertIn(result.selected.return_model, ("linear", "power"))
        self.assertIn(result.selected.response.formula, ("linear", "power"))
        self.assertGreaterEqual(result.selected.response.weighted_rmse, 0.0)

    def test_search_is_repeatable(self):
        kwargs = dict(
            return_models=("linear",),
            return_coefficients=(0.5, 1.0),
            response_formulas=("linear",),
        )
        self.assertEqual(fit_tik_pairs(self.observations, **kwargs),
                         fit_tik_pairs(self.observations, **kwargs))

    def test_requires_two_unique_observations(self):
        with self.assertRaises(ValueError):
            fit_tik_pairs(self.observations[:1])
        duplicate = (self.observations[0], self.observations[0])
        with self.assertRaises(ValueError):
            fit_tik_pairs(duplicate)

    def test_invalid_search_parameters_rejected(self):
        with self.assertRaises(ValueError):
            fit_tik_pairs(self.observations, return_coefficients=(0.0,))


if __name__ == "__main__":
    unittest.main()
