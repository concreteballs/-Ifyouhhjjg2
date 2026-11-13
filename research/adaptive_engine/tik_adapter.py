"""End-to-end adaptive fitting over paired TIK-0 local states."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from typing import Iterable

from research.tik0.local_state import TIKLocalStateInputs, calculate_local_state
from .optimizer import Candidate, Sample, fit_candidates
from .stability import StabilityReport, assess_stability


@dataclass(frozen=True)
class TIKPairObservation:
    """One paired-location input and its observed output difference."""
    observation_id: str
    state_a: TIKLocalStateInputs
    state_b: TIKLocalStateInputs
    observed_delta: float
    weight: float = 1.0


@dataclass(frozen=True)
class TIKAdaptiveCandidate:
    return_model: str
    return_coefficient: float
    return_exponent: float
    response: Candidate
    stability: StabilityReport
    score: float


@dataclass(frozen=True)
class TIKAdaptiveResult:
    selected: TIKAdaptiveCandidate
    alternatives: tuple[TIKAdaptiveCandidate, ...]
    observation_count: int


def _paired_contrast(item: TIKPairObservation, model: str,
                     coefficient: float, exponent: float) -> float:
    a = calculate_local_state(
        item.state_a, return_model_name=model,
        return_coefficient=Decimal(str(coefficient)),
        return_exponent=Decimal(str(exponent)),
    )
    b = calculate_local_state(
        item.state_b, return_model_name=model,
        return_coefficient=__import__("decimal").Decimal(str(coefficient)),
        return_exponent=__import__("decimal").Decimal(str(exponent)),
    )
    returned_a = float(a.return_flow.returned_power_density_w_m3)
    returned_b = float(b.return_flow.returned_power_density_w_m3)
    incoming_a = float(a.tik.power_density_w_m3)
    incoming_b = float(b.tik.power_density_w_m3)
    scale = max((abs(incoming_a) + abs(incoming_b)) / 2.0, 1e-300)
    return (returned_a - returned_b) / scale


def fit_tik_pairs(
    observations: Iterable[TIKPairObservation],
    *,
    return_models: tuple[str, ...] = ("linear", "power", "saturating"),
    return_coefficients: tuple[float, ...] = (0.1, 0.5, 1.0, 2.0),
    return_exponents: tuple[float, ...] = (0.75, 1.0, 1.5),
    response_formulas: tuple[str, ...] = ("linear", "power", "saturating"),
    maximum_relative_change: float = 0.1,
) -> TIKAdaptiveResult:
    """Fit the complete TIK -> return-flow -> response chain across point pairs.

    The optimizer jointly searches return-curve family/parameters and the
    downstream response family/parameters. Inputs are evaluated by the
    existing TIK-0 and return-flow implementations; no duplicate physics
    calculation is introduced here.
    """
    data = tuple(observations)
    if len(data) < 2:
        raise ValueError("at least two paired observations are required")
    if len({item.observation_id for item in data}) != len(data):
        raise ValueError("observation_id values must be unique")
    if any(not item.observation_id.strip() for item in data):
        raise ValueError("observation_id is required")
    if any(not isfinite(item.observed_delta) or not isfinite(item.weight) or item.weight <= 0 for item in data):
        raise ValueError("observed deltas must be finite and weights positive")
    if not return_models or any(name not in ("linear", "power", "saturating") for name in return_models):
        raise ValueError("unsupported return model family")
    if not return_coefficients or any(not isfinite(v) or v <= 0 for v in return_coefficients):
        raise ValueError("return coefficients must be finite and positive")
    if not return_exponents or any(not isfinite(v) or v <= 0 for v in return_exponents):
        raise ValueError("return exponents must be finite and positive")

    ranked = []
    for model in return_models:
        for coefficient in return_coefficients:
            exponents = return_exponents if model == "power" else (1.0,)
            for exponent in exponents:
                samples = tuple(
                    Sample(_paired_contrast(item, model, coefficient, exponent),
                           item.observed_delta, item.weight)
                    for item in data
                )
                responses = fit_candidates(samples, formulas=response_formulas)
                response = responses[0]
                stability = assess_stability(
                    response.formula, response.parameters,
                    tuple(sample.x for sample in samples),
                    maximum_relative_change=maximum_relative_change,
                )
                # Stability failure is visible and strongly disfavoured, not hidden.
                score = response.score + (1e6 if not stability.passed else 0.0)
                ranked.append(TIKAdaptiveCandidate(
                    model, coefficient, exponent, response, stability, score
                ))
    ranked.sort(key=lambda item: (
        item.score, item.response.weighted_rmse, item.return_model,
        item.return_coefficient, item.return_exponent, item.response.formula,
    ))
    return TIKAdaptiveResult(ranked[0], tuple(ranked[1:]), len(data))
