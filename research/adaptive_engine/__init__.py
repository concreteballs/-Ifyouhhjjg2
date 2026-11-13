"""Adaptive search, TIK integration, stability checks and model registry."""
from .entities import Entity, EntitySet
from .engine import AdaptiveResult, run_adaptive
from .formulas import FORMULAS, predict
from .optimizer import Candidate, Sample, fit_candidates
from .registry import ModelRecord, ModelRegistry
from .stability import StabilityReport, assess_stability
from .tik_adapter import TIKAdaptiveCandidate, TIKAdaptiveResult, TIKPairObservation, fit_tik_pairs

__all__ = [
    "Entity", "EntitySet", "AdaptiveResult", "run_adaptive", "FORMULAS",
    "predict", "Candidate", "Sample", "fit_candidates", "ModelRecord",
    "ModelRegistry", "StabilityReport", "assess_stability",
    "TIKAdaptiveCandidate", "TIKAdaptiveResult", "TIKPairObservation",
    "fit_tik_pairs",
]
