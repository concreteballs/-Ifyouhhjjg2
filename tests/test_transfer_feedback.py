import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine.tik_adapter import TIKPairObservation
from research.adaptive_engine.transfer_engine import ProcessProfile
from research.adaptive_engine.tik_research_pipeline import TIKResearchObservation, fit_tik_research_dataset
from research.adaptive_engine.tik_transfer_search import TIKTransferRule, search_tik_transfer_candidates
from research.adaptive_engine.transfer_feedback import (
    TransferFeedbackRegistry, build_transfer_feedback,
)


def state(probability):
    return TIKLocalStateInputs(
        tik=ModelInputs(D("10"), 2, D("2"), D(str(probability)), D("1e-120")),
        return_channel_coverage_fraction=D("0.75"),
        return_probability=D("0.8"), return_efficiency=D("0.9"),
        return_reference_power_density_w_m3=D("1e-10"),
    )


def profile(pid, family="tik-paired", source=""):
    return ProcessProfile(
        pid, family, ("paired_locations",), ("paired_contrast",),
        ("same_protocol",), ("steady_state",),
        (("transmission", "fraction"),), (("observed_delta", "dimensionless"),),
        (("transmission", 0.0, 1.0),), ("return_response",), source_id=source,
    )


def observation(oid, group, source, delta, a, b, prof=None):
    pair = TIKPairObservation(oid, state(a), state(b), delta)
    return TIKResearchObservation(pair, group, prof or profile(oid, source=source))


class TransferFeedbackTests(unittest.TestCase):
    def dataset(self):
        return (
            observation("fit-a", "train-a", "fit-source-a", 0.1, 0.9, 0.8),
            observation("fit-b", "train-b", "fit-source-b", 0.2, 0.8, 0.6),
            observation("hold", "test", "hold-source", 0.3, 0.7, 0.4),
            observation("partial", "transfer", "partial-source", 0.2, 0.45, 0.4,
                        profile("partial", "glider-process", "partial-source")),
        )

    def run_feedback(self):
        data = self.dataset()
        baseline = fit_tik_research_dataset(
            data, reference_profile=profile("reference"),
            fit_group_ids=("train-a", "train-b"), holdout_group_ids=("test",),
            return_models=("linear",), return_coefficients=(1.0,),
            response_formulas=("linear",),
        )
        rule = TIKTransferRule("transmission-map", "return_response",
                               "transmission_probability", "transmission_probability")
        result = search_tik_transfer_candidates(
            data, baseline, (rule,), max_candidates=4,
            return_models=("linear",), return_coefficients=(1.0,),
            response_formulas=("linear",),
        )
        return baseline, result, build_transfer_feedback(result, baseline)

    def test_feedback_compares_same_baseline_and_holdout(self):
        baseline, search, report = self.run_feedback()
        self.assertEqual(report.fit_observation_ids, baseline.fit_observation_ids)
        self.assertEqual(report.holdout_observation_ids, ("hold",))
        self.assertEqual(report.partial_transfer_observation_ids, ("partial",))
        self.assertEqual(len(report.evaluations), len(search.evaluations))
        evaluated_by_id = {item.candidate_id: item for item in search.evaluations}
        for row in report.evaluations:
            evaluated = evaluated_by_id[row.candidate_id]
            self.assertEqual(row.holdout_count, 1)
            self.assertAlmostEqual(
                row.holdout_improvement,
                report.baseline_holdout_score - row.holdout_score,
            )

    def test_unstable_candidates_are_never_marked_as_success(self):
        baseline, search, report = self.run_feedback()
        # The report reflects the candidate's actual stability result.
        evaluated_by_id = {item.candidate_id: item for item in search.evaluations}
        for row in report.evaluations:
            evaluated = evaluated_by_id[row.candidate_id]
            self.assertEqual(row.stable, evaluated.fit.selected.stability.passed)
            if not row.stable:
                self.assertEqual(row.outcome, "unstable")

    def test_registry_round_trip_and_component_statistics(self):
        _, _, report = self.run_feedback()
        registry = TransferFeedbackRegistry()
        registry.record("experiment-001", report)
        self.assertIn("return_response", registry.component_statistics())
        with self.assertRaises(ValueError):
            registry.record("experiment-001", report)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            registry.export_json(path)
            restored = TransferFeedbackRegistry()
            restored.load_json(path)
            self.assertEqual(restored.run_ids(), ("experiment-001",))
            self.assertEqual(restored.get("experiment-001"), report)
            self.assertEqual(restored.component_statistics(), registry.component_statistics())

    def test_registry_rejects_unknown_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema":"unknown","runs":{}}', encoding="utf-8")
            with self.assertRaises(ValueError):
                TransferFeedbackRegistry().load_json(path)


if __name__ == "__main__":
    unittest.main()
