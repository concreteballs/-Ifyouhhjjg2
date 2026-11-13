"""Deterministic coarse-to-fine search over formula families and parameters."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import isfinite, sqrt
from typing import Iterable
from .formulas import FORMULAS, predict

@dataclass(frozen=True)
class Sample:
    x: float
    y: float
    weight: float = 1.0

@dataclass(frozen=True)
class Candidate:
    formula: str
    parameters: dict[str, float]
    weighted_rmse: float
    stability_rmse: float
    score: float
    sample_count: int

def _grids(formula: str, input_scale: float, output_scale: float):
    multipliers = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
    gains = tuple(v * output_scale / input_scale for v in multipliers)
    offsets = tuple(v * output_scale for v in (-0.1, -0.05, 0.0, 0.05, 0.1))
    caps = tuple(v * output_scale for v in multipliers)
    if formula == "linear":
        return (("gain", gains), ("offset", offsets))
    if formula == "power":
        return (("gain", gains), ("exponent", (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)), ("offset", offsets))
    if formula == "saturating":
        return (("cap", caps), ("rate", (0.05, 0.1, 0.25, 0.5, 1.0, 2.0)), ("offset", offsets))
    if formula == "quadratic":
        return (("linear", gains), ("quadratic", tuple(v * output_scale / input_scale**2 for v in (-2, -1, 0, 1, 2))), ("offset", offsets))
    return (("gain", gains), ("cap", caps), ("rate", (0.05, 0.1, 0.25, 0.5, 1.0)), ("offset", offsets))

def _rmse(data, formula, params):
    total = sum(s.weight * (predict(formula, s.x, params) - s.y) ** 2 for s in data)
    weight = sum(s.weight for s in data)
    return sqrt(total / weight)

def fit_candidates(samples: Iterable[Sample], *, formulas: tuple[str, ...] = FORMULAS,
                   stability_fraction: float = 0.01, stability_weight: float = 0.5,
                   refinement_rounds: int = 2) -> list[Candidate]:
    data = tuple(samples)
    if len(data) < 2:
        raise ValueError("at least two samples are required")
    if not formulas or any(f not in FORMULAS for f in formulas):
        raise ValueError("unsupported or empty formula selection")
    if not 0 <= stability_fraction <= 1 or stability_weight < 0 or refinement_rounds < 0:
        raise ValueError("invalid stability settings")
    for s in data:
        if not all(isfinite(v) for v in (s.x, s.y, s.weight)) or s.weight <= 0:
            raise ValueError("sample values must be finite and weight positive")
    scale = max(max(abs(s.x) for s in data), 1e-12)
    output_scale = max(max(abs(s.y) for s in data), 1e-12)
    candidates = []
    for formula in formulas:
        dimensions = _grids(formula, scale, output_scale)
        grids = [d[1] for d in dimensions]
        best_params, best_score = None, float("inf")
        # Coarse grid followed by deterministic local refinement around the best point.
        for values in product(*grids):
            params = dict(zip((d[0] for d in dimensions), values))
            error = _rmse(data, formula, params)
            perturbed = tuple(Sample(s.x * (1 + stability_fraction), s.y, s.weight) for s in data)
            stable = _rmse(perturbed, formula, params)
            score = error + stability_weight * abs(stable - error)
            if score < best_score:
                best_params, best_score = params, score
        params = dict(best_params)
        for _ in range(refinement_rounds):
            for key in params:
                center = params[key]
                step = max(abs(center) * 0.2, 1e-8)
                choices = []
                for factor in (-1, 0, 1):
                    trial = dict(params); trial[key] = center + factor * step
                    if formula == "power" and key == "exponent" and trial[key] <= 0: continue
                    if formula == "saturating" and key in ("cap", "rate") and trial[key] <= 0: continue
                    if formula == "linear_saturating" and key in ("cap", "rate") and trial[key] <= 0: continue
                    choices.append((_rmse(data, formula, trial), trial))
                if choices:
                    params = min(choices, key=lambda pair: pair[0])[1]
        error = _rmse(data, formula, params)
        perturbed = tuple(Sample(s.x * (1 + stability_fraction), s.y, s.weight) for s in data)
        stable = _rmse(perturbed, formula, params)
        score = error + stability_weight * abs(stable - error)
        candidates.append(Candidate(formula, params, error, stable, score, len(data)))
    return sorted(candidates, key=lambda c: (c.score, c.weighted_rmse, c.formula))
