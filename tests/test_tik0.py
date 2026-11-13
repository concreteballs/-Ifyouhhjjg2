from decimal import Decimal
import unittest

from research.tik0 import ModelInputs, calibrate_event_energy, calculate, planck_scales


D = Decimal


def inputs(*, volume="10", count=2, cell_volume="2", probability="0.5", energy="3e-30", reference=None):
    return ModelInputs(
        observation_volume_m3=D(volume),
        active_cell_count=count,
        cell_volume_m3=D(cell_volume),
        transmission_probability=D(probability),
        event_energy_j=None if energy is None else D(energy),
        reference_power_density_w_m3=None if reference is None else D(reference),
    )


class Tik0ModelTests(unittest.TestCase):
    def test_planck_scales_are_in_expected_order_of_magnitude(self):
        scales = planck_scales()
        self.assertTrue(D("5.3e-44") < scales.time_s < D("5.5e-44"))
        self.assertTrue(D("1.6e-35") < scales.length_m < D("1.7e-35"))
        self.assertTrue(D("4.0e-105") < scales.volume_m3 < D("4.5e-105"))
        self.assertTrue(D("1.8e9") < scales.energy_j < D("2.1e9"))

    def test_rate_uses_active_volume_not_bare_cell_count(self):
        result = calculate(inputs(volume="10", count=2, cell_volume="2", probability="0.5", energy=None))
        expected_total = planck_scales().event_rate_per_m3_s * D("0.5") * D("4")
        self.assertEqual(result.total_event_rate_per_s, expected_total)
        self.assertEqual(result.event_rate_density_per_m3_s, expected_total / D("10"))
        self.assertEqual(result.active_volume_fraction, D("0.4"))

    def test_two_disjoint_groups_add_exactly(self):
        one = calculate(inputs(volume="10", count=1, cell_volume="2", energy=None))
        two = calculate(inputs(volume="10", count=2, cell_volume="2", energy=None))
        self.assertEqual(two.total_event_rate_per_s, one.total_event_rate_per_s * 2)

    def test_regrouping_same_cells_changes_nothing(self):
        separate_groups_total = sum(
            (calculate(inputs(volume="10", count=1, cell_volume="1", energy=None)).total_event_rate_per_s for _ in range(4)),
            D(0),
        )
        regrouped = calculate(inputs(volume="10", count=4, cell_volume="1", energy=None))
        self.assertEqual(regrouped.total_event_rate_per_s, separate_groups_total)

    def test_subdivision_of_fixed_active_volume_changes_nothing(self):
        coarse = calculate(inputs(volume="10", count=2, cell_volume="2", energy=None))
        subdivided = calculate(inputs(volume="10", count=4, cell_volume="1", energy=None))
        self.assertEqual(coarse.total_event_rate_per_s, subdivided.total_event_rate_per_s)
        self.assertEqual(coarse.event_rate_density_per_m3_s, subdivided.event_rate_density_per_m3_s)

    def test_scaling_active_and_observation_volumes_preserves_rate_density(self):
        small = calculate(inputs(volume="10", count=2, cell_volume="2", energy=None))
        large = calculate(inputs(volume="20", count=4, cell_volume="2", energy=None))
        self.assertEqual(large.total_event_rate_per_s, small.total_event_rate_per_s * 2)
        self.assertEqual(large.event_rate_density_per_m3_s, small.event_rate_density_per_m3_s)

    def test_active_fraction_scales_rate_density_linearly(self):
        half = calculate(inputs(volume="10", count=1, cell_volume="2", energy=None))
        full = calculate(inputs(volume="10", count=2, cell_volume="2", energy=None))
        self.assertEqual(full.event_rate_density_per_m3_s, half.event_rate_density_per_m3_s * 2)

    def test_energy_and_power_outputs_are_consistent(self):
        result = calculate(inputs(volume="10", count=2, cell_volume="2", probability="0.5", energy="3e-30"))
        self.assertEqual(result.total_power_w, result.total_event_rate_per_s * D("3e-30"))
        self.assertEqual(result.power_density_w_m3, result.total_power_w / D("10"))

    def test_tik_is_optional_and_dimensionless_ratio(self):
        no_reference = calculate(inputs(reference=None))
        self.assertIsNone(no_reference.tik0)
        with_reference = calculate(inputs(reference="1e5"))
        self.assertEqual(with_reference.tik0, with_reference.power_density_w_m3 / D("1e5"))

    def test_calibration_reproduces_target_but_is_not_validation(self):
        target = D("2.5e-8")
        epsilon = calibrate_event_energy(
            target, observation_volume_m3=D("10"), active_cell_count=2,
            cell_volume_m3=D("2"), transmission_probability=D("0.8"),
        )
        fitted = calculate(inputs(volume="10", count=2, cell_volume="2", probability="0.8",
                                  energy=str(epsilon), reference=str(target)))
        self.assertAlmostEqual(float(fitted.power_density_w_m3), float(target), places=18)
        self.assertAlmostEqual(float(fitted.tik0), 1.0, places=12)

    def test_invalid_probability_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate(inputs(probability="1.01"))

    def test_zero_transmission_cannot_be_used_for_calibration(self):
        with self.assertRaises(ValueError):
            calibrate_event_energy(D("1"), D("10"), 1, D("1"), D("0"))

    def test_invalid_geometry_is_rejected(self):
        invalid = [
            inputs(volume="0"),
            inputs(count=0),
            inputs(count=True),
            inputs(cell_volume="0"),
            inputs(volume="3", count=2, cell_volume="2"),
        ]
        for case in invalid:
            with self.subTest(case=case), self.assertRaises(ValueError):
                calculate(case)

    def test_negative_event_energy_and_nonpositive_reference_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate(inputs(energy="-1"))
        with self.assertRaises(ValueError):
            calculate(inputs(reference="0"))


if __name__ == "__main__":
    unittest.main()
