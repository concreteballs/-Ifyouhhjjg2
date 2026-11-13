from decimal import Decimal
import unittest

from research.tik0 import ModelInputs, calibrate_event_energy, calculate, planck_scales


class Tik0ModelTests(unittest.TestCase):
    def test_planck_scales_are_in_expected_order_of_magnitude(self):
        scales = planck_scales()
        self.assertTrue(Decimal("5.3e-44") < scales.time_s < Decimal("5.5e-44"))
        self.assertTrue(Decimal("1.6e-35") < scales.length_m < Decimal("1.7e-35"))
        self.assertTrue(Decimal("4.0e-105") < scales.volume_m3 < Decimal("4.5e-105"))
        self.assertTrue(Decimal("1.8e9") < scales.energy_j < Decimal("2.1e9"))

    def test_one_cell_rate_matches_planck_baseline(self):
        result = calculate(ModelInputs(Decimal("1e-30"), Decimal("1")))
        self.assertEqual(result.event_rate_per_m3_s, planck_scales().event_rate_per_m3_s)

    def test_grouping_is_strictly_additive(self):
        one = calculate(ModelInputs(Decimal("2e-30"), Decimal("0.25"), 1))
        two = calculate(ModelInputs(Decimal("2e-30"), Decimal("0.25"), 2))
        self.assertEqual(two.event_rate_per_m3_s, one.event_rate_per_m3_s * 2)
        self.assertEqual(two.power_density_w_m3, one.power_density_w_m3 * 2)

    def test_event_energy_is_independent_of_rest_mass(self):
        energy = Decimal("3.2e-40")
        result = calculate(ModelInputs(energy, Decimal("0.5")))
        self.assertEqual(result.power_density_w_m3, result.event_rate_per_m3_s * energy)

    def test_tik_is_optional_until_reference_is_supplied(self):
        incomplete = calculate(ModelInputs(Decimal("1e-40"), Decimal("1")))
        self.assertIsNone(incomplete.tik0)
        complete = calculate(ModelInputs(Decimal("1e-40"), Decimal("1"), 1, Decimal("1e5")))
        self.assertEqual(complete.tik0, complete.power_density_w_m3 / Decimal("1e5"))

    def test_calibration_reproduces_target_but_is_not_validation(self):
        target = Decimal("2.5e-8")
        epsilon = calibrate_event_energy(target, Decimal("0.8"), 3)
        result = calculate(ModelInputs(epsilon, Decimal("0.8"), 3, target))
        self.assertAlmostEqual(float(result.tik0), 1.0, places=12)

    def test_invalid_probability_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate(ModelInputs(Decimal("1e-30"), Decimal("1.01")))

    def test_zero_transmission_cannot_be_used_for_calibration(self):
        with self.assertRaises(ValueError):
            calibrate_event_energy(Decimal("1"), Decimal("0"))

    def test_non_positive_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate(ModelInputs(Decimal("1e-30"), Decimal("1"), 1, Decimal("0")))


if __name__ == "__main__":
    unittest.main()
