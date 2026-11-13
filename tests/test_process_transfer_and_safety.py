import unittest
from research.adaptive_engine.transfer_engine import (
    Applicability, CalibrationPoint, DatasetObservation, DatasetRole,
    ProcessProfile, TaskDefinition, TaskOperation, assess_process_transfer,
    build_applicability_split, cluster_tasks, fit_calibration, plan_skill_transfer,
)
from research.adaptive_engine.safety_gate import (
    AuthorizationStatus, ExecutionRequest, authorize_execution,
)


def profile(pid, family="aviation", capabilities=("energy",), source="", experiment=""):
    return ProcessProfile(pid, family, ("vehicle",), ("trajectory_control",),
        ("airborne",), ("normal",), (("speed", "m/s"),), (("path", "m"),),
        (("speed", 0.0, 100.0),), capabilities, source, experiment)


class AnalogyTests(unittest.TestCase):
    def test_partial_transfer_between_different_families(self):
        a = profile("glider", "glider", ("energy", "thermal_search"))
        b = profile("powered", "powered", ("energy", "engine_control"))
        result = assess_process_transfer(a, b)
        self.assertEqual(result.applicability, Applicability.PARTIAL)
        self.assertEqual(result.transferable_components, ("energy", "trajectory_control"))

    def test_transfer_is_directional_and_reversible_by_reassessment(self):
        a = ProcessProfile("a", "glider", ("vehicle",), ("trajectory_control",),
            ("airborne",), ("normal",), (("speed", "m/s"),), (("path", "m"),),
            (("speed", 0.0, 100.0),), ("energy", "attitude_recovery"))
        b = ProcessProfile("b", "powered", ("vehicle",), ("trajectory_control",),
            ("airborne",), ("normal",), (("speed", "m/s"),), (("path", "m"),),
            (("speed", 0.0, 100.0),), ("aerobatic_control",), required_components=("energy",))
        ab = assess_process_transfer(a, b)
        ba = assess_process_transfer(b, a)
        self.assertEqual(ab.source_id, "a")
        self.assertEqual(ba.source_id, "b")
        self.assertNotEqual(ab.transferable_components, ba.transferable_components)

    def test_unknown_profile_is_not_promoted(self):
        sparse = ProcessProfile("sparse", "unknown")
        self.assertEqual(assess_process_transfer(sparse, profile("ref")).applicability,
                         Applicability.UNKNOWN)

    def test_holdout_requires_independent_lineage(self):
        ref = profile("ref", source="A", experiment="run-A")
        same = profile("same", source="A", experiment="run-A")
        other = profile("other", source="B", experiment="run-B")
        roles = build_applicability_split(ref, (
            DatasetObservation("fit", "train", ref),
            DatasetObservation("leak", "test1", same),
            DatasetObservation("valid", "test2", other),
        ), fit_group_ids=("train",), holdout_group_ids=("test1", "test2"),
           model_family="m")
        self.assertEqual([x.role for x in roles],
            [DatasetRole.FIT, DatasetRole.UNRESOLVED, DatasetRole.HOLDOUT])


    def test_holdout_is_checked_against_all_fit_lineage_not_only_reference(self):
        reference = profile("reference", source="source-A", experiment="run-A")
        second_fit = profile("second-fit", source="source-B", experiment="run-B")
        leaked_holdout = profile("holdout", source="source-B", experiment="run-C")
        roles = build_applicability_split(reference, (
            DatasetObservation("fit-a", "train-a", reference),
            DatasetObservation("fit-b", "train-b", second_fit),
            DatasetObservation("hold-b", "test-b", leaked_holdout),
        ), fit_group_ids=("train-a", "train-b"), holdout_group_ids=("test-b",),
           model_family="m")
        self.assertEqual(roles[2].role, DatasetRole.UNRESOLVED)

    def test_partial_analogue_is_transfer_only(self):
        ref = profile("ref", capabilities=("grip",))
        other = ProcessProfile("other", "different", ("robot",), ("grasp",),
            ("room",), ("slow",), (("force", "N"),), (("object", "id"),),
            (("force", 0.0, 10.0),), ("grip",))
        role = build_applicability_split(ref, (DatasetObservation("p", "h", other),),
            fit_group_ids=(), holdout_group_ids=("h",), model_family="grasp")[0]
        self.assertEqual(role.role, DatasetRole.PARTIAL_TRANSFER)
        self.assertIn("grip", role.assessment.transferable_components)


class TaskTests(unittest.TestCase):
    def test_cluster_finds_shared_operations_across_related_tasks(self):
        a = TaskDefinition("window", (TaskOperation("step"), TaskOperation("duck")))
        b = TaskDefinition("door", (TaskOperation("step"), TaskOperation("walk")))
        self.assertEqual(cluster_tasks((a, b))[0].reusable_operations, ("step",))

    def test_transfer_plan_adaptation_and_calibration(self):
        a = TaskDefinition("peach", (TaskOperation("grip", tags=("soft",)),
            TaskOperation("close", prerequisites=("grip",))))
        b = TaskDefinition("glass", (TaskOperation("grip", tags=("rigid",), requires_calibration=True),
            TaskOperation("close", prerequisites=("grip",)), TaskOperation("release")))
        plan = plan_skill_transfer(a, b)
        self.assertEqual(plan.transferable_operations, ("close", "grip"))
        self.assertEqual(plan.missing_operations, ("release",))
        self.assertEqual(plan.adaptation_operations, ("grip",))
        self.assertEqual(plan.requires_calibration, ("grip",))

    def test_dependency_cycle_is_rejected(self):
        with self.assertRaises(ValueError):
            TaskDefinition("cycle", (TaskOperation("a", ("b",)), TaskOperation("b", ("a",))))


class CalibrationTests(unittest.TestCase):
    def test_calibration_and_range_gate(self):
        result = fit_calibration((CalibrationPoint(0, 0.1), CalibrationPoint(10, 10.1),
            CalibrationPoint(20, 20.1)), maximum_residual=0.001)
        self.assertTrue(result.accepted)
        self.assertAlmostEqual(result.correct(5.1), 5.0, places=6)
        self.assertTrue(result.valid_for(2, 18, maximum_residual=0.001))
        self.assertFalse(result.valid_for(-1, 18, maximum_residual=0.001))


class SafetyTests(unittest.TestCase):
    def test_learning_does_not_grant_execution(self):
        request = ExecutionRequest("vehicle-control", "vehicle", 5)
        result = authorize_execution(request, execution_requested=False)
        self.assertEqual(result.status, AuthorizationStatus.KNOWLEDGE_ONLY)
        self.assertTrue(result.knowledge_retained)

    def test_critical_sabotage_is_denied_even_with_approvals(self):
        request = ExecutionRequest("shutdown", "critical_infrastructure_sabotage", 5,
            True, True, True, True, True, True)
        self.assertEqual(authorize_execution(request).status, AuthorizationStatus.DENIED)

    def test_physical_action_fails_closed_without_calibration_and_interlock(self):
        request = ExecutionRequest("grip", "robotics", 1, True, True, True,
            physical_actuation=True)
        self.assertEqual(authorize_execution(request).status, AuthorizationStatus.DENIED)

    def test_high_risk_needs_dual_approval_and_sandbox(self):
        request = ExecutionRequest("industrial", "industrial_maintenance", 4,
            authenticated=True, environment_authorized=True, explicit_scope_match=True,
            human_approval=True, second_approver=True, sandboxed=True)
        self.assertEqual(authorize_execution(request).status, AuthorizationStatus.ALLOWED)


if __name__ == "__main__":
    unittest.main()
