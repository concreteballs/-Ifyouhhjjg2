import unittest
from decimal import Decimal as D

from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine.dynamic_adapter import TIKTimeObservation, fit_dynamic_tik_series


def state(probability):
    return TIKLocalStateInputs(
        tik=ModelInputs(D("10"), 2, D("2"), D(str(probability)), D("1e-120")),
        return_channel_coverage_fraction=D("0.75"),
        return_probability=D("0.8"),
        return_efficiency=D("0.9"),
        return_reference_power_density_w_m3=D("1e27"),
    )


class DynamicTIKAdapterTests(unittest.TestCase):
    def setUp(self):
        self.data = (
            TIKTimeObservation("t0", 0.0, state(0.9), 0.10),
            TIKTimeObservation("t1", 1.0, state(0.8), 0.15),
            TIKTimeObservation("t2", 2.5, state(0.6), 0.20),
            TIKTimeObservation("t3", 4.0, state(0.5), 0.25),
        )

    def test_fits_return_curve_and_relaxation_time(self):
        result = fit_dynamic_tik_series(
            self.data,
            return_models=("linear",),
            return_coefficients=(0.5, 1.0),
            time_constants_s=(0.5, 2.0),
            initial_fractions=(0.0, 0.1),
        )
        self.assertEqual(result.selected.observation_count, 4)
        self.assertGreater(result.selected.time_constant_s, 0)
        self.assertGreaterEqual(result.selected.weighted_rmse, 0)
        self.assertEqual(len(result.alternatives), 7)

    def test_search_is_deterministic(self):
        kwargs = dict(
            return_models=("linear",),
            return_coefficients=(0.5,),
            time_constants_s=(1.0, 2.0),
            initial_fractions=(0.0, 0.1),
        )
        self.assertEqual(fit_dynamic_tik_series(self.data, **kwargs),
                         fit_dynamic_tik_series(self.data, **kwargs))

    def test_time_order_and_fraction_validation(self):
        unordered = (
            self.data[1],
            self.data[0],
        )
        with self.assertRaises(ValueError):
            fit_dynamic_tik_series(unordered)
        invalid = (self.data[0], TIKTimeObservation("bad", 1.0, state(0.5), 1.2))
        with self.assertRaises(ValueError):
            fit_dynamic_tik_series(invalid)

    def test_requires_unique_observation_ids(self):
        with self.assertRaises(ValueError):
            fit_dynamic_tik_series((self.data[0], self.data[0]))


if __name__ == "__main__":
    unittest.main()
