from decimal import Decimal
import unittest

from research.tik0 import ModelInputs, TIKLocalStateInputs, calculate_local_state
from research.redshift import (
    predict_from_tik0_local_states,
    redshift_observation_from_tik0_states,
    fit_redshift_models,
)

D = Decimal


def state(*, transmission="0.8", cell_count=2, coverage="0.5", event_energy="3e-30"):
    return TIKLocalStateInputs(
        tik=ModelInputs(
            observation_volume_m3=D("10"),
            active_cell_count=cell_count,
            cell_volume_m3=D("2"),
            transmission_probability=D(transmission),
            event_energy_j=None if event_energy is None else D(event_energy),
        ),
        return_channel_coverage_fraction=D(coverage),
        return_probability=D("0.5"),
        return_efficiency=D("0.8"),
        return_reference_power_density_w_m3=D("1e5"),
    )


class TIKLocalStateTests(unittest.TestCase):
    def test_local_state_connects_tik_power_to_return_flow(self):
        result = calculate_local_state(state())
        self.assertEqual(
            result.return_flow.returned_power_density_w_m3
            + result.return_flow.retained_power_density_w_m3,
            result.tik.power_density_w_m3,
        )
        self.assertEqual(result.parameter_status["active_volume_fraction_applied_once"], "DERIVED")

    def test_tik_active_fraction_is_not_applied_twice(self):
        full_coverage = calculate_local_state(state(coverage="1"))
        half_coverage = calculate_local_state(state(coverage="0.5"))
        self.assertEqual(
            full_coverage.return_flow.returned_power_density_w_m3,
            half_coverage.return_flow.returned_power_density_w_m3 * 2,
        )

    def test_more_tik_active_cells_raise_incoming_and_returned_power(self):
        one = calculate_local_state(state(cell_count=1))
        two = calculate_local_state(state(cell_count=2))
        self.assertEqual(
            two.tik.power_density_w_m3,
            one.tik.power_density_w_m3 * 2,
        )
        self.assertEqual(
            two.return_flow.returned_power_density_w_m3,
            one.return_flow.returned_power_density_w_m3 * 2,
        )

    def test_missing_event_energy_is_rejected_for_bridge(self):
        with self.assertRaises(ValueError):
            calculate_local_state(state(event_energy=None))

    def test_zero_event_energy_produces_zero_return_power(self):
        result = calculate_local_state(state(event_energy="0"))
        self.assertEqual(result.return_flow.returned_power_density_w_m3, D("0"))

    def test_invalid_return_channel_geometry_is_rejected(self):
        invalid = state(coverage="1.2")
        with self.assertRaises(ValueError):
            calculate_local_state(invalid)

    def test_end_to_end_prediction_uses_two_local_tik_states(self):
        a, b = state(transmission="0.8"), state(transmission="0.4")
        prediction = predict_from_tik0_local_states(
            a, b, redshift_reference_power_density_w_m3=1e5,
            redshift_coefficient=2.0, redshift_exponent=1.0,
        )
        self.assertEqual(prediction.input_kind, "tik0_local_state_contrast")
        self.assertGreater(prediction.fractional_shift, 0)

    def test_observation_builder_and_fit_keep_tik_input_separate(self):
        a, b = state(transmission="0.8"), state(transmission="0.4")
        observation = redshift_observation_from_tik0_states(
            "synthetic-clock-pair", a, b,
            observed_fractional_shift=2e-12, sigma=1e-13,
            redshift_reference_power_density_w_m3=1e5,
            source="synthetic test data",
        )
        self.assertEqual(observation.input_kind, "tik0_local_state_contrast")
        fits = fit_redshift_models(
            [observation, observation.__class__(
                "synthetic-clock-pair-2", observation.x * 2,
                observation.y * 2, observation.sigma,
                observation.input_kind, source="synthetic test data"
            )],
            input_scale=1.0, output_scale=1e-12,
            coefficient_grid=(0.5, 1.0, 2.0),
            exponent_grid=(1.0,),
            saturation_rate_grid=(0.5,),
            saturation_cap_grid=(2.0,),
        )
        self.assertTrue(fits)
        self.assertTrue(all(item.input_kind == "tik0_local_state_contrast" for item in fits))

    def test_reference_potential_benchmarks_are_not_used_as_tik_observations(self):
        from research.redshift import PUBLISHED_BENCHMARKS
        self.assertTrue(all(
            item.input_kind == "reference_potential_shift"
            for item in PUBLISHED_BENCHMARKS
        ))


if __name__ == "__main__":
    unittest.main()
