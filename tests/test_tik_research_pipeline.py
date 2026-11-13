import unittest
from decimal import Decimal as D

from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine.tik_adapter import TIKPairObservation
from research.adaptive_engine.transfer_engine import ProcessProfile, DatasetRole
from research.adaptive_engine.tik_research_pipeline import (
    TIKResearchObservation, fit_tik_research_dataset,
)


def state(probability):
    return TIKLocalStateInputs(
        tik=ModelInputs(D("10"), 2, D("2"), D(str(probability)), D("1e-120")),
        return_channel_coverage_fraction=D("0.75"),
        return_probability=D("0.8"), return_efficiency=D("0.9"),
        return_reference_power_density_w_m3=D("1e-10"),
    )


def profile(pid, family="tik-paired", *, source="", functional=("paired_contrast",),
            capabilities=("return_response",)):
    return ProcessProfile(
        pid, family, ("paired_locations",), functional, ("same_protocol",),
        ("steady_state",), (("transmission", "fraction"),),
        (("observed_delta", "dimensionless"),),
        (("transmission", 0.0, 1.0),), capabilities,
        source_id=source,
    )


def item(oid, group, source, delta, a, b, *, prof=None):
    pair = TIKPairObservation(oid, state(a), state(b), delta)
    return TIKResearchObservation(pair, group, prof or profile(oid, source=source))


class TIKResearchPipelineTests(unittest.TestCase):
    def test_fit_only_and_independent_holdout_evaluated_without_refitting(self):
        reference = profile("reference")
        data = (
            item("fit-1", "train-1", "source-1", 0.1, 0.9, 0.8),
            item("fit-2", "train-2", "source-2", 0.2, 0.8, 0.6),
            item("hold-1", "test-1", "source-3", 0.3, 0.7, 0.4),
        )
        result = fit_tik_research_dataset(
            data, reference_profile=reference,
            fit_group_ids=("train-1", "train-2"),
            holdout_group_ids=("test-1",),
            return_models=("linear",), return_coefficients=(0.5, 1.0),
            response_formulas=("linear",),
        )
        self.assertEqual(result.fit_observation_ids, ("fit-1", "fit-2"))
        self.assertEqual(result.holdout_observation_ids, ("hold-1",))
        self.assertEqual(result.fit.observation_count, 2)
        self.assertEqual(result.holdout.observation_count, 1)
        self.assertEqual(result.roles[2].role, DatasetRole.HOLDOUT)
        self.assertGreaterEqual(result.holdout.weighted_rmse, 0.0)

    def test_partial_process_is_retained_but_not_used_for_fit_or_holdout(self):
        reference = profile("reference")
        partial_profile = profile("partial", family="alternate-process",
            functional=("paired_contrast",), capabilities=("return_response",))
        data = (
            item("fit-1", "train-1", "source-1", 0.1, 0.9, 0.8),
            item("fit-2", "train-2", "source-2", 0.2, 0.8, 0.6),
            item("partial-1", "transfer", "source-3", 0.3, 0.7, 0.4,
                 prof=partial_profile),
        )
        result = fit_tik_research_dataset(
            data, reference_profile=reference,
            fit_group_ids=("train-1", "train-2"),
            holdout_group_ids=(), return_models=("linear",),
            return_coefficients=(1.0,), response_formulas=("linear",),
        )
        self.assertEqual(result.partial_transfer_observation_ids, ("partial-1",))
        self.assertNotIn("partial-1", result.fit_observation_ids)
        self.assertIsNone(result.holdout)

    def test_shared_lineage_cannot_be_used_as_holdout(self):
        reference = profile("reference")
        data = (
            item("fit-1", "train-1", "shared-source", 0.1, 0.9, 0.8),
            item("fit-2", "train-2", "source-2", 0.2, 0.8, 0.6),
            item("leak", "test-1", "shared-source", 0.3, 0.7, 0.4),
        )
        result = fit_tik_research_dataset(
            data, reference_profile=reference,
            fit_group_ids=("train-1", "train-2"),
            holdout_group_ids=("test-1",), return_models=("linear",),
            return_coefficients=(1.0,), response_formulas=("linear",),
        )
        self.assertNotIn("leak", result.holdout_observation_ids)
        self.assertIn("leak", result.unresolved_observation_ids)

    def test_insufficient_fit_observations_is_rejected(self):
        with self.assertRaises(ValueError):
            fit_tik_research_dataset(
                (item("one", "train", "source", 0.1, 0.9, 0.8),),
                reference_profile=profile("ref"), fit_group_ids=("train",),
                holdout_group_ids=(),
            )


if __name__ == "__main__":
    unittest.main()
