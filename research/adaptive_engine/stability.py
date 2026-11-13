"""Repeatability, perturbation and boundary checks for fitted models."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from .formulas import predict

@dataclass(frozen=True)
class StabilityReport:
    finite_outputs: bool
    repeatable: bool
    perturbation_relative_change: float
    boundary_failures: int
    passed: bool

def assess_stability(formula: str, parameters: dict[str, float], inputs: tuple[float, ...],
                     *, perturbation: float = 1e-6, maximum_relative_change: float = 0.1) -> StabilityReport:
    if perturbation < 0 or maximum_relative_change < 0:
        raise ValueError("stability thresholds must be non-negative")
    failures, changes, finite = 0, [], True
    for x in inputs:
        try:
            first = predict(formula, x, parameters)
            second = predict(formula, x, parameters)
            shifted = predict(formula, x * (1 + perturbation), parameters)
            finite = finite and all(isfinite(v) for v in (first, second, shifted))
            if first != second:
                finite = False
            changes.append(abs(shifted - first) / max(abs(first), 1e-12))
        except (ValueError, ArithmeticError, OverflowError, KeyError):
            failures += 1
    maximum = max(changes, default=float("inf"))
    passed = finite and failures == 0 and maximum <= maximum_relative_change
    return StabilityReport(finite, finite, maximum, failures, passed)
