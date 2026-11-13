"""End-to-end adaptive model selection facade."""
from __future__ import annotations
from dataclasses import dataclass
from .entities import EntitySet
from .optimizer import Candidate, Sample, fit_candidates
from .stability import StabilityReport, assess_stability

@dataclass(frozen=True)
class AdaptiveResult:
    selected: Candidate
    alternatives: tuple[Candidate, ...]
    stability: StabilityReport
    entities: EntitySet

def run_adaptive(samples: tuple[Sample, ...], entities: EntitySet, *,
                 formulas: tuple[str, ...] = ("linear", "power", "saturating", "quadratic", "linear_saturating"),
                 maximum_relative_change: float = 0.1) -> AdaptiveResult:
    candidates = fit_candidates(samples, formulas=formulas)
    selected = candidates[0]
    stability = assess_stability(selected.formula, selected.parameters,
        tuple(s.x for s in samples), maximum_relative_change=maximum_relative_change)
    return AdaptiveResult(selected, tuple(candidates[1:]), stability, entities)
