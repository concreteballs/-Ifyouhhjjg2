"""Adaptive search, TIK integration, temporal fitting and model registry."""
from .entities import Entity, EntitySet
from .engine import AdaptiveResult, run_adaptive
from .formulas import FORMULAS, predict
from .optimizer import Candidate, Sample, fit_candidates
from .registry import ModelRecord, ModelRegistry
from .stability import StabilityReport, assess_stability
from .tik_adapter import TIKAdaptiveCandidate, TIKAdaptiveResult, TIKPairObservation, fit_tik_pairs
from .dynamic_adapter import DynamicTIKCandidate, DynamicTIKResult, TIKTimeObservation, fit_dynamic_tik_series
from .raw_parameter_search import TIKRawParameterGrid, TIKRawSearchCandidate, TIKRawSearchResult, fit_tik_raw_parameters
from .tik_research_pipeline import (TIKResearchObservation, TIKHoldoutPrediction, TIKHoldoutReport, TIKResearchResult, fit_tik_research_dataset)
from .tik_transfer_search import (TIKTransferRule, TIKComponentHint, TIKTransferCandidate,
    TIKTransferEvaluation, TIKTransferSearchResult, propose_tik_component_hints,
    combine_tik_transfer_hints, search_tik_transfer_candidates)

__all__ = [
    "Entity", "EntitySet", "AdaptiveResult", "run_adaptive", "FORMULAS",
    "predict", "Candidate", "Sample", "fit_candidates", "ModelRecord",
    "ModelRegistry", "StabilityReport", "assess_stability",
    "TIKAdaptiveCandidate", "TIKAdaptiveResult", "TIKPairObservation",
    "fit_tik_pairs", "DynamicTIKCandidate", "DynamicTIKResult",
    "TIKTimeObservation", "fit_dynamic_tik_series",
    "TIKRawParameterGrid", "TIKRawSearchCandidate", "TIKRawSearchResult",
    "fit_tik_raw_parameters", "TIKResearchObservation", "TIKHoldoutPrediction",
    "TIKHoldoutReport", "TIKResearchResult", "fit_tik_research_dataset",
    "TIKTransferRule", "TIKComponentHint", "TIKTransferCandidate",
    "TIKTransferEvaluation", "TIKTransferSearchResult",
    "propose_tik_component_hints", "combine_tik_transfer_hints",
    "search_tik_transfer_candidates",
    "Applicability", "AxisAssessment", "AxisStatus", "CalibrationPoint",
    "CalibrationProfile", "DatasetObservation", "DatasetRole", "ObservationRole",
    "ProcessAssessment", "ProcessProfile", "TaskCluster", "TaskDefinition",
    "TaskOperation", "TransferPlan", "assess_process_transfer",
    "build_applicability_split", "cluster_tasks", "fit_calibration",
    "plan_skill_transfer", "AuthorizationDecision", "AuthorizationStatus",
    "CapabilityKnowledge", "ExecutionRequest", "SafetyPolicy", "authorize_execution",
]

from .transfer_engine import (
    Applicability, AxisAssessment, AxisStatus, CalibrationPoint, CalibrationProfile,
    DatasetObservation, DatasetRole, ObservationRole, ProcessAssessment, ProcessProfile,
    TaskCluster, TaskDefinition, TaskOperation, TransferPlan,
    assess_process_transfer, build_applicability_split, cluster_tasks,
    fit_calibration, plan_skill_transfer,
)
from .safety_gate import (
    AuthorizationDecision, AuthorizationStatus, CapabilityKnowledge,
    ExecutionRequest, SafetyPolicy, authorize_execution,
)
