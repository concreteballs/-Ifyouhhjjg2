import unittest
from decimal import Decimal as D

from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine.tik_adapter import TIKPairObservation
from research.adaptive_engine.transfer_engine import ProcessProfile, DatasetRole
from research.adaptive_engine.tik_research_pipeline import TIKResearchObservation, fit_tik_research_dataset
from research.adaptive_engine.tik_transfer_search import (
    TIKTransferRule, propose_tik_component_hints, combine_tik_transfer_hints,
    search_tik_transfer_candidates,
)


def state(probability):
    return TIKLocalStateInputs(
        tik=ModelInputs(D("10"), 2, D("2"), D(str(probability)), D("1e-120")),
        return_channel_coverage_fraction=D("0.75"),
        return_probability=D("0.8"), return_efficiency=D("0.9"),
        return_reference_power_density_w_m3=D("1e-10"),
    )


def profile(pid, family="tik-paired", source="", functional=("paired_contrast",),
            capabilities=("return_response",)):
    return ProcessProfile(
        pid, family, ("paired_locations",), functional, ("same_protocol",),
        ("steady_state",), (("transmission", "fraction"),),
        (("observed_delta", "dimensionless"),),
        (("transmission", 0.0, 1.0),), capabilities, source_id=source,
    )


def observation(oid, group, source, delta, a, b, prof=None):
    pair = TIKPairObservation(oid, state(a), state(b), delta)
    return TIKResearchObservation(pair, group, prof or profile(oid, source=source))


class TIKTransferSearchTests(unittest.TestCase):
    def make_dataset(self):
        partial_a = profile("partial-a", "glider-process", "partial-source-a",
                            capabilities=("return_response",))
        partial_b = profile("partial-b", "robot-process", "partial-source-b",
                            capabilities=("return_response",))
        return (
            observation("fit-a", "train-a", "fit-source-a", 0.1, 0.9, 0.8),
            observation("fit-b", "train-b", "fit-source-b", 0.2, 0.8, 0.6),
            observation("hold", "test", "hold-source", 0.3, 0.7, 0.4),
            observation("partial-a", "transfer-a", "partial-source-a", 0.2, 0.45, 0.4, partial_a),
            observation("partial-b", "transfer-b", "partial-source-b", 0.2, 0.65, 0.6, partial_b),
        )

    def test_component_hints_require_explicit_component_and_rule(self):
        data = self.make_dataset()
        rules = (TIKTransferRule("transmission-map", "return_response",
                                 "transmission_probability", "transmission_probability"),)
        hints = propose_tik_component_hints(
            data[3:], rules, transferable_components={"partial-a": ("return_response",),
                                                       "partial-b": ("other",)})
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].source_observation_id, "partial-a")
        self.assertEqual(hints[0].candidate_values, (0.45,))

    def test_multiple_analogues_combine_into_deterministic_candidates(self):
        data = self.make_dataset()
        rules = (TIKTransferRule("transmission-map", "return_response",
                                 "transmission_probability", "transmission_probability"),)
        hints = propose_tik_component_hints(
            data[3:], rules, transferable_components={"partial-a": ("return_response",),
                                                       "partial-b": ("return_response",)})
        first = combine_tik_transfer_hints(hints, ("fit-a", "fit-b"), max_candidates=4)
        second = combine_tik_transfer_hints(tuple(reversed(hints)), ("fit-b", "fit-a"),
                                            max_candidates=4)
        self.assertEqual(len(first), 2)
        self.assertEqual([x.grids for x in first], [x.grids for x in second])
        self.assertEqual(len(first[0].proposal_ids), 2)

    def test_candidate_bound_is_enforced(self):
        data = self.make_dataset()
        rules = (TIKTransferRule("map", "return_response", "transmission_probability",
                                 "transmission_probability", multipliers=(1.0, 2.0)),)
        hints = propose_tik_component_hints(
            data[3:], rules, transferable_components={"partial-a": ("return_response",),
                                                       "partial-b": ("return_response",)})
        with self.assertRaises(ValueError):
            combine_tik_transfer_hints(hints, ("fit-a",), max_candidates=1)

    def test_partial_hints_fit_only_training_and_score_frozen_holdout(self):
        data = self.make_dataset()
        baseline = fit_tik_research_dataset(
            data, reference_profile=profile("reference"),
            fit_group_ids=("train-a", "train-b"), holdout_group_ids=("test",),
            return_models=("linear",), return_coefficients=(1.0,),
            response_formulas=("linear",),
        )
        self.assertEqual(baseline.roles[3].role, DatasetRole.PARTIAL_TRANSFER)
        rules = (TIKTransferRule("transmission-map", "return_response",
                                 "transmission_probability", "transmission_probability"),)
        result = search_tik_transfer_candidates(
            data, baseline, rules, max_candidates=4,
            return_models=("linear",), return_coefficients=(1.0,),
            response_formulas=("linear",),
        )
        self.assertEqual(len(result.proposals), 2)
        self.assertEqual(len(result.evaluations), 2)
        for evaluation in result.evaluations:
            self.assertEqual(evaluation.fit.observation_count, 2)
            self.assertEqual(evaluation.holdout.observation_count, 1)
            self.assertEqual(tuple(p.observation_id for p in evaluation.holdout.predictions), ("hold",))

    def test_reverse_component_mapping_is_independent(self):
        data = self.make_dataset()
        forward = TIKTransferRule("forward", "return_response",
                                  "transmission_probability", "transmission_probability")
        reverse = TIKTransferRule("reverse", "different_component",
                                  "return_probability", "return_probability")
        hints = propose_tik_component_hints(
            data[3:], (forward, reverse),
            transferable_components={"partial-a": ("return_response",),
                                      "partial-b": ("different_component",)})
        self.assertEqual({h.rule_id for h in hints}, {"forward", "reverse"})
        self.assertEqual({h.component for h in hints}, {"return_response", "different_component"})


if __name__ == "__main__":
    unittest.main()
