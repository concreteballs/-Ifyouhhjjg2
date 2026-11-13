import json
import tempfile
import unittest
from pathlib import Path
from research.adaptive_engine import (
    Entity, EntitySet, ModelRecord, ModelRegistry, Sample,
    assess_stability, fit_candidates, run_adaptive,
)

class AdaptiveEngineTests(unittest.TestCase):
    def setUp(self):
        self.samples = tuple(Sample(float(x), 2.0 * x + 0.5) for x in range(-4, 5))

    def test_entity_validation_and_extension(self):
        entities = EntitySet((Entity("gain", 2.0, bounds=(0.0, 5.0)), Entity("offset", 0.5)))
        extended = entities.replace_values({"gain": 3.0})
        self.assertEqual(extended.as_dict(), {"gain": 3.0, "offset": 0.5})
        with self.assertRaises(ValueError):
            entities.replace_values({"missing": 1.0})
        with self.assertRaises(ValueError):
            Entity("bad", 8.0, bounds=(0.0, 1.0))

    def test_search_ranks_candidates_and_is_deterministic(self):
        first = fit_candidates(self.samples)
        second = fit_candidates(self.samples)
        self.assertEqual(first, second)
        self.assertEqual(first[0].formula, "linear")
        self.assertLess(first[0].weighted_rmse, 0.2)

    def test_adaptive_facade_and_stability(self):
        entities = EntitySet((Entity("gain", 1.0),))
        result = run_adaptive(self.samples, entities)
        self.assertTrue(result.stability.finite_outputs)
        self.assertEqual(len(result.alternatives), 4)
        report = assess_stability("linear", {"gain": 2.0, "offset": 0.5},
                                  (0.0, 1.0, 2.0), maximum_relative_change=0.01)
        self.assertTrue(report.passed)

    def test_registry_round_trip(self):
        candidate = fit_candidates(self.samples, formulas=("linear",))[0]
        stability = assess_stability(candidate.formula, candidate.parameters, (0.0, 1.0))
        registry = ModelRegistry()
        registry.save(ModelRecord("baseline", candidate, stability, {"purpose": "test"}))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "models.json"
            registry.export_json(path)
            loaded = ModelRegistry(); loaded.load_json(path)
            self.assertEqual(loaded.get("baseline"), registry.get("baseline"))
            self.assertEqual(json.loads(path.read_text()), json.loads(path.read_text()))

    def test_invalid_samples_rejected(self):
        with self.assertRaises(ValueError):
            fit_candidates((Sample(1.0, 2.0),))
        with self.assertRaises(ValueError):
            fit_candidates((Sample(1.0, 2.0, 0.0), Sample(2.0, 3.0)))

if __name__ == "__main__":
    unittest.main()
