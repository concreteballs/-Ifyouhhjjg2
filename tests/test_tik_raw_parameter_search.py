import unittest
from decimal import Decimal as D
from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine.tik_adapter import TIKPairObservation
from research.adaptive_engine.raw_parameter_search import TIKRawParameterGrid, fit_tik_raw_parameters

def state(transmission, *, cell_count=2, cell_volume="2"):
    return TIKLocalStateInputs(
        tik=ModelInputs(D("10"), cell_count, D(cell_volume), D(str(transmission)), D("1e-120")),
        return_channel_coverage_fraction=D("0.75"), return_probability=D("0.8"),
        return_efficiency=D("0.9"), return_reference_power_density_w_m3=D("1e-10"))

class TIKRawParameterSearchTests(unittest.TestCase):
    def setUp(self):
        self.observations = (
            TIKPairObservation("p1", state(0.9), state(0.8), 0.1),
            TIKPairObservation("p2", state(0.8), state(0.6), 0.2),
            TIKPairObservation("p3", state(0.7), state(0.4), 0.3))

    def fit(self, grids, **kwargs):
        return fit_tik_raw_parameters(self.observations, grids,
            return_models=("linear",), return_coefficients=(0.5, 1.0),
            response_formulas=("linear", "power"), **kwargs)

    def test_search_returns_ranked_candidates_and_is_repeatable(self):
        grids = (
            TIKRawParameterGrid("p1", "state_a", "transmission_probability", (0.7, 0.9)),
            TIKRawParameterGrid("p2", "state_b", "return_efficiency", (0.6, 0.9)))
        first, second = self.fit(grids), self.fit(grids)
        self.assertEqual(first, second)
        self.assertEqual(first.attempted_count, 4)
        self.assertEqual(first.valid_count + first.rejected_count, 4)
        self.assertEqual(len(first.alternatives), first.valid_count - 1)
        self.assertGreaterEqual(first.selected.score, 0.0)

    def test_invalid_geometry_is_skipped_not_fatal(self):
        result = self.fit((TIKRawParameterGrid("p1", "state_a", "active_cell_count", (2, 6)),))
        self.assertEqual(result.attempted_count, 2)
        self.assertEqual(result.rejected_count, 1)
        self.assertEqual(result.valid_count, 1)
        self.assertEqual(result.selected.parameter_values[0][3], "2")

    def test_candidate_budget_prevents_combinatorial_explosion(self):
        grids = (
            TIKRawParameterGrid("p1", "state_a", "transmission_probability", (0.2, 0.4, 0.6)),
            TIKRawParameterGrid("p2", "state_b", "return_efficiency", (0.2, 0.4, 0.6)))
        with self.assertRaises(ValueError):
            self.fit(grids, max_candidates=8)

    def test_dimension_limit_and_unknown_target_rejected(self):
        with self.assertRaises(ValueError):
            self.fit((TIKRawParameterGrid("missing", "state_a", "transmission_probability", (0.5,)),))
        too_many = tuple(TIKRawParameterGrid("p1", "state_a", name, (value,))
            for name, value in (("transmission_probability", 0.5), ("event_energy_j", 1e-120),
                ("cell_volume_m3", 1.0), ("return_probability", 0.5), ("return_efficiency", 0.5)))
        with self.assertRaises(ValueError):
            self.fit(too_many, max_dimensions=4)

    def test_invalid_grid_values_rejected(self):
        with self.assertRaises(ValueError):
            self.fit((TIKRawParameterGrid("p1", "state_a", "active_cell_count", (1.5,)),))
        with self.assertRaises(ValueError):
            self.fit((TIKRawParameterGrid("p1", "state_a", "unknown_field", (1.0,)),))

if __name__ == "__main__":
    unittest.main()
